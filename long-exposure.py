import cv2
import numpy as np
import sys
import os.path
from time import perf_counter
from strictyaml import load, Map, Str, Float, Int

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

class Config:
    SCHEMA = Map(dict(
        image_scale=Float(),
        frame_limit=Int(),
        alignment=Map(dict(mode=Str(), termination_iterations=Int(), termination_eps=Float()))
    ))
    def __init__(self, path='config.yaml'):
        yaml_str = open(path, 'r').read()
        self.cfg = load(yaml_str, Config.SCHEMA).data

    def get(self, key):
        return self.cfg[key]

class Accumulator:
    """Accumulate pixel values across frames"""
    def __init__(self):
        self.accum = None
        self.count = 0

    def init(self, frame):
        self.accum = np.zeros(frame.shape, dtype=np.float)
        self.count = 0

    def eat_frame(self, frame):
        if self.accum is None:
            self.init(frame)
        norm = frame.astype('float')
        self.accum += norm
        self.count += 1

    def get_mean_image(self):
        mean_float = self.accum / self.count
        return mean_float.astype('uint8') 

class Aligner:
    """Align subsequent images to the first"""
    MODEMAP = dict(
        translation=cv2.MOTION_TRANSLATION,
        homography=cv2.MOTION_HOMOGRAPHY, 
        euclid=cv2.MOTION_EUCLIDEAN
    )
    def __init__(self, mode='translation', iterations=50, eps=1e-10):
        self.last_frame = None
        self.shape = None
        self.warp_mode = Aligner.MODEMAP[mode]
        self.warp_matrix = self._get_warp_matrix()
        num_iterations = iterations
        termination_eps = eps
        self.criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, num_iterations, termination_eps)

    def _get_warp_matrix(self):
        if self.warp_mode == cv2.MOTION_HOMOGRAPHY:
            return np.eye(3, 3, dtype=np.float32)
        return np.eye(2, 3, dtype=np.float32)

    def _warp_frame(self, frame, warp_matrix):
        if self.warp_mode == cv2.MOTION_HOMOGRAPHY:
            return cv2.warpPerspective (frame, warp_matrix, self.shape)#, flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        return cv2.warpAffine(frame, warp_matrix, self.shape, flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)

    def eat_frame(self, frame):
        warp_matrix = self._get_warp_matrix()
        grey_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.last_frame is None:
            self.last_frame = grey_frame
            self.shape = (grey_frame.shape[1], grey_frame.shape[0])
            return frame
        else:
            (cc, self.warp_matrix) = cv2.findTransformECC(self.last_frame, grey_frame, self.warp_matrix, self.warp_mode, self.criteria)
            aligned_frame = self._warp_frame(frame, self.warp_matrix)
            self.last_frame = cv2.cvtColor(aligned_frame, cv2.COLOR_BGR2GRAY)
            return aligned_frame

class Resampler:
    def __init__(self, xscale, yscale):
        self.xscale = xscale
        self.yscale = yscale

    def eat_frame(self, frame):
        if self.xscale == self.yscale == 1:
            return frame
        shape = frame.shape
        down_shape = (round(shape[1]*self.yscale), round(shape[0]*self.xscale))
        return cv2.resize(frame, down_shape) 

def filter_frames(stream, filters, frame_limit=0):
    frame_count = 0
    time_keeper = TimeKeeper()
    while True:
        time_keeper.start('io')
        status, frame = stream.read()
        time_keeper.end('io')
        frame_count += 1
        if not status or (frame_limit > 0 and frame_count >= frame_limit):
            break

        print('Frame {}...'.format(frame_count))

        input = frame
        for filter in filters:
            filter_name = filter.__class__.__name__
            time_keeper.start(filter_name)
            output = filter.eat_frame(input)
            time_keeper.end(filter_name)
            input = output

    return time_keeper

# -----------------------------------------------------------------------------

def main():
    cfg = Config('config.yaml')
    # Downscaling factor for both input and output.
    # Use this to keep your runtime under control at the cost of resolution.
    # Set to 1 to disable resampling
    scale = cfg.get('image_scale')

    # Apply this effect to the first N frames only.
    frame_limit = cfg.get('frame_limit')

    align_cfg = cfg.get('alignment')
    align_iterations = align_cfg['termination_iterations']
    align_mode = align_cfg['mode']
    align_termination_eps = align_cfg['termination_eps']

    in_filename = sys.argv[1]
    stream = cv2.VideoCapture(in_filename)
    aligner = Aligner(mode=align_mode, iterations=align_iterations, eps=align_termination_eps)
    resampler = Resampler(scale, scale)
    accum = Accumulator()

    print('Aligning and stacking...')
    times = filter_frames(stream, [resampler, aligner, accum], frame_limit)
    print('Calculating mean image...')
    result_image = accum.get_mean_image()

    base_filename = os.path.basename(os.path.splitext(in_filename)[0])
    filename = '{}-{}-{}-{}-{}it-{}f.png'.format(base_filename, align_mode, align_termination_eps, scale, align_iterations, frame_limit)
    cv2.imwrite('out/'+filename, result_image) 

    print(times.report())

if __name__ == '__main__':
    main()

