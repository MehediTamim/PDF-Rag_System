from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from infrastructure.llm.pdf_extractor import GeminiPDFExtractor
from infrastructure.llm.embeddings import embedding_service
from infrastructure.database.weaviate_client import WeaviateRAG
from domain.services.semantic_chunker import SimpleSemanticChunker
from config.settings import settings
from utils.logger import Logger

logger = Logger.get_logger('ingestion_service')


class IngestionPipeline:

    def __init__(self, use_chunking=True):
        try:
            self.pdf_extractor = GeminiPDFExtractor()
            self.embedding_model = embedding_service
            self.use_chunking = use_chunking

            if self.use_chunking:
                self.chunker = SimpleSemanticChunker()

            self.weaviate = WeaviateRAG()
            logger.info(f"Ingestion pipeline initialized (chunking: {use_chunking})")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {e}")
            raise

    def process_page_with_chunking(self, collection_name, image, page_num):
        try:
            result = self.pdf_extractor.extract_page(image, page_num)
            content_blocks = result['content_blocks']

            all_chunks = []

            for block in content_blocks:
                content = block.get('content', '')
                data_type = block.get('data_type', 'text')

                if not content or content.strip() == '':
                    continue

                if data_type == 'text':
                    chunks = self.chunker.chunk_text(content)
                    for chunk_text in chunks:
                        all_chunks.append({
                            'content': chunk_text,
                            'type': 'text'
                        })
                else:
                    all_chunks.append({
                        'content': content,
                        'type': data_type
                    })

            for chunk_data in all_chunks:
                embedding = self.embedding_model.encode([chunk_data['content']], convert_to_numpy=True)[0].tolist()

                doc = {
                    'content': chunk_data['content'],
                    'page': page_num
                }

                self.weaviate.add_documents(collection_name, [doc], [embedding])

            logger.debug(f"Page {page_num}: {len(all_chunks)} chunks processed")
            return {'page': page_num, 'chunks': len(all_chunks)}

        except Exception as e:
            logger.error(f"Error processing page {page_num} with chunking: {e}")
            return {'page': page_num, 'chunks': 0, 'error': str(e)}

    def process_page_without_chunking(self, collection_name, image, page_num):
        try:
            content = self.pdf_extractor.extract_page(image, page_num)['content']

            if not content:
                content = 'not found'

            embedding = self.embedding_model.encode([content], convert_to_numpy=True)[0].tolist()

            doc = {
                'content': content,
                'page': page_num
            }

            self.weaviate.add_documents(collection_name, [doc], [embedding])
            logger.debug(f"Page {page_num} processed without chunking")
            return page_num

        except Exception as e:
            logger.error(f"Error processing page {page_num} without chunking: {e}")
            return None

    def ingest_pdf(self, pdf_path, max_workers=None, collection_name=None):
        try:
            pdf_path = Path(pdf_path)
            pdf_name = pdf_path.name
            max_workers = max_workers or settings.MAX_WORKERS

            logger.info(f"Starting PDF ingestion: {pdf_name}")

            if collection_name is None:
                collection_name = self.weaviate.get_or_create_collection(pdf_name)
            else:
                if not self.weaviate.check_collection_exists(collection_name):
                    collection_name = self.weaviate.get_or_create_collection(collection_name)

            images = self.pdf_extractor.pdf_to_images(pdf_path)

            if self.use_chunking:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for i, image in enumerate(images, 1):
                        future = executor.submit(self.process_page_with_chunking, collection_name, image, i)
                        futures.append(future)

                    total_chunks = 0
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            total_chunks += result.get('chunks', 0)
                        except Exception as e:
                            logger.error(f"Error in future result: {e}")

                    logger.info(f"Ingestion complete: {total_chunks} chunks from {len(images)} pages")

            else:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for i, image in enumerate(images, 1):
                        future = executor.submit(self.process_page_without_chunking, collection_name, image, i)
                        futures.append(future)

                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error in future result: {e}")

                    logger.info(f"Ingestion complete: {len(images)} pages processed")

            count = self.weaviate.get_collection_object_count(collection_name)
            logger.info(f"Collection '{collection_name}' now has {count} documents")

            return collection_name

        except Exception as e:
            logger.error(f"Error in ingest_pdf: {e}")
            raise

    def close(self):
        try:
            self.weaviate.close()
            logger.info("Ingestion pipeline closed")
        except Exception as e:
            logger.error(f"Error closing ingestion pipeline: {e}")
