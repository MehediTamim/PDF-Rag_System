import weaviate
from weaviate.classes.config import Configure, Property, DataType
from typing import List, Dict, Optional, Any
from config.settings import settings
from utils.logger import Logger

logger = Logger.get_logger('weaviate_client')


class WeaviateRAG:
    def __init__(self, host: str = None, port: int = None, grpc_port: int = None):
        try:
            host = host or settings.WEAVIATE_HOST
            port = port or settings.WEAVIATE_PORT
            grpc_port = grpc_port or settings.WEAVIATE_GRPC_PORT

            self.client = weaviate.connect_to_local(host=host, port=port, grpc_port=grpc_port)

            if not self.client.is_ready():
                raise ConnectionError(f"Failed to connect to Weaviate at {host}:{port}")

            logger.info(f"Connected to Weaviate at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate client: {e}")
            raise

    def get_or_create_collection(self, pdf_name: str):
        try:
            collection_name = pdf_name.replace('.pdf', '').replace(' ', '_').replace('-', '_')

            if self.client.collections.exists(collection_name):
                logger.info(f"Collection '{collection_name}' already exists")
                return collection_name

            self.client.collections.create(
                name=collection_name,
                vector_config=Configure.Vectors.self_provided(),
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="page", data_type=DataType.INT),
                    Property(name="chunk_id", data_type=DataType.INT)
                ]
            )

            logger.info(f"Collection '{collection_name}' created")
            return collection_name

        except Exception as e:
            logger.error(f"Error in get_or_create_collection: {e}")
            raise

    def check_collection_exists(self, collection_name: str) -> bool:
        try:
            return self.client.collections.exists(collection_name)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    def list_all_collections(self) -> Optional[List[str]]:
        try:
            collections = self.client.collections.list_all()
            logger.debug(f"Found {len(collections)} collections")
            return list(collections.keys())
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return None

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.collections.delete(collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            raise Exception(f"Failed to delete collection '{collection_name}': {str(e)}")

    def add_documents(self, collection_name: str, documents: List[Dict], embeddings: List[List[float]]):
        try:
            if len(documents) != len(embeddings):
                raise ValueError("Documents and embeddings length mismatch")

            collection = self.client.collections.get(collection_name)

            with collection.batch.dynamic() as batch:
                for doc, embedding in zip(documents, embeddings):
                    batch.add_object(
                        properties={
                            "content": doc["content"],
                            "page": doc["page"]
                        },
                        vector=embedding
                    )

            logger.debug(f"Added {len(documents)} documents to '{collection_name}'")

        except Exception as e:
            logger.error(f"Error adding documents to '{collection_name}': {e}")
            raise

    def get_collection_object_count(self, collection_name: str) -> Optional[int]:
        try:
            collection = self.client.collections.get(collection_name)
            count_response = collection.aggregate.over_all(total_count=True)
            return count_response.total_count
        except Exception as e:
            logger.error(f"Error getting object count for '{collection_name}': {e}")
            return None

    def semantic_search(self, collection_name: str, query_vector: List[float], limit: int = 5, min_certainty: float = 0.7) -> List[Dict[str, Any]]:
        try:
            collection = self.client.collections.get(collection_name)
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                certainty=min_certainty
            )
            logger.debug(f"Semantic search found {len(response.objects)} results")
            return self._format_results(response.objects)
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def hybrid_search(self, collection_name: str, query_text: str, query_vector: List[float], limit: int = 5, alpha: float = 0.5) -> List[Dict[str, Any]]:
        try:
            collection = self.client.collections.get(collection_name)
            response = collection.query.hybrid(
                query=query_text,
                vector=query_vector,
                alpha=alpha,
                limit=limit
            )
            logger.debug(f"Hybrid search found {len(response.objects)} results")
            return self._format_results(response.objects)
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def close(self):
        try:
            self.client.close()
            logger.info("Weaviate connection closed")
        except Exception as e:
            logger.error(f"Error closing Weaviate connection: {e}")

    @staticmethod
    def _format_results(objects) -> List[Dict[str, Any]]:
        return [{
            "id": str(obj.uuid),
            "content": obj.properties.get("content", ""),
            "page": obj.properties.get("page", 0)
        } for obj in objects]
