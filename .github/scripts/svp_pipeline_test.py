#!/usr/bin/env python3
import vapoursynth as vs
import json
import sys
import os

# Load SVPflow plugins first - they must be loaded before creating the core
plugin_dir = '/usr/local/opt/vapoursynth/lib/vapoursynth/'

for p in ['libsvpflow1_vs64.dylib', 'libsvpflow2_vs64.dylib']:
    path = os.path.join('/usr/local/opt/vapoursynth/lib/vapoursynth/', p)
    if os.path.exists(path):
        vs.core.std.LoadPlugin(path=path)
        print(f'Loaded: {p}')
    else:
        print(f'MISSING: {path}')

core = vs.core

clip = core.std.BlankClip(width=1920, height=1080, length=60, fpsnum=30, fpsden=1, format=vs.YUV420P8)
print(f"Test clip: {clip.width}x{clip.height}, {clip.num_frames} frames @ {float(clip.fps_num)/float(clip.fps_den):.2f} fps")

super_str = json.dumps({"pel": 1, "gpu": True})
vectors_str = json.dumps({"block": {"w": 8, "overlap": 2}, "main": {"search": {"distance": 0, "coarse": {"distance": -10}}}})
smooth_str = json.dumps({"rate": {"num": 60, "abs": True}, "algo": 13, "mask": {"area": 50, "area_sharp": 1.2}, "scene": {"blend": False, "mode": 0, "limits": {"blocks": 9999999}}})

try:
    super_clip = core.svp1.Super(clip, super_str)
    print("SVSuper: OK")
    vectors = core.svp1.Analyse(super_clip['clip'], super_clip['data'], clip, vectors_str)
    print("SVAnalyse: OK")
    smooth = core.svp2.SmoothFps(clip, super_clip['clip'], super_clip['data'], vectors['clip'], vectors['data'], smooth_str)
    print(f"SVSmoothFps: OK - Output: {smooth.width}x{smooth.height} @ {float(smooth.fps_num)/float(smooth.fps_den):.2f} fps, {smooth.num_frames} frames")

    frame_count = 0
    for i, frame in enumerate(smooth.frames()):
        frame_count += 1
        if frame_count >= 10:
            break
    print(f"Frames generated: {frame_count}")
    print("SUCCESS: SVP pipeline works without Manager!")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)