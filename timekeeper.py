from time import perf_counter

class TimeKeeper:
    def __init__(self):
        self.times = {}
        self.start('total')

    def _time(self): return perf_counter()

    def start(self, task_name):
        if not task_name in self.times:
            self.times[task_name] = []
        self.times[task_name].append(self._time())

    def end(self, task_name):
        if not task_name in self.times:
            return
        if len(self.times[task_name]) % 2 != 1:
            return
        self.times[task_name].append(self._time())

    def task_time(self, task_name):
        if not task_name in self.times: return None
        times = self.times[task_name]
        n_times = len(times)
        start_idx = list(range(0, n_times, 2))
        end_idx = list(range(1, n_times, 2))
        if len(end_idx) < len(start_idx): start_idx.pop()
        n_spans = len(start_idx)
        spans = [times[end_idx[idx]] - times[start_idx[idx]] for idx in range(n_spans)]
        avg_time = sum(spans) / n_spans
        return '''{}
    hits: {}
    avg: {:.2}
    min; {:.2}
    max: {:.2}
'''.format(task_name, len(spans), avg_time, min(spans), max(spans))

    def report(self):
        self.end('total')
        return '\n'.join([self.task_time(task_name) for task_name in self.times.keys()])

