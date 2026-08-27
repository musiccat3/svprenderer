#!/usr/bin/env python3
import vapoursynth as vs
import json
import time
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

# Also load bestsource if available
bestsource_path = '/usr/local/opt/vapoursynth/lib/vapoursynth/bestsource.dylib'
if os.path.exists(bestsource_path):
    vs.core.std.LoadPlugin(path=bestsource_path)
    print('Loaded: bestsource.dylib')

core = vs.core

# Create test video using ffmpeg first
import subprocess
subprocess.run([
    'arch', '-x86_64', '/usr/local/bin/ffmpeg',
    '-f', 'lavfi', '-i', 'testsrc=duration=30:size=1920x1080:rate=30',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '/tmp/test_30s.mp4', '-y'
], check=True)

# Use ffms2 (ffms2 is usually available with VapourSynth) or bestsource
# Try bestsource first, fallback to ffms2
clip = None
try:
    clip = core.bs.VideoSource(source="/tmp/test_30s.mp4", cachemode=0)
    print("Using bestsource")
except AttributeError:
    try:
        clip = core.ffms2.Source(source="/tmp/test_30s.mp4", cachemode=0)
        print("Using ffms2")
    except AttributeError:
        # Fallback to blank clip for testing
        print("Using blank clip for testing")
        clip = vs.core.std.BlankClip(width=1920, height=1080, length=900, fpsnum=30, fpsden=1, format=vs.YUV420P8)

print(f"Input: {clip.width}x{clip.height} @ {float(clip.fps_num)/float(clip.fps_den):.2f} fps, {clip.num_frames} frames")

# Disable GPU since GitHub Actions runners don't have GPU support
super_str = json.dumps({"pel": 1, "gpu": False})
vectors_str = json.dumps({"block": {"w": 8, "overlap": 2}, "main": {"search": {"distance": 0, "coarse": {"distance": -10}}}})
smooth_str = json.dumps({"rate": {"num": 120, "abs": True}, "algo": 13, "mask": {"area": 50, "area_sharp": 1.2}, "scene": {"blend": False, "mode": 0, "limits": {"blocks": 9999999}}, "gpu": False})

try:
    super_clip = core.svp1.Super(clip, super_str)
    print("SVSuper: OK")
    vectors = core.svp1.Analyse(super_clip['clip'], super_clip['data'], clip, vectors_str)
    print("SVAnalyse: OK")
    smooth = core.svp2.SmoothFps(clip, super_clip['clip'], super_clip['data'], vectors['clip'], vectors['data'], smooth_str)
    print(f"SVSmoothFps: OK - Output: {smooth.width}x{smooth.height} @ {float(smooth.fps_num)/float(smooth.fps_den):.2f} fps, {smooth.num_frames} frames")

    frame_count = 0
    start = time.time()
    for i, frame in enumerate(smooth.frames()):
        frame_count += 1
        if frame_count % 600 == 0:
            elapsed = time.time() - start
            print(f"Frame {frame_count}, elapsed: {elapsed:.1f}s, rate: {frame_count/elapsed:.1f} fps")
    print(f"Total frames: {frame_count}, time: {time.time() - start:.1f}s")
    print("SUCCESS: Full render works without Manager!")
    os._exit(0)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)