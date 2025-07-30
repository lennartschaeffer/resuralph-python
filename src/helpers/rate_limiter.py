import logging
from datetime import datetime, timedelta
from aws.dynamo import get_last_ai_review, save_ai_review_attempt

logger = logging.getLogger(__name__)


class RateLimiter:
    
    def can_use_ai_review(self, user_id):
        
        try:
            last_review = get_last_ai_review(user_id)
            
            if not last_review:
                return True, None
            
            # Parse the timestamp
            last_review_time = datetime.fromisoformat(last_review['created_at'])
            current_time = datetime.now()
            
            # Check if 24 hours have passed
            time_diff = current_time - last_review_time
            if time_diff >= timedelta(hours=24):
                return True, None
            
            # Calculate remaining time
            remaining_time = timedelta(hours=24) - time_diff
            hours_remaining = int(remaining_time.total_seconds() // 3600)
            minutes_remaining = int((remaining_time.total_seconds() % 3600) // 60)
            
            if hours_remaining > 0:
                time_str = f"{hours_remaining}h {minutes_remaining}m"
            else:
                time_str = f"{minutes_remaining}m"
            
            return False, time_str
            
        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {str(e)}")
            # On error, allow the review to proceed (fail open)
            return True, None
    
    def record_ai_review_usage(self, user_id):
        
        try:
            return save_ai_review_attempt(user_id)
        except Exception as e:
            logger.error(f"Error recording AI review usage for user {user_id}: {str(e)}")
            return False
    


# Global instance
rate_limiter = RateLimiter()

def can_use_ai_review(user_id):
    """Convenience function for checking AI review rate limit"""
    return rate_limiter.can_use_ai_review(user_id)

def record_ai_review_usage(user_id):
    """Convenience function for recording AI review usage"""
    return rate_limiter.record_ai_review_usage(user_id)