import subprocess
import unittest
from unittest.mock import patch

from playcore.accounts import password_command, password_status
from playcore import install_helper


class AccountTests(unittest.TestCase):
    def test_public_status_does_not_request_or_expose_passwords(self):
        for state, expected in (("P", "Configurada"), ("NP", "Sin contraseña"), ("L", "Cuenta bloqueada")):
            calls = []
            def runner(args, **kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args, 0, f"player {state} 2026-10-30 0 99999 7 -1", "")
            self.assertEqual(password_status(runner, lambda _: "/usr/bin/passwd"), expected)
            self.assertEqual(calls, [["passwd", "-S"]])

    def test_password_command_is_interactive_for_current_account(self):
        program, args = password_command(lambda name: "/usr/bin/" + name)
        self.assertEqual(program, "/usr/bin/konsole")
        self.assertEqual(args, ["--separate", "--nofork", "--hold", "-e", "/usr/bin/passwd"])
        self.assertNotIn("--stdin", args)

    def test_missing_tools_and_status_failure(self):
        with self.assertRaises(RuntimeError):
            password_command(lambda _: None)
        self.assertIn("Desconocido", password_status(which=lambda _: None))
        def runner(*args, **kwargs):
            raise subprocess.TimeoutExpired("passwd", 5)
        self.assertEqual(password_status(runner, lambda _: "passwd"), "Desconocido")

    def test_helper_cannot_run_unprivileged(self):
        with patch("playcore.install_helper.os.geteuid", return_value=1000):
            with self.assertRaisesRegex(RuntimeError, "PolicyKit"):
                install_helper.main()
