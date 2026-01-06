# search_engine.py
import json
import numpy as np
import config
from modules import embedder,editor

def load_memory(file_path):
    print(f"📂 Loading memory from {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} shots.")
    return data

def cosine_similarity(v1, v2):
    """
    Calculates how similar two vectors are (0 to 1).
    1 = Identical, 0 = Different.
    """
    if not v1 or not v2: return 0.0
    
    # Convert to numpy arrays
    a = np.array(v1)
    b = np.array(v2)
    
    # Compute Cosine Similarity
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_video(query, db, top_k=3):
    print(f"\n🔎 Searching for: '{query}'...")
    
    # 1. Convert Query to Vector
    query_vector = embedder.generate_vector_from_text(query)
    
    # 2. Compare against all shots
    results = []
    for shot in db:
        if shot.get('vector'):
            score = cosine_similarity(query_vector, shot['vector'])
            results.append((score, shot))
    
    # 3. Sort
    results.sort(key=lambda x: x[0], reverse=True)
    
    # 4. Print Winners
    top_matches = results[:top_k]
    print(f"\n🏆 TOP {top_k} MATCHES:")
    
    clips_to_edit = []
    
    for i, (score, shot) in enumerate(top_matches):
        print(f"   #{i+1} [Score: {score:.4f}] {shot['time_start']} -> {shot['time_end']}")
        print(f"       📝 {shot['description'][:100]}...")
        
        # Calculate seconds for FFmpeg
        # (Assuming you saved StartTimestampMillis in ingestion, otherwise parse SMPTE)
        # Let's use the 'StartTimestampMillis' if available in your JSON, or parse the SMPTE
        
        # Quick SMPTE Parser fallback (HH:MM:SS;FF)
        def smpte_to_sec(smpte):
            parts = smpte.replace(';', ':').split(':')
            return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2]) + int(parts[3])/30.0

        if 'start_ms' in shot:
            start_sec = shot['start_ms'] / 1000.0
            end_sec = shot['end_ms'] / 1000.0
        else:
             # Fallback if ingestion didn't save ms
             start_sec = smpte_to_sec(shot['time_start'])
             end_sec = smpte_to_sec(shot['time_end'])
             
        clips_to_edit.append({
            'start_seconds': start_sec,
            'duration': end_sec - start_sec
        })

    return clips_to_edit

if __name__ == "__main__":
    db = load_memory("reelsmith_memory.json")
    
    while True:
        user_query = input("\n🗣️  What scene are you looking for? (or 'q' to quit): ")
        if user_query.lower() == 'q': break
        
        # Run Search
        found_clips = search_video(user_query, db)
        
        # Ask to Render
        if found_clips:
            ask = input("🎬 Render these clips into a video? (y/n): ")
            if ask.lower() == 'y':
                editor.create_highlight_reel(config.LOCAL_VIDEO_PATH, found_clips)
                print("✨ Video saved as 'highlight_reel.mp4'!")
    # Load Database
    db = load_memory("reelsmith_memory.json")
    
    # Interactive Loop
    while True:
        user_query = input("\n🗣️  What scene are you looking for? (or 'q' to quit): ")
        if user_query.lower() == 'q':
            break
        
        search_video(user_query, db)