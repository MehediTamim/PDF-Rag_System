import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL_NAME: str = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash')

    OLLAMA_MODEL_NAME: str = os.getenv('OLLAMA_MODEL_NAME', 'llama3.2:latest')
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_TIMEOUT: int = int(os.getenv('OLLAMA_TIMEOUT', '300'))

    WEAVIATE_HOST: str = os.getenv('WEAVIATE_HOST', 'localhost')
    WEAVIATE_PORT: int = int(os.getenv('WEAVIATE_PORT', '8080'))
    WEAVIATE_GRPC_PORT: int = int(os.getenv('WEAVIATE_GRPC_PORT', '50051'))

    EMBEDDING_MODEL_NAME: str = os.getenv('EMBEDDING_MODEL_NAME', 'BAAI/bge-m3')

    PDF_DPI: int = int(os.getenv('PDF_DPI', '200'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '10'))

    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))


settings = Settings()
