from unittest import TestCase

from ..datazilla import DatazillaResult



class DatazillaResultTest(TestCase):
    def test_init_with_results(self):
        """Can initialize with a dictionary of results."""
        data = {"suite": {"test": [1, 2, 3]}}
        res = DatazillaResult(data)

        self.assertEqual(res.results, data)


    def test_init_noargs(self):
        """Can initialize with no argument and get empty initial results."""
        res = DatazillaResult()

        self.assertEqual(res.results, {})


    def test_add_testsuite(self):
        """Can add a test suite with tests and results."""
        res = DatazillaResult()
        res.add_testsuite("suite", {"test1": [1, 2, 3]})

        self.assertEqual(res.results, {"suite": {"test1": [1, 2, 3]}})


    def test_add_test_results(self):
        """Can add results to a suite."""
        res = DatazillaResult()
        res.add_test_results("suite", "test", [1, 2, 3])

        self.assertEqual(res.results, {"suite": {"test": [1, 2, 3]}})


    def test_join_results(self):
        """Can merge a full results dictionary into this result."""
        res = DatazillaResult({"suite1": {"test1a": [1]}})

        res.join_results(
            {
                "suite1": {"test1a": [2], "test1b": [3]},
                "suite2": {"test2a": [4]},
                }
            )

        self.assertEqual(
            res.results,
            {
                "suite1": {"test1a": [1, 2], "test1b": [3]},
                "suite2": {"test2a": [4]},
                }
            )
