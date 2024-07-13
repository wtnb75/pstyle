import unittest
from unittest.mock import patch, ANY
from click.testing import CliRunner
from pstyle.main import cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_help(self):
        res = CliRunner().invoke(cli, ["--help"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("--version", res.output)
        self.assertIn("--help", res.output)
        self.assertIn("convert", res.output)

    def test_conv_help(self):
        res = CliRunner().invoke(cli, ["convert", "--help"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("named", res.output)
        self.assertIn("qmark", res.output)
        self.assertIn("--normalize", res.output)

    def test_conv_format2qmark(self):
        res = CliRunner().invoke(cli, [
            "convert", "--from-style", "format", "--to-style", "qmark", "--args", "1",
            "select * from tbl1 where id=%s"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("SELECT * FROM tbl1 WHERE id=?", res.output)

    def test_conv_format2qmark_original(self):
        res = CliRunner().invoke(cli, [
            "convert", "--from-style", "format", "--to-style", "qmark", "--args", "1",
            "select * from tbl1 where id=%s", "--original"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("select * from tbl1 where id=?", res.output)

    def test_list_drivers(self):
        res = CliRunner().invoke(cli, ["list-drivers"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("sqlite3", res.output)

    def test_try_db(self):
        with patch("IPython.start_ipython") as si:
            CliRunner().invoke(cli, ["try-db", "sqlite3://:memory:"])
            expected_ns = {
                "dsn": "sqlite3://:memory:",
                "db": ANY, "wrapped": ANY,
                "paramstyle": ("qmark", "auto"),
                "version": ANY,
            }
            si.assert_called_once_with(
                argv=[], user_ns=expected_ns)

    def test_try_db_code(self):
        with patch("code.InteractiveConsole") as ci:
            CliRunner().invoke(cli, ["try-db", "sqlite3://:memory:", "--code"])
            expected_ns = {
                "dsn": "sqlite3://:memory:",
                "db": ANY, "wrapped": ANY,
                "paramstyle": ("qmark", "auto"),
                "version": ANY,
            }
            ci.assert_called_once_with(locals=expected_ns)
            ci.return_value.interact.assert_called_once_with()

    def test_try_db_invalid(self):
        res = CliRunner().invoke(cli, ["try-db", "invalid://localhost/db"])
        self.assertIsNotNone(res.exception)
        self.assertEqual(2, res.exit_code)
        self.assertIn("invalid not found in ", res.output)
