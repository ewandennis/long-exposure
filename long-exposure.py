import cv2
import numpy as np
import sys

class Accumulator:
    def __init__(self):
        self.accum = None
        self.count = 0

    """Accumulate pixel values across frames"""
    def init(self, frame):
        self.accum = np.zeros(frame.shape, dtype=np.float)
        self.count = 0

    def add_frame(self, frame):
        if self.accum is None:
            self.init(frame)
        norm = frame.astype('float')
        self.accum += norm
        self.count += 1

    def get_mean_image(self):
        mean_float = self.accum / self.count
        return mean_float.astype('uint8') 

stream = cv2.VideoCapture(sys.argv[1])
accum = Accumulator()

while True:
    status, frame = stream.read()
    if not status:
        break

    shape = frame.shape
    smaller = cv2.resize(frame, (shape[0]//4, shape[1]//4))

    accum.add_frame(frame)    

# Write the accumulator to file
cv2.imwrite('accum.png', accum.get_mean_image())
