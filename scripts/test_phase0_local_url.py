"""Local endpoint boundary used by disposable parallel lifecycle stacks."""
import unittest

from phase0_api import validate_disposable_url


class DisposableUrlTests(unittest.TestCase):
    def test_allows_explicit_local_ports(self):
        self.assertEqual(
            validate_disposable_url("http://localhost:18080"),
            "http://localhost:18080",
        )
        self.assertEqual(
            validate_disposable_url("http://127.0.0.1:8080/"),
            "http://127.0.0.1:8080",
        )

    def test_rejects_remote_implicit_and_credentialed_urls(self):
        for value in (
            "https://localhost:18080",
            "http://localhost",
            "http://example.invalid:8080",
            "http://user:password@localhost:18080",
            "http://localhost:18080/api",
            "http://localhost:18080?x=1",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_disposable_url(value)


if __name__ == "__main__":
    unittest.main()
