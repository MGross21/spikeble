import unittest

class TestAppImport(unittest.TestCase):
    def test_import_raises(self):
        with self.assertRaises(NotImplementedError):
            import app

class TestAppSubmoduleImport(unittest.TestCase):
    def test_import_raises(self):
        with self.assertRaises(NotImplementedError):
            from app import sound, bargraph, display, linegraph, music

if __name__ == "__main__":
    unittest.main()