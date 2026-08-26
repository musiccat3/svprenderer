#!/usr/bin/env python3
import vapoursynth as vs
import json
import time

core = vs.core

clip = core.bs.VideoSource(source="/tmp/test_30s.mp4", cachemode=0)
print(f"Input: {clip.width}x{clip.height} @ {float(clip.fps_num)/float(clip.fps_den):.2f} fps, {clip.num_frames} frames")

super_str = json.dumps({"pel": 1, "gpu": True})
vectors_str = json.dumps({"block": {"w": 8, "overlap": 2}, "main": {"search": {"distance": 0, "coarse": {"distance": -10}}}})
smooth_str = json.dumps({"rate": {"num": 120, "abs": True}, "algo": 13, "mask": {"area": 50, "area_sharp": 1.2}, "scene": {"blend": False, "mode": 0, "limits": {"blocks": 9999999}}})

super_clip = core.svp1.Super(clip, super_str)
vectors = core.svp1.Analyse(super_clip['clip'], super_clip['data'], clip, super_str)
smooth = core.svp2.SmoothFps(clip, super_clip['clip'], super_clip['data'], vectors['clip'], vectors['data'], smooth_str)
print(f"Output: {smooth.width}x{smooth.height} @ {float(smooth.fps_num)/float(smooth.fps_den):.2f} fps, {smooth.num_frames} frames")

frame_count = 0
start = time.time()
for i, frame in enumerate(smooth.frames()):
    frame_count += 1
    if frame_count % 600 == 0:
        elapsed = time.time() - start
        print(f"Frame {frame_count}, elapsed: {elapsed:.1f}s, rate: {frame_count/elapsed:.1f} fps")
print(f"Total frames: {frame_count}, time: {time.time() - start:.1f}s")