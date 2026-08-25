#!/usr/bin/env python3
"""
Download GitHub Actions artifacts for x86_64 SVP Renderer
"""
import os
import sys
import subprocess
import argparse
import tempfile
import shutil

def download_artifacts(repo, workflow_name, run_id=None):
    """Download artifacts from GitHub Actions run"""
    # First, get the run ID if not provided
    if run_id is None:
        print("Fetching latest workflow run...")
        result = subprocess.run([
            'gh', 'run', 'list',
            '--repo', repo,
            '--workflow', 'Build x86_64 VapourSynth + SVPflow',
            '--limit', '1',
            '--json', 'databaseId,conclusion,createdAt',
            '--jq', '.[0].databaseId'
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error getting run ID: {result.stderr}")
            return None
        run_id = result.stdout.strip()
        if not run_id:
            print("No workflow runs found")
            return None
    
    print(f"Downloading artifacts from run {run_id}...")
    
    # Download artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([
            'gh', 'run', 'download',
            '--repo', 'phoenix2/svprenderer',
            '--dir', '/tmp/gh_artifacts',
            str(run_id)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error downloading artifacts: {result.stderr}")
            return None
        
        print("Artifacts downloaded to /tmp/gh_artifacts")
        return '/tmp/gh_artifacts'

def install_artifacts(artifact_dir, install_prefix='/usr/local'):
    """Install downloaded artifacts to system"""
    import shutil
    
    artifact_dir = '/tmp/gh_artifacts'
    if not os.path.exists(artifact_dir):
        print("No artifacts found")
        return False
    
    # Install VapourSynth
    vapoursynth_src = os.path.join(artifact_dir, 'vapoursynth')
    if os.path.exists(vapoursynth_src):
        dest = '/usr/local'
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(vapoursynth_src, dest)
        print(f"Installed VapourSynth to {dest}")
    
    # Install SVPflow libraries
    svp_src = os.path.join(artifact_dir, 'svpflow-4.2.0.142')
    if os.path.exists(svp_src):
        dest = '/usr/local/lib/vapoursynth'
        os.makedirs(dest, exist_ok=True)
        for f in os.listdir(svp_src):
            if f.endswith('.dylib'):
                shutil.copy2(os.path.join(svp_src, f), os.path.join(dest, f))
                print(f"Installed {f}")
    
    # Install FFmpeg
    ffmpeg_src = os.path.join(artifact_dir, 'ffmpeg')
    if os.path.exists(ffmpeg_src):
        dest = '/usr/local/bin/ffmpeg'
        shutil.copy2(ffmpeg_src, dest)
        os.chmod(dest, 0o755)
        print(f"Installed FFmpeg to {dest}")
    
    return True

def verify_installation():
    """Verify the installation works"""
    import subprocess
    
    # Test vspipe
    result = subprocess.run(['arch', '-x86_64', '/usr/local/bin/vspipe', '--version'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"vspipe failed: {result.stderr}")
        return False
    print(f"vspipe version: {result.stdout.strip()}")
    
    # Test VapourSynth + SVP load
    test_code = '''
import sys
sys.path.insert(0, '/usr/local/lib/python3.12/site-packages')
import vapoursynth as vs
core = vs.core
for p in ['libsvpflow1_vs64.dylib', 'libsvpflow2_vs64.dylib']:
    path = f'/usr/local/lib/vapoursynth/{p}'
    core.std.LoadPlugin(path=path)
    print(f'Loaded: {p}')
print('All plugins loaded successfully')
'''
    result = subprocess.run(['arch', '-x86_64', '/usr/local/bin/python3', '-c', '''
import sys
sys.path.insert(0, '/usr/local/lib/python3.12/site-packages')
import vapoursynth as vs
core = vs.core
for p in ['libsvpflow1_vs64.dylib', 'libsvpflow2_vs64.dylib']:
    path = f'/usr/local/lib/vapoursynth/{p}'
    core.std.LoadPlugin(path=path)
    print(f'Loaded: {p}')
print('All plugins loaded successfully')
'''], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"SVP load test failed: {result.stderr}")
        return False
    print(result.stdout.strip())
    
    # Test SVP pipeline
    test_pipeline = '''
import vapoursynth as vs
core = vs.core
clip = core.std.BlankClip(width=1920, height=1080, length=60, fpsnum=30, fpsden=1, format=vs.YUV420P8)
import json
super_str = '{"pel": 1, "gpu": true}'
vectors_str = '{"block": {"w": 8, "overlap": 2}, "main": {"search": {"distance": 0, "coarse": {"distance": -10}}}}'
smooth_str = '{"rate": {"num": 60, "abs": true}, "algo": 13, "mask": {"area": 50, "area_sharp": 1.2}, "scene": {"blend": false, "mode": 0, "limits": {"blocks": 9999999}}}'
super_clip = core.svp1.Super(clip, super_str)
vectors = core.svp1.Analyse(super_clip['clip'], super_clip['data'], clip, vectors_str)
smooth = core.svp2.SmoothFps(clip, super_clip['clip'], super_clip['data'], vectors['clip'], vectors['data'], smooth_str)
print(f"Output: {smooth.width}x{smooth.height} @ {float(smooth.fps_num)/float(smooth.fps_den):.2f} fps, {smooth.num_frames} frames")
frame_count = 0
for frame in smooth.frames():
    frame_count += 1
    if frame_count >= 10:
        break
print(f"SVP pipeline works! Generated {frame_count} frames")
'''
    result = subprocess.run(['arch', '-x86_64', '/usr/local/bin/python3', '-c', test_pipeline], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SVP pipeline test failed: {result.stderr}")
        return False
    print(result.stdout.strip())
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Download and install SVP Renderer artifacts')
    parser.add_argument('--repo', default='phoenix2/svprenderer', help='GitHub repo')
    parser.add_argument('--run-id', type=int, help='Specific run ID to download')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing installation')
    
    args = parser.parse_args()
    
    if args.verify_only:
        print("Verifying existing installation...")
        if verify_installation():
            print("\n✅ Installation verified successfully!")
        else:
            print("\n❌ Verification failed")
            sys.exit(1)
        return
    
    # Download artifacts
    artifact_dir = download_artifacts(args.repo, 'Build x86_64 VapourSynth + SVPflow')
    if not artifact_dir:
        print("Failed to download artifacts")
        sys.exit(1)
    
    # Install
    print("Installing artifacts...")
    if not install_artifacts('/tmp/gh_artifacts'):
        print("Failed to install artifacts")
        sys.exit(1)
    
    # Verify
    print("\nVerifying installation...")
    if verify_installation():
        print("\n✅ Installation successful!")
        print("\nYou can now use the standalone SVP renderer:")
        print("  arch -x86_64 /usr/local/bin/vspipe ...")
        print("  arch -x86_64 /usr/local/bin/python3 -c \"import vapoursynth...\"")
    else:
        print("\n❌ Verification failed")
        sys.exit(1)

if __name__ == '__main__':
    main()