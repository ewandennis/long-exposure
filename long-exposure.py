import cv2
import sys
import os.path

from timekeeper import TimeKeeper
from config import Config
from filters import *

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

    filters = []

    # Downscaling factor for both input and output.
    # Use this to keep your runtime under control at the cost of resolution.
    # Set to 1 to disable resampling
    scale = cfg.get('image_scale')
    filters.append(Resampler(scale, scale))

    align_cfg = cfg.get('alignment')
    if align_cfg['enabled']:
        filters.append(Aligner(
          mode=align_cfg['mode'],
          iterations=align_cfg['max_iterations'],
          eps=align_cfg['termination_eps']))

    accum = Accumulator()
    filters.append(accum)

    in_filename = sys.argv[1]
    stream = cv2.VideoCapture(in_filename)

    print('Aligning and stacking...')
    frame_limit = cfg.get('frame_limit') # Apply this effect to the first N frames only.
    time_keeper = filter_frames(stream, filters, frame_limit)

    print('Calculating mean image...')
    time_keeper.start('mean image')
    result_image = accum.get_mean_image()
    time_keeper.end('mean image')

    base_filename = os.path.basename(os.path.splitext(in_filename)[0])
    filename = '{}-{}-{}-{}-{}it-{}f.png'.format(
        base_filename,
        align_cfg['mode'],
        align_cfg['termination_eps'],
        scale,
        align_cfg['max_iterations'],
        frame_limit
    )

    cv2.imwrite('out/'+filename, result_image) 

    if cfg.get('dump_stats'):
        print(time_keeper.report())

if __name__ == '__main__':
    main()

