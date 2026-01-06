import time
import cv2
import os
from .aws_clients import aws

def start_shot_detection(bucket, video_key):
    print(f"🕵️  Requesting Shot Detection for: {video_key}...")
    response = aws.rekognition_client.start_segment_detection(
        Video={'S3Object': {'Bucket': bucket, 'Name': video_key}},
        SegmentTypes=['SHOT']
    )
    return response['JobId']

def wait_for_job(job_id):
    print("⏳ Waiting for shot detection to complete...")
    while True:
        status = aws.rekognition_client.get_segment_detection(JobId=job_id)
        s = status['JobStatus']
        if s in ['SUCCEEDED', 'FAILED']:
            return status
        print("   ...still processing...")
        time.sleep(5)

def extract_frames_for_shot(video_path, start_ms, end_ms, max_frames=5):
    """
    Extracts up to 'max_frames' evenly spaced across the shot duration.
    Returns a list of image bytes.
    """
    duration = end_ms - start_ms
    if duration < 1000: # If shot is < 1 second, take just 1 frame
        timestamps = [start_ms + (duration / 2)]
    else:
        # Logic: 0%, 25%, 50%, 75%, 90%
        # Or simple: Every 1 second, up to max_frames
        step = duration / (max_frames + 1)
        timestamps = [start_ms + step * i for i in range(1, max_frames + 1)]

    frames = []
    cap = cv2.VideoCapture(video_path)
    
    for ts in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, ts)
        success, frame = cap.read()
        if success:
            _, buffer = cv2.imencode('.jpg', frame)
            frames.append(buffer.tobytes())
            
    cap.release()
    return frames
