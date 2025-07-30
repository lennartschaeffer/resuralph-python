import os
import logging
import requests
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class HypothesisClient:
    def __init__(self):
        self.api_key = os.getenv('HYPOTHESIS_API_KEY')
        self.base_url = 'https://api.hypothes.is/api'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_annotation(self, annotation_data: Dict) -> Optional[Dict]:
        
        try:
            url = f"{self.base_url}/annotations"
            
            response = requests.post(
                url,
                json=annotation_data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                annotation = response.json()
                logger.info(f"Successfully created annotation: {annotation.get('id', 'unknown')}")
                return annotation
            else:
                logger.error(f"Failed to create annotation. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error creating annotation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating annotation: {str(e)}")
            return None
    
    def create_bulk_annotations(self, annotations: List[Dict]) -> Dict:
        
        results = {
            'created': [],
            'failed': [],
            'total': len(annotations)
        }
        
        for i, annotation_data in enumerate(annotations):
            try:
                # Add small delay between requests to avoid rate limiting
                if i > 0:
                    time.sleep(0.5)
                
                created_annotation = self.create_annotation(annotation_data)
                
                if created_annotation:
                    results['created'].append({
                        'id': created_annotation.get('id'),
                        'text': annotation_data.get('text', '')[:50] + '...'
                    })
                else:
                    results['failed'].append({
                        'error': 'API returned null',
                        'text': annotation_data.get('text', '')[:50] + '...'
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'error': str(e),
                    'text': annotation_data.get('text', '')[:50] + '...'
                })
        
        success_rate = len(results['created']) / results['total'] * 100 if results['total'] > 0 else 0
        logger.info(f"Bulk annotation creation complete: {len(results['created'])}/{results['total']} successful ({success_rate:.1f}%)")
        
        return results
    
    def validate_annotation_data(self, annotation_data: Dict) -> bool:
        
        required_fields = ['uri', 'target', 'text']
        
        for field in required_fields:
            if field not in annotation_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate target structure
        target = annotation_data.get('target', [])
        if not isinstance(target, list) or len(target) == 0:
            logger.error("Target must be a non-empty list")
            return False
        
        # Validate text content
        text = annotation_data.get('text', '')
        if not text or len(text.strip()) == 0:
            logger.error("Annotation text cannot be empty")
            return False
        
        return True


# Global instance
hypothesis_client = HypothesisClient()


def create_annotation(annotation_data: Dict) -> Optional[Dict]:
    """Convenience function for creating single annotation"""
    return hypothesis_client.create_annotation(annotation_data)


def create_bulk_annotations(annotations: List[Dict]) -> Dict:
    """Convenience function for creating multiple annotations"""
    return hypothesis_client.create_bulk_annotations(annotations)


def validate_annotation_data(annotation_data: Dict) -> bool:
    """Convenience function for validating annotation data"""
    return hypothesis_client.validate_annotation_data(annotation_data)