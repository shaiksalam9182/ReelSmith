# modules/transcriber.py
import time
import json
import urllib.request
from .aws_clients import aws

def start_transcription_job(bucket, video_key, job_name):
    """
    Starts an AWS Transcribe job for the video in S3.
    """
    file_uri = f"s3://{bucket}/{video_key}"
    print(f"👂 Starting Transcription for: {file_uri}")
    
    try:
        aws.transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='mp4',
            LanguageCode='en-US',
            Settings={'ShowSpeakerLabels': False} # Keep it simple for now
        )
        return job_name
    except aws.transcribe.exceptions.ConflictException:
        print(f"⚠️ Job {job_name} already exists. Using existing job.")
        return job_name

def wait_for_job(job_name):
    """
    Polls AWS Transcribe until the job is done.
    """
    print(f"⏳ Waiting for Transcription (Job: {job_name})...")
    while True:
        status = aws.transcribe.get_transcription_job(TranscriptionJobName=job_name)
        s = status['TranscriptionJob']['TranscriptionJobStatus']
        
        if s in ['COMPLETED', 'FAILED']:
            return status['TranscriptionJob']
        
        print("... transcribing audio ...")
        time.sleep(10)

def get_transcript_text(transcript_uri):
    """
    Downloads the JSON result from AWS and parses it into a clean list of segments.
    """
    print("📥 Downloading Transcript JSON...")
    with urllib.request.urlopen(transcript_uri) as response:
        data = json.loads(response.read().decode())
    
    # Extract the flat list of items (words/punctuations)
    items = data['results']['items']
    
    clean_segments = []
    current_sentence = []
    start_time = 0.0
    
    # We will group words into sentences for easier searching later
    for item in items:
        content = item['alternatives'][0]['content']
        type = item.get('type')
        
        if type == 'pronunciation':
            # It's a word
            if not current_sentence:
                start_time = float(item['start_time'])
            current_sentence.append(content)
            
        elif type == 'punctuation':
            # It's punctuation (., ?) - attach to last word and close sentence
            if current_sentence:
                current_sentence[-1] += content
            
            # End of sentence found
            if content in ['.', '?', '!']:
                end_time = start_time # Rough approximation for end of sentence
                # Try to get end time from the item if possible, otherwise use logic
                
                full_text = " ".join(current_sentence)
                clean_segments.append({
                    "text": full_text,
                    "start": start_time,
                    # We define 'end' as the start of the next sentence usually, 
                    # but here we just leave it open or simple.
                    # For RAG, we just need to know "Does this text fall in the shot?"
                })
                current_sentence = []
    
    print(f"✅ Parsed {len(clean_segments)} sentences from audio.")
    return clean_segments

def get_text_in_range(segments, start_sec, end_sec):
    """
    Helper to find all text spoken between start_sec and end_sec.
    """
    matched_text = []
    for seg in segments:
        # If the sentence started inside our shot window
        if seg['start'] >= start_sec and seg['start'] < end_sec:
            matched_text.append(seg['text'])
            
    return " ".join(matched_text)