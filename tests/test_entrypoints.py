import importlib
import sys
import unittest


class EntrypointTests(unittest.TestCase):
    def test_app_package_import_has_no_web_framework_dependency(self):
        package = importlib.import_module("app")

        self.assertEqual(package.__version__, "0.2.0")
        self.assertNotIn("flask", sys.modules)


if __name__ == "__main__":
    unittest.main()
