from langchain_experimental.text_splitter import SemanticChunker
from infrastructure.llm.embeddings import embedding_service
from typing import List
from utils.logger import Logger

logger = Logger.get_logger('semantic_chunker')


class SimpleSemanticChunker:

    def __init__(self):
        try:
            self.embedding_model = embedding_service
            self.semantic_splitter = SemanticChunker(
                embeddings=self._create_langchain_embeddings(),
                breakpoint_threshold_type="percentile"
            )
            logger.info("Semantic chunker initialized")
        except Exception as e:
            logger.error(f"Failed to initialize semantic chunker: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        try:
            if not text or len(text.strip()) == 0:
                return []

            chunks = self.semantic_splitter.split_text(text)
            logger.debug(f"Text chunked into {len(chunks)} pieces")
            return chunks

        except Exception as e:
            logger.warning(f"Error in semantic chunking, returning original text: {e}")
            return [text]

    def _create_langchain_embeddings(self):
        try:
            from langchain_core.embeddings import Embeddings

            class BGEEmbeddings(Embeddings):
                def __init__(self, model):
                    self.model = model

                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    return self.model.encode(texts, convert_to_numpy=True).tolist()

                def embed_query(self, text: str) -> List[float]:
                    return self.model.encode([text], convert_to_numpy=True)[0].tolist()

            return BGEEmbeddings(self.embedding_model)

        except Exception as e:
            logger.error(f"Error creating LangChain embeddings: {e}")
            raise
