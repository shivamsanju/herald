from typing import List

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from ray import serve
from sentence_transformers import CrossEncoder
from stop_words import get_stop_words
from transformers import AutoModel

from jobs.ingestion import enqueue_ingestion_job
from schema.base import Context, IngestionPayload, RetrievalPayload
from settings import settings
from utils.logger import logger

from .deps import get_workflow_manager

app = FastAPI()


@serve.deployment()
@serve.ingress(app)
class ServeDeployment:
    def __init__(self):
        self.stop_words = get_stop_words("en")
        self.reranker_model = CrossEncoder(settings.RERANKER_MODEL)
        self.embedding_model = AutoModel.from_pretrained(
            settings.EMBEDDING_MODEL, trust_remote_code=True
        )
        self.vector_store_client = QdrantClient(base_url=settings.QDRANT_BASE_URI)

    def _remove_stopwords(self, text: str) -> str:
        return " ".join([word for word in text.split() if word not in self.stop_words])

    def _get_query_embedding(self, query: str) -> List[float]:
        processed_query = self._remove_stopwords(query)
        embeddings = self.embedding_model.encode([processed_query]).tolist()
        return embeddings[0]

    def _search_chunks_by_vector(
        self, asset_ids: List[str], vector: List[float], limit
    ) -> List[models.ScoredPoint]:
        # Implement this: https://qdrant.tech/articles/hybrid-search/
        try:
            collections = self.vector_store_client.search(
                collection_name=settings.VECTOR_DB_COLLECTION_NAME,
                query_vector=vector,
                query_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key="asset_id",
                            match=models.MatchValue(
                                value=asset_id,
                            ),
                        )
                        for asset_id in asset_ids
                    ]
                    if len(asset_ids) > 0
                    else None,
                ),
                with_payload=True,
                with_vectors=False,
                limit=limit * 10,  # get more elements to remove duplicates
            )
            unique = []
            seen_scores = set()
            for c in collections:
                if c.score not in seen_scores:
                    seen_scores.add(c.score)
                    unique.append(c)
            return unique[:limit]
        except UnexpectedResponse as e:
            logger.error(e)
            return []

    def _rerank_contexts(
        self,
        query: str,
        contexts: List[models.ScoredPoint],
        score_threshold: float = 1,
    ) -> List[Context]:
        if len(contexts) == 0:
            return []
        query_paragraph_pairs = [
            (query, context.payload.get("text")) for context in contexts
        ]
        scores = self.reranker_model.predict(
            query_paragraph_pairs,
            batch_size=50,
        )

        # Update scores in the ranked_chunks
        relevant_contexts = []
        seen_scores = set()
        for context, score in zip(contexts, scores):
            if score >= score_threshold and score not in seen_scores:
                seen_scores.add(score)
                relevant_contexts.append(
                    Context(
                        text=context.payload.get("text"),
                        metadata=context.payload.get("metadata"),
                        score=score,
                    )
                )
        relevant_contexts.sort(key=lambda x: x.score, reverse=True)
        return relevant_contexts

    @app.get("/health")
    def healthcheck(self):
        return True

    @app.post("/retrieve")
    def get_contexts(self, request: RetrievalPayload) -> List[Context]:
        vector = self._get_query_embedding(request.query)
        contexts = self._search_chunks_by_vector(
            request.asset_ids, vector, request.num_contexts
        )
        reranked_contexts = self._rerank_contexts(
            request.query, contexts, request.score_threshold
        )
        return reranked_contexts

    @app.post("/ingest")
    async def submit_ingestion_task(
        self, payload: IngestionPayload, workflow=Depends(get_workflow_manager)
    ):
        enqueue_ingestion_job(payload.asset_id, payload, workflow)
        return JSONResponse(status_code=200, content={"job_id": payload.asset_id})

    @app.get("/ingest/{job_id}/status")
    async def get_task_status(
        self, job_id: str, workflow=Depends(get_workflow_manager)
    ):
        status = workflow.get_status(job_id)
        return JSONResponse(status_code=200, content={"status": status})

    @app.get("/ingest/{job_id}/metadata")
    async def get_workflow_metadata(
        self, job_id: str, workflow=Depends(get_workflow_manager)
    ):
        metadata = workflow.get_metadata(job_id)
        return JSONResponse(status_code=200, content={"metadata": metadata})

    @app.get("/ingest/{job_id}/output")
    async def get_output(self, job_id: str, workflow=Depends(get_workflow_manager)):
        metadata = workflow.get_output(job_id)
        return JSONResponse(status_code=200, content={"output": metadata})
