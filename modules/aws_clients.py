import boto3
import config

class AWSManager:
    def __init__(self):
        self.session = boto3.Session(region_name=config.AWS_REGION)
        self.s3_client = self.session.client('s3')
        self.rekognition_client = self.session.client('rekognition')
        self.bedrock_client = self.session.client('bedrock-runtime')
        self.transcribe = self.session.client('transcribe')

aws = AWSManager()