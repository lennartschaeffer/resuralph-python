import os
import logging
from datetime import datetime, timezone
from supabase import create_client, Client

logger = logging.getLogger(__name__)

DOCUMENTS_TABLE = "documents"
AI_REVIEW_USAGE_TABLE = "ai_review_usage"


class SupabaseManager:
    def __init__(self):
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SECRET_KEY"]
        self.client: Client = create_client(url, key)

    def insert_document(
        self,
        id: str,
        s3_key: str,
        title: str | None,
        uploader_id: str,
        uploader_username: str,
        version: int,
    ) -> dict | None:
        try:
            result = (
                self.client.table(DOCUMENTS_TABLE)
                .insert(
                    {
                        "id": id,
                        "s3Key": s3_key,
                        "title": title,
                        "uploaderId": uploader_id,
                        "uploaderUsername": uploader_username,
                        "version": version,
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )
            return result.data[0] if result.data else None # type: ignore
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return None

    def delete_document(self, id: str) -> bool:
        try:
            self.client.table(DOCUMENTS_TABLE).delete().eq("id", id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting document {id}: {e}")
            return False

    def get_documents_by_uploader(self, uploader_id: str) -> list[dict]:
        try:
            result = (
                self.client.table(DOCUMENTS_TABLE)
                .select("*")
                .eq("uploaderId", uploader_id)
                .order("version", desc=False)
                .execute()
            )
            return result.data or [] # type: ignore
        except Exception as e:
            logger.error(f"Error fetching documents for uploader {uploader_id}: {e}")
            return []

    def get_latest_version(self, uploader_id: str) -> int:
        try:
            result = (
                self.client.table(DOCUMENTS_TABLE)
                .select("version")
                .eq("uploaderId", uploader_id)
                .order("version", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["version"] # type: ignore
            return 0
        except Exception as e:
            logger.error(f"Error fetching latest version for {uploader_id}: {e}")
            return 0

    def get_latest_document(self, uploader_id: str) -> dict | None:
        try:
            result = (
                self.client.table(DOCUMENTS_TABLE)
                .select("*")
                .eq("uploaderId", uploader_id)
                .order("version", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None # type: ignore
        except Exception as e:
            logger.error(f"Error fetching latest document for {uploader_id}: {e}")
            return None

# Global instance
supabase_manager = SupabaseManager()
