# modules/analyzer.py
import json
import boto3
from .aws_clients import aws

# Configuration
# Use 'amazon.nova-pro-v1:0' or 'anthropic.claude-3-5-sonnet-20240620-v1:0'
MODEL_ID = "arn:aws:bedrock:us-west-2:556343216872:inference-profile/us.amazon.nova-pro-v1:0" 

def analyze_shot(frames, transcript_text):
    """
    Sends multiple images and context text to the LLM.
    Returns a rich text description.
    """
    
    # 1. Build the User Message Payload
    content_blocks = []
    
    # A. Add the Text Context first
    if transcript_text:
        content_blocks.append({
            "text": f"TRANSCRIPT OF AUDIO IN THIS SCENE:\n'{transcript_text}'\n\n"
        })
    else:
        content_blocks.append({
            "text": "AUDIO TRANSCRIPT: [No dialogue detected]\n\n"
        })

    # B. Add the Images (Iterate through the list of bytes)
    for i, img_bytes in enumerate(frames):
        content_blocks.append({
            "text": f"Image {i+1}:" # Labeling helps the model understand sequence
        })
        content_blocks.append({
            "image": {
                "format": "jpeg", 
                "source": {"bytes": img_bytes}
            }
        })

    # C. Add the Prompt
    prompt = """
    TASK: Analyze this sequence of frames and the audio transcript.
    OUTPUT: A detailed visual and narrative description.
    
    GUIDELINES:
    1. Describe the ACTION: What is physically happening? (e.g., chasing, fighting, kissing).
    2. Describe the EMOTION: What is the mood? (e.g., tense, joyful).
    3. Incorporate the DIALOGUE: Explain how the words relate to the visual.
    
    Return ONLY the description paragraph. Do not add headers like "Here is the analysis".
    """
    content_blocks.append({"text": prompt})

    # 2. Call the Model
    try:
        response = aws.bedrock_client.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": content_blocks}],
            inferenceConfig={"temperature": 0.1, "maxTokens": 500}
        )
        return response['output']['message']['content'][0]['text']
        
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return "Analysis failed."