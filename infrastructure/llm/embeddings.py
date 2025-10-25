from sentence_transformers import SentenceTransformer
from config.settings import settings
from utils.logger import Logger

logger = Logger.get_logger('embeddings')


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            try:
                cls._instance = super().__new__(cls)
                cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info(f"Embedding model loaded: {settings.EMBEDDING_MODEL_NAME}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return cls._instance

    def encode(self, texts, **kwargs):
        try:
            return self.model.encode(texts, **kwargs)
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise


embedding_service = EmbeddingService()
