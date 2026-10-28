"""Missing-library fixtures and fake-command tests; never install host packages."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import json
import os
import sys
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'linux_bootstrap.py'
spec = importlib.util.spec_from_file_location('linux_bootstrap', MODULE)
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)


class RequirementsTests(unittest.TestCase):
    def test_ldd_fixture_reports_unique_sonames(self):
        text = 'libgtk-3.so.0 => not found\nlibnss3.so => /lib/libnss3.so (0x1)\nlibgtk-3.so.0 => not found\n'
        self.assertEqual(boot.parse_ldd(text, 0), ['libgtk-3.so.0'])

    def test_abi_failure_is_never_package_repair(self):
        with self.assertRaisesRegex(RuntimeError, 'unsupported glibc'):
            boot.parse_ldd("app: /lib/libc.so.6: version `GLIBC_2.38' not found", 1)
        with self.assertRaisesRegex(RuntimeError, 'Could not inspect'):
            boot.parse_ldd('not a dynamic executable', 1)

    def test_supported_families_and_debian_t64_fallback(self):
        self.assertEqual(boot.distro_family('ID=linuxmint\nID_LIKE="ubuntu debian"'), 'apt')
        self.assertEqual(boot.distro_family('ID=rocky\nID_LIKE="rhel centos fedora"'), 'dnf')
        self.assertIsNone(boot.distro_family('ID=arch'))
        self.assertEqual(boot.package_plan(['libgtk-3.so.0', 'libgdk-3.so.0'], 'apt', lambda name: name == 'libgtk-3-0t64'), ['libgtk-3-0t64'])
        self.assertEqual(boot.package_plan(['libasound.so.2'], 'apt', lambda name: name == 'libasound2'), ['libasound2'])
        self.assertEqual(boot.package_plan(['libasound.so.2', 'libgtk-3.so.0'], 'dnf'), ['alsa-lib', 'gtk3'])

    def test_unknown_library_distro_or_package_stops(self):
        for missing, family in [(['invented.so'], 'apt'), (['libgtk-3.so.0'], None)]:
            with self.assertRaises(RuntimeError):
                boot.package_plan(missing, family, lambda _: True)
        with self.assertRaisesRegex(RuntimeError, 'No supported package'):
            boot.package_plan(['libgtk-3.so.0'], 'apt', lambda _: False)
        with self.assertRaisesRegex(RuntimeError, 'unrecognized'):
            boot.package_command('apt', ['curl;sh'])

    def test_declining_visible_consent_runs_no_elevated_command(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'dialog', return_value=False), patch.object(boot, 'run') as runner:
            self.assertFalse(boot.repair(Path('/app'), 'apt', ['libnss3']))
            runner.assert_not_called()

    def test_pkexec_elevates_only_absolute_package_manager(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'dialog', return_value=True), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as runner:
            self.assertTrue(boot.repair(Path('/app'), 'apt', ['libnss3']))
            self.assertEqual(runner.call_args.args[0], ['/usr/bin/pkexec', '/usr/bin/apt-get', 'install', '--no-install-recommends', '-y', 'libnss3'])
            self.assertNotIn('shell', runner.call_args.kwargs)

    def test_failed_or_cancelled_auth_never_launches_app(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'dialog', return_value=True), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 126, '', 'cancelled')):
            with self.assertRaisesRegex(RuntimeError, 'cancelled or failed'):
                boot.repair(Path('/app'), 'dnf', ['gtk3'])

    def test_smoke_still_checks_and_requires_confirmation(self):
        with patch.object(sys, 'argv', ['bootstrap', '--app-dir', '/app', '--', '--smoke']), patch.object(boot, 'probe', return_value=['libnss3.so']), patch.object(boot, 'package_plan', return_value=['libnss3']), patch.object(boot, 'repair', return_value=False) as repair, patch.object(boot.os, 'execv') as launch, patch.object(boot.os, 'geteuid', return_value=1000), patch.dict(boot.os.environ, {'DISPLAY': ':fixture'}):
            self.assertEqual(boot.main(), 3)
            repair.assert_called_once()
            launch.assert_not_called()

    def test_terminal_confirmation_uses_sudo_only_for_package_manager(self):
        with patch.object(Path, 'is_file', return_value=True), patch('builtins.input', return_value='yes'), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 0)) as runner:
            self.assertTrue(boot.repair(Path('/app'), 'dnf', ['gtk3'], terminal=True))
            self.assertEqual(runner.call_args.args[0], ['/usr/bin/sudo', '/usr/bin/dnf', 'install', '-y', 'gtk3'])

    def test_protontricks_is_an_explicit_allowed_package_only(self):
        with patch.object(Path, 'is_file', return_value=True):
            self.assertEqual(boot.package_command('apt', ['protontricks']), ['/usr/bin/apt-get', 'install', '--no-install-recommends', '-y', 'protontricks'])
        with patch.object(Path, 'is_file', return_value=True):
            command = boot.terminal_command('/app/python', '/app/helper.py', Path('/app'), ensure_protontricks=True)
        self.assertIn('--ensure-protontricks', command)
        self.assertNotIn('shell', command)

    def test_protontricks_flag_never_executes_game_verb_or_electron(self):
        with patch.object(sys, 'argv', ['bootstrap', '--app-dir', '/app', '--ensure-protontricks']), patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'run') as runner, patch.object(boot.os, 'execv') as launch, patch.object(boot.os, 'geteuid', return_value=1000), patch.dict(boot.os.environ, {'DISPLAY': ':fixture'}):
            self.assertEqual(boot.main(), 0)
            runner.assert_not_called()
            launch.assert_not_called()

    def test_apprun_invokes_bundled_preflight_and_preserves_args(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            python = root / 'resources/python/bin/python3'
            python.parent.mkdir(parents=True)
            python.write_text('#!' + sys.executable + '\nimport json,sys;print(json.dumps(sys.argv[1:]))\n')
            python.chmod(0o755)
            env = os.environ.copy()
            env['APPDIR'] = scratch
            result = subprocess.run(['/bin/sh', str(MODULE.parent / 'linux_AppRun.sh'), '--smoke', 'space argument'], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), [str(root / 'resources/linux_bootstrap.py'), '--app-dir', scratch, '--', '--smoke', 'space argument'])

    def test_headless_environment_never_executes_electron(self):
        with patch.object(sys, 'argv', ['bootstrap', '--app-dir', '/app', '--', '--smoke']), patch.object(boot, 'probe', return_value=[]), patch.object(boot, 'dialog'), patch.object(boot.os, 'geteuid', return_value=1000), patch.dict(boot.os.environ, {}, clear=True), patch.object(boot.os, 'execv') as launch:
            self.assertEqual(boot.main(), 2)
            launch.assert_not_called()

    def test_empty_apt_cache_refreshes_once_after_consent_then_replans(self):
        state = {'ready': False}
        def fake_run(args, **kwargs):
            self.assertEqual(args, ['/usr/bin/pkexec', '/usr/bin/apt-get', 'update'])
            state['ready'] = True
            return subprocess.CompletedProcess(args, 0, '', '')
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'apt_available', side_effect=lambda name: state['ready'] and name == 'libgtk-3-0t64'), patch.object(boot, 'dialog', return_value=True), patch.object(boot, 'run', side_effect=fake_run) as runner:
            self.assertEqual(boot.plan_with_refresh(['libgtk-3.so.0'], 'apt', Path('/app')), ['libgtk-3-0t64'])
            runner.assert_called_once()

    def test_declined_index_refresh_executes_no_commands(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'apt_available', return_value=False), patch.object(boot, 'dialog', return_value=False), patch.object(boot, 'run') as runner:
            self.assertIsNone(boot.plan_with_refresh(['libgtk-3.so.0'], 'apt', Path('/app')))
            runner.assert_not_called()

    def test_failed_index_refresh_never_launches_electron(self):
        with patch.object(sys, 'argv', ['bootstrap', '--app-dir', '/app', '--', '--smoke']), patch.object(boot, 'probe', return_value=['libgtk-3.so.0']), patch.object(boot, 'apt_available', return_value=False), patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'dialog', return_value=True), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 100, '', 'bad repository')), patch.object(boot.os, 'execv') as launch, patch.object(boot.os, 'geteuid', return_value=1000), patch.dict(boot.os.environ, {'DISPLAY': ':fixture'}):
            self.assertEqual(boot.main(), 2)
            launch.assert_not_called()

    def test_refresh_never_loops_or_attempts_unknown_libraries(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'apt_available', return_value=False), patch.object(boot, 'dialog', return_value=True), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as runner:
            with self.assertRaises(boot.PackageIndexMissing):
                boot.plan_with_refresh(['libgtk-3.so.0'], 'apt', Path('/app'))
            runner.assert_called_once()
            runner.reset_mock()
            with self.assertRaises(RuntimeError):
                boot.plan_with_refresh(['libgtk-3.so.0', 'unknown.so'], 'apt', Path('/app'))
            runner.assert_not_called()

    def test_host_package_tools_are_not_called_for_probe_fixture(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(boot, 'run', return_value=subprocess.CompletedProcess([], 0, 'libnss3.so => not found\n', '')) as runner:
            self.assertEqual(boot.probe(Path('/app')), ['libnss3.so'])
            self.assertEqual(runner.call_args.args[0], ['/usr/bin/ldd', '/app/MattsSDKBoostingTools'])


if __name__ == '__main__':
    unittest.main()
