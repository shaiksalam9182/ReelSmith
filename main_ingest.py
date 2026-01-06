# main_ingest.py
import time
import json
import config
from modules import aws_clients, video_tools, transcriber, analyzer, embedder

def main():
    print("🎬 STARTING PROJECT REELSMITH: INGESTION ENGINE")
    print(f"Target Video: {config.VIDEO_FILENAME}")
    
    # --- PHASE 1: SENSORS (Async Jobs) ---
    print("\n--- PHASE 1: STARTING SENSORS ---")
    
    # 1. Start Vision (Rekognition)
    shot_job_id = video_tools.start_shot_detection(config.S3_BUCKET_NAME, config.VIDEO_FILENAME)
    
    # 2. Start Hearing (Transcribe)
    # Use a unique name to avoid conflicts
    transcribe_job_name = f"reelsmith_job_{int(time.time())}"
    transcriber.start_transcription_job(config.S3_BUCKET_NAME, config.VIDEO_FILENAME, transcribe_job_name)
    
    # 3. Wait for Results
    print(">>> Jobs started. Waiting for completion...")
    shot_result = video_tools.wait_for_job(shot_job_id)
    transcribe_result = transcriber.wait_for_job(transcribe_job_name)
    
    if shot_result['JobStatus'] == 'FAILED' or transcribe_result['TranscriptionJobStatus'] == 'FAILED':
        print("❌ Critical Error: AWS processing failed.")
        return

    # --- PHASE 2: PROCESSING (The Loop) ---
    print("\n--- PHASE 2: ANALYSIS & FUSION ---")
    
    # Parse Data
    shots = [s for s in shot_result['Segments'] if s['Type'] == 'SHOT']
    transcript_uri = transcribe_result['Transcript']['TranscriptFileUri']
    all_sentences = transcriber.get_transcript_text(transcript_uri)
    
    print(f"📊 Found {len(shots)} shots and {len(all_sentences)} sentences.")
    
    final_database = []
    
    # LOOP THROUGH SHOTS (Limit to first 5 for your first test run!)
    for i, shot in enumerate(shots): 
        print(f"\n🎥 Processing Shot {i+1} ({shot['StartTimecodeSMPTE']} -> {shot['EndTimecodeSMPTE']})")

        print(f"DEBUG KEYS: {shot.keys()}")
        
        start_ms = shot['StartTimestampMillis']
        end_ms = shot['EndTimestampMillis']
        
        # A. Extract Evidence (5 Frames + Text)
        frames = video_tools.extract_frames_for_shot(config.LOCAL_VIDEO_PATH, start_ms, end_ms, max_frames=3)
        text_context = transcriber.get_text_in_range(all_sentences, start_ms/1000, end_ms/1000)
        
        print(f"   Evidence: {len(frames)} frames | Text: '{text_context}'")
        
        # B. Analyze (The Brain)
        print("   🧠 Asking Nova to describe this...")
        description = analyzer.analyze_shot(frames, text_context)
        print(f"   📝 Description: {description[:100]}...") # Print first 100 chars
        
        # C. Embed (The Index)
        # Note: We embed the DESCRIPTION, not the raw image now.
        # Check if you want Text Embedding or Multimodal. 
        # For simplicity, let's stick to Titan Multimodal but pass the TEXT description as input.
        # Or better: Use Titan Text Embeddings v2 for search.
        # For now, let's use the Embedder we have (Titan Multimodal accepts text too!)
        vector = embedder.generate_vector_from_text(description) 
        
        # D. Save
        record = {
            "shot_id": i,
            "time_start": shot['StartTimecodeSMPTE'],
            "time_end": shot['EndTimecodeSMPTE'],
            "description": description,
            "transcript": text_context,
            "vector": vector
        }
        final_database.append(record)
        
    # --- PHASE 3: STORAGE ---
    print("\n--- PHASE 3: SAVING MEMORY ---")
    with open("reelsmith_memory.json", "w") as f:
        json.dump(final_database, f)
        
    print(f"✅ DONE! Saved {len(final_database)} smart memories to 'reelsmith_memory.json'")

if __name__ == "__main__":
    main()