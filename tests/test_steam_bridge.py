import unittest
from unittest.mock import Mock, patch

from playcore.steam_bridge import IMPORT_DIALOG_VISIBLE, local_socket, request_import, wait_for_import_dialog


class SteamBridgeTests(unittest.TestCase):
    def setUp(self):
        self.url = "ws://127.0.0.1:8081/devtools/page/test"
        self.targets = [{"title": "SharedJSContext", "webSocketDebuggerUrl": self.url}]

    def test_only_local_steam_debugger_urls_are_allowed(self):
        self.assertTrue(local_socket(self.url))
        for url in ("ws://example.com:8081/devtools/page/x",
                    "ws://127.0.0.1:9000/devtools/page/x",
                    "ws://user:pass@localhost:8081/devtools/page/x",
                    "file:///tmp/x", "ws://localhost:bad/devtools/page/x"):
            self.assertFalse(local_socket(url))

    @patch("playcore.steam_bridge.import_script", return_value="OFFICIAL_EVENT_SCRIPT")
    def test_only_one_dispatch_and_confirmation_remains_pending(self, script):
        execute = Mock(side_effect=[True, True, True])
        result = request_import(object(), lambda: self.targets * 2, execute)
        self.assertIn("pendiente", result)
        self.assertEqual(execute.call_count, 3)
        self.assertEqual(execute.call_args_list[0].args[1], "window.hasDeckyLaunchOptions === true")
        self.assertIn("OFFICIAL_EVENT_SCRIPT", execute.call_args_list[1].args[1])
        self.assertEqual(execute.call_args_list[2].args[1], IMPORT_DIALOG_VISIBLE)

    @patch("playcore.steam_bridge.time.sleep")
    @patch("playcore.steam_bridge.time.monotonic", side_effect=[0, 0, 0, 4])
    @patch("playcore.steam_bridge.import_script", return_value="EVENT")
    def test_loaded_plugin_without_visible_dialog_does_not_report_success(self, script, clock, sleep):
        execute = Mock(side_effect=[True, True, False])
        with self.assertRaisesRegex(RuntimeError, "Abre Steam en modo Big Picture"):
            request_import(object(), lambda: self.targets * 2, execute)
        # Un evento aceptado sin modal visible nunca se reenvía automáticamente.
        self.assertEqual(execute.call_count, 3)

    @patch("playcore.steam_bridge.time.sleep")
    def test_waits_for_delayed_render_without_resending_event(self, sleep):
        execute = Mock(side_effect=[False, True])
        wait_for_import_dialog(self.url, execute)
        self.assertEqual(execute.call_count, 2)
        self.assertTrue(all(call.args[1] == IMPORT_DIALOG_VISIBLE for call in execute.call_args_list))

    def test_failed_dialog_probe_does_not_claim_success(self):
        with self.assertRaisesRegex(RuntimeError, "no se ha podido confirmar"):
            wait_for_import_dialog(self.url, Mock(side_effect=RuntimeError("connection lost")))

    @patch("playcore.steam_bridge.import_script", return_value="EVENT")
    def test_uncertain_dispatch_is_never_retried(self, script):
        execute = Mock(side_effect=[True, RuntimeError("timeout")])
        with self.assertRaisesRegex(RuntimeError, "timeout"):
            request_import(object(), lambda: self.targets * 2, execute)
        self.assertEqual(execute.call_count, 2)

    @patch("playcore.steam_bridge.import_script", return_value="EVENT")
    def test_unloaded_plugin_does_not_dispatch(self, script):
        execute = Mock(return_value=False)
        with self.assertRaisesRegex(RuntimeError, "no está cargado"):
            request_import(object(), lambda: self.targets, execute)
        execute.assert_called_once_with(self.url, "window.hasDeckyLaunchOptions === true")

    @patch("playcore.steam_bridge.import_script", return_value="EVENT")
    def test_unreachable_steam_reports_actionable_error(self, script):
        with self.assertRaisesRegex(RuntimeError, "Abre Big Picture"):
            request_import(object(), Mock(side_effect=OSError("refused")), Mock())

    @patch("playcore.steam_bridge.import_script", side_effect=RuntimeError("no detectado"))
    def test_manifest_check_precedes_connection(self, script):
        discover = Mock()
        with self.assertRaisesRegex(RuntimeError, "no detectado"):
            request_import(object(), discover, Mock())
        discover.assert_not_called()
