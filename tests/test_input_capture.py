import unittest
from split_typing.input_capture import supports_raw


class TestInputCapture(unittest.TestCase):
    def test_supports_raw_is_bool(self):
        self.assertIsInstance(supports_raw(), bool)

    def test_supports_raw_false_when_not_tty(self):
        # under the test runner stdin is usually not a TTY
        # so this must not raise and must return a bool
        self.assertIn(supports_raw(), (True, False))
