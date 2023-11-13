from typing import Any, List
from llama_index.embeddings.base import BaseEmbedding
from langchain.embeddings import OllamaEmbeddings as LangchainOllamaEmbeddings
from llama_index.bridge.pydantic import PrivateAttr


class HeraldOllamaEmbeddings(BaseEmbedding):
    _model = PrivateAttr()

    def __init__(
        self,
        base_url: str = "http://172.17.0.1:11434",
        model_name: str = "llama2",
        **kwargs: Any,
    ) -> None:
        self._model = LangchainOllamaEmbeddings(base_url=base_url, model=model_name)
        super().__init__(**kwargs)

    @classmethod
    def class_name(cls) -> str:
        return "herald_ollama"

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        embeddings = self._model.embed_query(query)
        return embeddings

    def _get_text_embedding(self, text: str) -> List[float]:
        if len(text) < 1:
            return []
        embeddings = self._model.embed_documents(text[0])
        return embeddings[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.embed_documents(texts)
        return embeddings

