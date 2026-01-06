# modules/editor.py
import subprocess
import os

def seconds_to_hms(seconds):
    """Converts seconds to HH:MM:SS.mmm format"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

def create_highlight_reel(video_path, clips, output_file="highlight_reel.mp4"):
    """
    Cuts snippets from the video and merges them.
    clips: List of dicts [{'start_seconds': 10.5, 'duration': 5.0}, ...]
    """
    print(f"✂️  Editing {len(clips)} clips into '{output_file}'...")

    # 1. Create a temporary text file listing the clips (FFmpeg concat method)
    # Note: We cut each clip to a temp file first, then merge. 
    # This is more robust for different codecs.
    
    temp_files = []
    
    for i, clip in enumerate(clips):
        start = clip['start_seconds']
        duration = clip['duration']
        temp_name = f"temp_clip_{i}.mp4"
        
        # FFmpeg command to cut ONLY this segment (re-encoding for safety)
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-i', video_path,
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'fast', # Re-encode video
            '-c:a', 'aac',                        # Re-encode audio
            temp_name
        ]
        
        # Run silently
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_files.append(temp_name)
        print(f"   - Cut clip {i+1}: Start {start:.2f}s (Duration: {duration:.2f}s)")

    # 2. Create list file for concatenation
    with open("mylist.txt", "w") as f:
        for tf in temp_files:
            f.write(f"file '{tf}'\n")

    # 3. Concatenate (Stitch)
    print("🎬 Stitching final movie...")
    stitch_cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'mylist.txt',
        '-c', 'copy',
        output_file
    ]
    subprocess.run(stitch_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Cleanup
    for tf in temp_files:
        os.remove(tf)
    os.remove("mylist.txt")
    
    print(f"✅ Created: {output_file}")