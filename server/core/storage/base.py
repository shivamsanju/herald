import io

from minio import Minio
from minio.error import S3Error
from minio.versioningconfig import ENABLED, VersioningConfig
from typing import List
from core.schema import CustomDoc
from utils.logger import logger


class MinioStorage:
    def __init__(self, endpoint, access_key, secret_key):
        try:
            self.client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=False
            )
        except S3Error as exc:
            logger.exception(f"Cannot connect to minio: {str(exc)}")

    def create_bucket_if_not_exists(self, bucket_name):
        found = self.client.bucket_exists(bucket_name)
        if not found:
            self.client.make_bucket(bucket_name)
            self.client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))

    def upload_document(self, document: CustomDoc):
        self.create_bucket_if_not_exists(document.asset_id)
        bucket_name = document.asset_id
        object_name = document.doc_id + ".txt"
        content_binary = document.text.encode("utf-8")
        length = len(content_binary)
        content = io.BytesIO(content_binary)
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=content,
            length=length,
            metadata=document.metadata,
            num_parallel_uploads=1,
        )

    def upload_documents(self, documents: List[CustomDoc], batch_size=50):
        for i in range(0, len(documents), min(batch_size, len(documents))):
            batch = documents[i : i + batch_size]
            self.upload_batch(batch)

    def upload_batch(self, batch: List[CustomDoc]):
        for doc in batch:
            self.upload_document(doc)

    def delete_documents(self, bucket_name, document_names):
        for document_name in document_names:
            try:
                self.client.remove_object(bucket_name, document_name)
            except S3Error as exc:
                logger.error(f"Error deleting document {document_name}: {exc}")
