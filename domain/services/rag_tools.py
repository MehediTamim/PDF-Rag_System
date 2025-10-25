from infrastructure.database.weaviate_client import WeaviateRAG
from infrastructure.llm.embeddings import embedding_service
from utils.logger import Logger
from utils.cache import get_query_cache

logger = Logger.get_logger('rag_tools')


class RAGTools:
    def __init__(self):
        try:
            self.weaviate = WeaviateRAG()
            self.embedding_model = embedding_service
            self.cache = get_query_cache()
            logger.info("RAG tools initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG tools: {e}")
            raise

    def semantic_search(self, collection_name: str, query: str, limit: int = 3):
        try:
            cached_results = self.cache.get(collection_name, query, 'semantic')
            if cached_results is not None:
                logger.info(f"Returning cached semantic search results for: {query[:50]}...")
                return cached_results
            
            query_vector = self.embedding_model.encode([query], convert_to_numpy=True)[0].tolist()
            results = self.weaviate.semantic_search(collection_name, query_vector, limit=limit, min_certainty=0.7)
            
            self.cache.set(collection_name, query, results, 'semantic')
            
            logger.debug(f"Semantic search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def hybrid_search(self, collection_name: str, query: str, limit: int = 3):
        try:
            cached_results = self.cache.get(collection_name, query, 'hybrid')
            if cached_results is not None:
                logger.info(f"Returning cached hybrid search results for: {query[:50]}...")
                return cached_results
            
            query_vector = self.embedding_model.encode([query], convert_to_numpy=True)[0].tolist()
            results = self.weaviate.hybrid_search(collection_name, query, query_vector, limit=limit, alpha=0.5)
            
            self.cache.set(collection_name, query, results, 'hybrid')
            
            logger.debug(f"Hybrid search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def get_cache_stats(self):
        try:
            return self.cache.get_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_cache(self, collection_name: str = None):
        try:
            if collection_name:
                self.cache.clear_collection(collection_name)
            else:
                self.cache.clear_all()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def close(self):
        try:
            self.weaviate.close()
            logger.info("RAG tools closed")
        except Exception as e:
            logger.error(f"Error closing RAG tools: {e}")
