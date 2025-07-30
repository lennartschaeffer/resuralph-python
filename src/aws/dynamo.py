import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


class DynamoManager:
    def __init__(self):
        self.dynamodb = boto3.client(
            'dynamodb',
            region_name=os.getenv('BUCKET_REGION')
        )
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME')

    def save_db_resume(self, pdf_url, pdf_name, user_id, version):
        
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

    def clear_all_user_resumes(self, user_id):
        
        try:
            # First get all resumes for the user
            all_resumes = self.get_all_user_resumes(user_id)
            
            if not all_resumes:
                return True  # Nothing to delete
            
            # Delete each resume record
            for resume in all_resumes:
                try:
                    self.dynamodb.delete_item(
                        TableName=self.table_name,
                        Key={
                            'user_id': {'S': user_id},
                            'resume_version': {'S': resume['resume_version']}
                        }
                    )
                except ClientError as e:
                    print(f"Error deleting resume {resume['resume_version']} for user {user_id}: {e}")
                    return False
            
            print(f"Successfully deleted {len(all_resumes)} resume records for user {user_id}")
            return True
            
        except Exception as e:
            print(f"Error clearing all user resumes: {e}")
            return False

    def get_last_ai_review(self, user_id):
        
        try:
            # Use a special key format for AI review tracking
            ai_review_key = f"{user_id}#ai_review"
            
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': {'S': ai_review_key}
                },
                ScanIndexForward=False,  # Get newest first
                Limit=1
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            # Convert DynamoDB format to simple dict
            item = items[0]
            converted_item = {}
            for key, value in item.items():
                if 'S' in value:
                    converted_item[key] = value['S']
                elif 'N' in value:
                    converted_item[key] = value['N']
            
            return converted_item
            
        except ClientError as e:
            print(f"Error querying last AI review for user {user_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get last AI review: {e}")
            return None

    def save_ai_review_attempt(self, user_id):
       
        try:
            # Use a special key format for AI review tracking
            ai_review_key = f"{user_id}#ai_review"
            current_time = datetime.now().isoformat()
            
            item = {
                'user_id': {'S': ai_review_key},
                'resume_version': {'S': f"ai_review_{current_time}"},
                'created_at': {'S': current_time},
                'review_type': {'S': 'ai_review'}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            return True
            
        except ClientError as e:
            print(f"Error saving AI review attempt for user {user_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error saving AI review attempt: {e}")
            return False


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

def get_all_user_resumes(user_id):
    """Convenience function for getting all user resumes"""
    return dynamo_manager.get_all_user_resumes(user_id)

def clear_all_user_resumes(user_id):
    """Convenience function for clearing all user resumes"""
    return dynamo_manager.clear_all_user_resumes(user_id)

def get_last_ai_review(user_id):
    """Convenience function for getting last AI review timestamp"""
    return dynamo_manager.get_last_ai_review(user_id)

def save_ai_review_attempt(user_id):
    """Convenience function for saving AI review attempt"""
    return dynamo_manager.save_ai_review_attempt(user_id)