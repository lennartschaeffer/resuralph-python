import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('BUCKET_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.region = os.getenv('BUCKET_REGION')

    def save_s3_resume(self, file_buffer, user_id):
        """
        Upload a PDF resume to S3
        
        Args:
            file_buffer (bytes): PDF file content as bytes
            user_id (str): Discord user ID
            
        Returns:
            dict: {'key': str, 'pdf_url': str} or None if failed
        """
        try:
            # Generate timestamp for unique filename
            timestamp = str(int(datetime.now().timestamp() * 1000))
            key = f"uploads/{user_id}/{timestamp}.pdf"
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_buffer,
                ContentType='application/pdf'
            )
            
            # Generate public URL
            pdf_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            
            return {
                'key': key,
                'pdf_url': pdf_url
            }
            
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in S3 upload: {e}")
            return None

    def delete_s3_resume(self, key):
        """
        Delete a PDF resume from S3
        
        Args:
            key (str): S3 object key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error in S3 delete: {e}")
            return False


# Global instance
s3_manager = S3Manager()

def save_s3_resume(file_buffer, user_id):
    """Convenience function for saving resume to S3"""
    return s3_manager.save_s3_resume(file_buffer, user_id)

def delete_s3_resume(key):
    """Convenience function for deleting resume from S3"""
    return s3_manager.delete_s3_resume(key)