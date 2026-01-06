import json
import base64
import config
from modules.aws_clients import aws

def generate_vector_from_text(text_input):
    """
    Generates a vector for the text description using Titan Multimodal.
    """
    if not text_input: return None
    
    payload = {
        "inputText": text_input
    }
    
    try:
        response = aws.bedrock_client.invoke_model(
            modelId=config.BEDROCK_EMBEDDING_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        response_body = json.loads(response.get('body').read())
        return response_body.get('embedding')
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None