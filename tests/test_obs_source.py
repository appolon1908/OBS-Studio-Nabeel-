"""Source-only tests: synthetic files and mocked tools, never OBS or hardware."""
import configparser
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "docs/scripts"


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "config"
        self.media = self.root / "media"

    def bootstrap(self):
        env = {"PATH": os.defpath, "HOME": str(self.root / "home"),
               "OBS_CONFIG_ROOT": str(self.config), "NABEEL_MEDIA_ROOT": str(self.media)}
        subprocess.run([sys.executable, str(SCRIPTS / "nabeel-obs-bootstrap.py")],
                       env=env, check=True, capture_output=True, text=True)

    def test_profile_geometry_audio_and_recording_are_deterministic(self):
        self.bootstrap()
        profile = configparser.ConfigParser(interpolation=None)
        profile.read(self.config / "basic/profiles/NABEEL-1080p60/basic.ini")
        self.assertEqual("1920", profile["Video"]["BaseCX"])
        self.assertEqual("1080", profile["Video"]["BaseCY"])
        self.assertEqual("60", profile["Video"]["FPSCommon"])
        self.assertEqual("48000", profile["Audio"]["SampleRate"])
        self.assertEqual("Stereo", profile["Audio"]["ChannelSetup"])
        self.assertEqual("mkv", profile["AdvOut"]["RecFormat2"])
        self.assertEqual(str(self.media / "Recordings"), profile["AdvOut"]["RecFilePath"])
        for directory in ("Recordings", "Clips", "Exports", "Archive"):
            self.assertTrue((self.media / directory).is_dir())

    def test_stream_credentials_and_capture_devices_remain_unset(self):
        self.bootstrap()
        service = json.loads((self.config / "basic/profiles/NABEEL-1080p60/service.json").read_text())
        self.assertEqual({"server": "", "key": "", "use_auth": False}, service["settings"])
        scene = json.loads((self.config / "basic/scenes/NABEEL-Station.json").read_text())
        self.assertEqual("Gameplay", scene["current_scene"])
        self.assertEqual([], scene["sources"][0]["settings"]["items"])
        self.assertEqual([], scene["saved_projectors"])

    def test_every_existing_profile_and_scene_is_backed_up_before_replacement(self):
        self.bootstrap()
        paths = [self.config / "basic/profiles/NABEEL-1080p60/basic.ini",
                 self.config / "basic/profiles/NABEEL-1080p60/service.json",
                 self.config / "basic/scenes/NABEEL-Station.json"]
        for path in paths:
            path.write_text("synthetic existing configuration")
        self.bootstrap()
        for path in paths:
            backups = list(path.parent.glob(path.name + ".bak-*"))
            self.assertEqual(1, len(backups))
            self.assertEqual("synthetic existing configuration", backups[0].read_text())
            self.assertNotEqual(backups[0].read_text(), path.read_text())


class CertificateDecisionTests(unittest.TestCase):
    """Passing simulations validate decision logic, never live certification."""
    def simulate(self, missing=None, http_status=200, network_error=False, count=1):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            profile = home / ".config/obs-studio/basic/profiles/NABEEL-1080p60/basic.ini"
            scene = home / ".config/obs-studio/basic/scenes/NABEEL-Station.json"
            for name, path in (("obs_profile", profile), ("obs_scene", scene)):
                if missing != name:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("synthetic fixture, not runtime evidence")
            recordings = home / "Videos/NABEEL/Recordings"
            recordings.mkdir(parents=True)
            for index in range(0 if missing == "recording_files" else count):
                path = recordings / f"synthetic-{index}.mkv"
                path.write_text("synthetic fixture, not a recording")
                os.utime(path, (1000 + index, 1000 + index))
            (recordings / "directory-not-a-recording").mkdir()
            exists = Path.exists
            calls = []

            def fake_exists(path):
                if str(path) in ("/usr/bin/chiaki", "/usr/bin/obs"):
                    return missing != ("chiaki_binary" if path.name == "chiaki" else "obs_binary")
                return exists(path)

            def fake_run(args, **kwargs):
                calls.append(args)
                if args[:2] == ["pgrep", "-f"]:
                    patterns = {r"(^|/)chiaki([ -]|$)": "chiaki_running",
                                r"(^|/)obs([ -]|$)": "obs_running"}
                    self.assertIn(args[2], patterns)
                    gate = patterns[args[2]]
                    return subprocess.CompletedProcess(args, 1 if missing == gate else 0, stdout="")
                if args[:3] == ["docker", "inspect", "-f"]:
                    self.assertIn(args[-1], ("nabeel-mediamtx", "nabeel-owncast"))
                    self.assertEqual("{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}", args[3])
                    gate = "mediamtx_container" if args[-1] == "nabeel-mediamtx" else "owncast_container"
                    return subprocess.CompletedProcess(args, 1 if missing == gate else 0, stdout="running|healthy")
                raise AssertionError(f"Unexpected external command: {args}")

            class Response:
                status = http_status
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False

            def fake_urlopen(url, timeout):
                self.assertEqual("http://127.0.0.1:8081/api/status", url)
                self.assertEqual(3, timeout)
                if network_error or missing == "owncast_http":
                    raise TimeoutError("synthetic unavailable service")
                return Response()

            output = io.StringIO()
            with patch.object(Path, "home", return_value=home), \
                    patch.object(Path, "exists", fake_exists), \
                    patch("subprocess.run", side_effect=fake_run), \
                    patch("subprocess.Popen", side_effect=AssertionError("No real processes")), \
                    patch("urllib.request.urlopen", side_effect=fake_urlopen), \
                    patch("socket.socket", side_effect=AssertionError("No real sockets")), \
                    contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(SCRIPTS / "nabeel-staging-certify.py"))
            self.assertEqual(4, len(calls))
            return raised.exception.code, json.loads(output.getvalue())

    def test_all_synthetic_gates_pass_without_authorizing_live_production(self):
        code, result = self.simulate()
        self.assertEqual(0, code)
        self.assertTrue(result["pass"])
        self.assertFalse(result["production_live_enabled"])
        self.assertEqual("nabeel.staging-certificate.v1", result["schema"])

    def test_each_missing_gate_fails_closed(self):
        for gate in ("chiaki_binary", "chiaki_running", "obs_binary", "obs_running",
                     "obs_profile", "obs_scene", "mediamtx_container",
                     "owncast_container", "owncast_http", "recording_files"):
            with self.subTest(gate=gate):
                code, result = self.simulate(missing=gate)
                self.assertEqual(1, code)
                self.assertFalse(result["pass"])
                self.assertFalse(result["production_live_enabled"])

    def test_non_success_http_status_and_timeout_fail_closed(self):
        for options in ({"http_status": 503}, {"network_error": True}):
            with self.subTest(options=options):
                code, result = self.simulate(**options)
                self.assertEqual(1, code)
                self.assertFalse(result["gates"]["owncast_http"]["ok"])

    def test_recording_evidence_is_only_five_latest_files(self):
        _, result = self.simulate(count=7)
        self.assertEqual([f"synthetic-{i}.mkv" for i in (6, 5, 4, 3, 2)],
                         [Path(p).name for p in result["gates"]["recording_files"]])


class PostprocessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.media = self.root / "media"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.arguments = self.root / "ffmpeg-arguments.json"
        self.source = self.root / "synthetic source with spaces.mkv"
        self.source.write_bytes(b"synthetic source bytes")
        self.env = {"PATH": str(self.bin) + os.pathsep + os.defpath,
                    "HOME": str(self.root), "NABEEL_MEDIA_ROOT": str(self.media),
                    "FAKE_FFMPEG_ARGS": str(self.arguments)}
        self.tool("ffmpeg", """
            import json, os, pathlib, sys
            pathlib.Path(os.environ["FAKE_FFMPEG_ARGS"]).write_text(json.dumps(sys.argv[1:]))
            if os.environ.get("FAKE_FFMPEG_FAIL"):
                raise SystemExit(9)
            pathlib.Path(sys.argv[-1]).write_bytes(b"synthetic encoded bytes")
        """)
        self.tool("ffprobe", """
            import os
            if os.environ.get("FAKE_FFPROBE_FAIL"):
                raise SystemExit(7)
            print("12.5")
        """)

    def tool(self, name, code):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(code))
        path.chmod(0o755)

    def run_script(self, *args, **env):
        return subprocess.run(["bash", str(SCRIPTS / "nabeel-postprocess.sh"), *map(str, args)],
                              env={**self.env, **env}, capture_output=True, text=True)

    def test_clip_arguments_and_manifest_bind_exact_source_and_output_bytes(self):
        result = self.run_script(self.source, "30", "90")
        self.assertEqual(0, result.returncode, result.stderr)
        args = json.loads(self.arguments.read_text())
        for flag, value in (("-ss", "30"), ("-t", "90"), ("-i", str(self.source)),
                            ("-c:v", "libx264"), ("-pix_fmt", "yuv420p"),
                            ("-movflags", "+faststart"), ("-c:a", "aac")):
            self.assertEqual(value, args[args.index(flag) + 1])
        self.assertIn("0:a:0?", args)
        manifest_path, = (self.media / "Exports").glob("*.manifest.json")
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual("nabeel.postproduction.v1", manifest["schema"])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), manifest["source_sha256"])
        self.assertEqual(hashlib.sha256(Path(manifest["export"]).read_bytes()).hexdigest(), manifest["export_sha256"])
        self.assertEqual(12.5, manifest["duration_seconds"])
        self.assertEqual("youtube-h264-aac-faststart", manifest["profile"])
        self.assertEqual(b"synthetic source bytes", self.source.read_bytes())

    def test_full_export_omits_duration_and_starts_at_zero(self):
        self.assertEqual(0, self.run_script(self.source).returncode)
        args = json.loads(self.arguments.read_text())
        self.assertNotIn("-t", args)
        self.assertEqual("0", args[args.index("-ss") + 1])

    def test_missing_input_or_argument_never_invokes_encoder(self):
        self.assertEqual(2, self.run_script().returncode)
        self.assertEqual(3, self.run_script(self.root / "missing.mkv").returncode)
        self.assertFalse(self.arguments.exists())

    def test_encoder_or_probe_failure_never_creates_success_manifest(self):
        for env in ({"FAKE_FFMPEG_FAIL": "1"}, {"FAKE_FFPROBE_FAIL": "1"}):
            with self.subTest(env=env):
                self.assertNotEqual(0, self.run_script(self.source, **env).returncode)
                self.assertEqual([], list((self.media / "Exports").glob("*.manifest.json")))


class OwnedSourceScopeTests(unittest.TestCase):
    def test_new_executable_or_application_source_requires_separate_pipeline_review(self):
        scripts = {"docs/scripts/nabeel-obs-bootstrap.py", "docs/scripts/nabeel-staging-certify.py",
                   "docs/scripts/nabeel-postprocess.sh"}
        known = {
            ".github/workflows/nabeel-integration-ci.yml",
            ".github/workflows/obs-source-ci.yml",
            "governance/interim-release-policy.json",
            "tests/test_obs_source.py",
        } | scripts
        raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT, text=True)
        for entry in raw.split("\0"):
            if not entry:
                continue
            metadata, name = entry.split("\t", 1)
            mode, _, stage = metadata.split()
            self.assertEqual("0", stage, "Unmerged index")
            self.assertIn(mode, ("100644", "100755"))
            self.assertTrue(name.endswith(".md") or name in known,
                            f"New product source requires dedicated pipeline review: {name}")
            if mode == "100755":
                self.assertIn(name, scripts)


if __name__ == "__main__":
    unittest.main()
