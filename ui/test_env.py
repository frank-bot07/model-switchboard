import unittest
import os
import shlex
import tempfile
from pathlib import Path
import sys

# Add ui directory to path so we can import server
sys.path.append(os.path.dirname(__file__))
import server

class TestEnv(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.env_file = Path(self.tmp_dir.name) / ".env"
        # Monkeypatch server.ENV_FILE
        self.old_env_file = server.ENV_FILE
        server.ENV_FILE = self.env_file

    def tearDown(self):
        server.ENV_FILE = self.old_env_file
        self.tmp_dir.cleanup()

    def test_write_read_simple(self):
        server.write_env_key("KEY", "VALUE")
        env = server.read_env()
        self.assertEqual(env["KEY"], "VALUE")

    def test_write_read_spaces(self):
        server.write_env_key("KEY", "value with spaces")
        env = server.read_env()
        self.assertEqual(env["KEY"], "value with spaces")

    def test_write_read_quotes(self):
        val = 'value with "double" and \'single\' quotes'
        server.write_env_key("KEY", val)
        env = server.read_env()
        self.assertEqual(env["KEY"], val)

    def test_write_read_multiline_simulation(self):
        server.write_env_key("KEY1", "val1")
        server.write_env_key("KEY2", "val2")
        env = server.read_env()
        self.assertEqual(env["KEY1"], "val1")
        self.assertEqual(env["KEY2"], "val2")

    def test_overwrite_key(self):
        server.write_env_key("KEY", "old")
        server.write_env_key("KEY", "new")
        env = server.read_env()
        self.assertEqual(env["KEY"], "new")
        self.assertEqual(len(env), 1)

    def test_special_characters(self):
        vals = ["!@#$%^&*()", "   leading and trailing   ", "';--", "\"", "\\"]
        for i, v in enumerate(vals):
            key = f"KEY{i}"
            server.write_env_key(key, v)
            env = server.read_env()
            self.assertEqual(env[key], v, f"Failed for value: {v!r}")

if __name__ == "__main__":
    unittest.main()
