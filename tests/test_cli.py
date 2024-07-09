import unittest
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
        self.assertIn("conv", res.output)

    def test_conv_help(self):
        res = CliRunner().invoke(cli, ["conv", "--help"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("named", res.output)
        self.assertIn("qmark", res.output)
        self.assertIn("--normalize", res.output)

    def test_conv_format2qmark(self):
        res = CliRunner().invoke(cli, [
            "conv", "--from-style", "format", "--to-style", "qmark", "--args", "1",
            "select * from tbl1 where id=%s"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("SELECT * FROM tbl1 WHERE id=?", res.output)

    def test_conv_format2qmark_original(self):
        res = CliRunner().invoke(cli, [
            "conv", "--from-style", "format", "--to-style", "qmark", "--args", "1",
            "select * from tbl1 where id=%s", "--original"])
        if res.exception:
            raise res.exception
        self.assertEqual(0, res.exit_code)
        self.assertIsNone(res.exception)
        self.assertIn("select * from tbl1 where id=?", res.output)
