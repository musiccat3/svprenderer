#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/usr/local/lib/python3.12/site-packages')
import vapoursynth as vs

print('VapourSynth version:', vs.__version__)
core = vs.core
print('Core created')

# SVPflow 4.2.0.142 libraries are installed by Homebrew to /usr/local/opt/vapoursynth/lib/vapoursynth/
plugin_dir = '/usr/local/opt/vapoursynth/lib/vapoursynth/'

for p in ['libsvpflow1_vs64.dylib', 'libsvpflow2_vs64.dylib']:
    path = os.path.join(plugin_dir, p)
    if os.path.exists(path):
        core.std.LoadPlugin(path=path)
        print(f'Loaded: {p}')
    else:
        print(f'MISSING: {path}')

print('All plugins loaded successfully')