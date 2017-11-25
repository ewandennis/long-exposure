import unittest
from timekeeper import TimeKeeper

class TestBase(unittest.TestCase):
    def setUp(self):
        self.task_name = 'a task'
        self.other_task_name = 'another task'
        self.third_task_name = 'yet another task'
        self.tk = TimeKeeper()
        self._fakeTask(self.task_name)
        self._fakeTask(self.task_name)
        self._fakeTask(self.other_task_name)
        self._fakeTask(self.other_task_name)
        self._fakeTask(self.other_task_name)
        self._fakeTask(self.third_task_name)

    def _fakeTask(self, name):
        self.tk.start(name)
        j = 0
        for i in range(10000): j+=i%2
        self.tk.end(name)

class Safety(TestBase):
    def test_end_without_start(self):
        self.tk.end('whaaaaat')
        self.tk.end(self.task_name)

class Summary(TestBase):
    def test_returns_a_summary(self):
        summary = self.tk.task_summary(self.task_name)
        self.assertIsInstance(summary, tuple) 
        self.assertEqual(len(summary), 4)

    def test_has_hits(self):
        summary = self.tk.task_summary(self.task_name)
        hits = summary[0]
        self.assertIsInstance(hits, int)
        self.assertEqual(hits, 2)

    def test_has_avg(self):
        summary = self.tk.task_summary(self.task_name)
        avg = summary[1]
        self.assertIsInstance(avg, float)
        self.assertTrue(avg > 0)

    def test_has_min(self):
        summary = self.tk.task_summary(self.task_name)
        min_time = summary[2]
        self.assertIsInstance(min_time, float)
        self.assertTrue(min_time > 0)

    def test_has_max(self):
        summary = self.tk.task_summary(self.task_name)
        max_time = summary[2]
        self.assertIsInstance(max_time, float)
        self.assertTrue(max_time > 0)

    def test_bad_task_name(self):
        summary = self.tk.task_summary('whaaaaaaat')
        self.assertIsNone(summary)

class Report(TestBase):
    def test_report(self):
        report = self.tk.report()
        self.assertIsInstance(report, str)

class TotalTime(TestBase):
    def test_total_time(self):
        report = self.tk.report()
        summary = self.tk.task_summary('total')
        self.assertIsNotNone(summary)

