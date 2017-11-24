import cv2
import numpy as np

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

