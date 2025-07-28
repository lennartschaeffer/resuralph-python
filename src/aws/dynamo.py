import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


class DynamoManager:
    def __init__(self):
        self.dynamodb = boto3.client(
            'dynamodb',
            region_name=os.getenv('BUCKET_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME')

    def save_db_resume(self, pdf_url, pdf_name, user_id, version):
        """
        Save resume metadata to DynamoDB
        
        Args:
            pdf_url (str): S3 URL of the PDF
            pdf_name (str): Original filename
            user_id (str): Discord user ID
            version (str): Resume version (e.g., "v1", "v2")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            item = {
                'user_id': {'S': user_id},
                'resume_version': {'S': version},
                'resume_url': {'S': pdf_url},
                'resume_name': {'S': pdf_name},
                'created_at': {'S': datetime.now().isoformat()}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            return True
            
        except ClientError as e:
            print(f"Error saving to DynamoDB: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error in DynamoDB save: {e}")
            return False

    def get_latest_db_resume(self, user_id):
        """
        Get the latest resume for a user
        
        Args:
            user_id (str): Discord user ID
            
        Returns:
            list: List of resume records (empty if none found)
        """
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id}
                },
                ScanIndexForward=False,  # Get newest first
                Limit=1
            )
            
            items = response.get('Items', [])
            
            # Convert DynamoDB format to simple dict
            result = []
            for item in items:
                converted_item = {}
                for key, value in item.items():
                    # Extract the actual value from DynamoDB format
                    if 'S' in value:
                        converted_item[key] = value['S']
                    elif 'N' in value:
                        converted_item[key] = value['N']
                result.append(converted_item)
            
            return result
            
        except ClientError as e:
            print(f"Error querying DynamoDB: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in DynamoDB query: {e}")
            return []

    def update_db_resume(self, user_id, pdf_url, pdf_name):
        """
        Update resume by incrementing version and saving new record
        
        Args:
            user_id (str): Discord user ID  
            pdf_url (str): S3 URL of the new PDF
            pdf_name (str): Original filename
            
        Returns:
            str: New version number (e.g., "v2") or None if failed
        """
        try:
            # Get latest version
            latest_resumes = self.get_latest_db_resume(user_id)
            
            if not latest_resumes:
                # First upload, start with v1
                new_version = "v1"
            else:
                # Increment version
                latest_version = latest_resumes[0]['resume_version']
                version_num = int(latest_version[1:])  # Remove 'v' prefix
                new_version = f"v{version_num + 1}"
            
            # Save new record
            success = self.save_db_resume(pdf_url, pdf_name, user_id, new_version)
            
            return new_version if success else None
            
        except Exception as e:
            print(f"Error updating resume version: {e}")
            return None

    def get_all_user_resumes(self, user_id):
        """
        Get all resumes for a user (for testing/debugging)
        
        Args:
            user_id (str): Discord user ID
            
        Returns:
            list: List of all resume records for the user
        """
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id}
                },
                ScanIndexForward=False  # Newest first
            )
            
            items = response.get('Items', [])
            
            # Convert DynamoDB format to simple dict
            result = []
            for item in items:
                converted_item = {}
                for key, value in item.items():
                    if 'S' in value:
                        converted_item[key] = value['S']
                    elif 'N' in value:
                        converted_item[key] = value['N']
                result.append(converted_item)
            
            return result
            
        except ClientError as e:
            print(f"Error querying all resumes: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get all resumes: {e}")
            return []


# Global instance
dynamo_manager = DynamoManager()

def save_db_resume(pdf_url, pdf_name, user_id, version):
    """Convenience function for saving resume to DynamoDB"""
    return dynamo_manager.save_db_resume(pdf_url, pdf_name, user_id, version)

def get_latest_db_resume(user_id):
    """Convenience function for getting latest resume"""
    return dynamo_manager.get_latest_db_resume(user_id)

def update_db_resume(user_id, pdf_url, pdf_name):
    """Convenience function for updating resume version"""
    return dynamo_manager.update_db_resume(user_id, pdf_url, pdf_name)