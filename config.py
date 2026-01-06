# config.py

# AWS Settings
AWS_REGION = "us-west-2"
S3_BUCKET_NAME = "reel-smith-ai"  # <--- Update this

# Model Settings
BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-image-v1"

# Local Settings
VIDEO_FILENAME = "NightOfTheLivingDead.mp4"        # File in S3
LOCAL_VIDEO_PATH = "NightOfTheLivingDead.mp4"      # File on your laptop
OUTPUT_DB_FILE = "vector_index.json"