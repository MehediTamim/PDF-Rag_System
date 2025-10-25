# RAG Chat System with PDF Processing

A production-ready RAG (Retrieval-Augmented Generation) chat system built with Domain-Driven Design architecture, featuring PDF document processing, semantic search, and an intelligent chat interface.

## 🏗️ Architecture

This project follows **Domain-Driven Design (DDD)** principles with clean separation of concerns:

```
├── application/          # Application Services (Use Cases)
│   ├── services/
│   │   ├── ingestion_service.py    # PDF ingestion pipeline
│   │   └── rag_agent.py            # RAG agent with LangGraph
│   └── dto/                         # Data Transfer Objects
│
├── domain/              # Business Logic & Domain Models
│   ├── models/
│   │   └── state.py                # RAG state definitions
│   └── services/
│       ├── semantic_chunker.py     # Semantic text chunking
│       └── rag_tools.py            # RAG search tools
│
├── infrastructure/      # External Integrations
│   ├── database/
│   │   └── weaviate_client.py      # Vector database client
│   └── llm/
│       ├── embeddings.py           # Embedding service
│       └── pdf_extractor.py        # PDF extraction with Gemini
│
├── config/              # Configuration & Settings
│   ├── settings.py                 # Environment settings
│   ├── prompts.py                  # PDF extraction prompts
│   └── rag_prompts.py             # RAG system prompts
│
├── presentation/        # UI Layer
│   └── streamlit/
│       └── app.py                  # Streamlit web interface
│
├── utils/               # Utilities
│   └── logger.py                   # Centralized logging system
│
└── logs/                # Application logs (auto-generated)
```

## ✨ Features

- **PDF Processing**: Extract and process PDFs using Google Gemini Vision API
- **Semantic Chunking**: Intelligent text chunking for optimal retrieval
- **Vector Search**: Powered by Weaviate for fast similarity search
- **Hybrid Search**: Combines semantic and keyword search
- **LangGraph Agent**: Multi-step reasoning with query processing and security checks
- **Real-time Chat**: Streamlit-based interactive chat interface
- **Comprehensive Logging**: All operations logged with timestamps and error tracking
- **Exception Handling**: Robust error handling with detailed logging

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose (for Weaviate)
- Ollama (for local LLM inference)
- Google Gemini API Key

## 🚀 Installation

### Step 1: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install PyTorch (CPU version)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and Setup Ollama

#### Install Ollama

Follow the official installation guide: [Ollama installation guide](https://ollama.com/download)

#### Start Ollama Service

In a **separate terminal**, run:

```bash
ollama serve
```

**Keep this terminal running** - Ollama needs to run continuously.

#### Pull the LLM Model

In another terminal (with your virtual environment activated):

```bash
ollama pull llama3.2:3b
```

This downloads the Llama 3.2 3B model (~2GB). You can use other models by changing the model name in `.env` later.

### Step 5: Start Weaviate (Vector Database)

```bash
docker-compose up -d
```

This will start Weaviate on:
- HTTP: `localhost:8081`
- gRPC: `localhost:50051`

### Step 6: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash

# Ollama Configuration
OLLAMA_MODEL_NAME=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=300

# Weaviate Configuration
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8081
WEAVIATE_GRPC_PORT=50051

# Embedding Model
EMBEDDING_MODEL_NAME=BAAI/bge-m3

# PDF Processing
PDF_DPI=200
MAX_WORKERS=10
```

## 🎯 Running the Application

### Start the Application

Simply run:

```bash
python main.py
```

The application will automatically start and be available at: **http://localhost:8501**

Your browser should open automatically. If it doesn't, navigate to the URL manually.

### Alternative Methods

You can also run using Streamlit directly:

```bash
streamlit run main.py
```

or:

```bash
streamlit run presentation/streamlit/app.py --server.port 8501 --server.address localhost
```

## 📖 Usage Guide

### 1. Upload PDF Documents

1. Open the application in your browser
2. Go to the "Upload PDF" tab in the sidebar
3. Upload your PDF file
4. Wait for processing (progress shown in real-time)
5. Your document will be indexed and ready for querying

### 2. Chat with Documents

1. Select a collection from the sidebar
2. Type your question in the chat input
3. The RAG agent will:
   - Check query security
   - Process and optimize your query
   - Search relevant content
   - Generate a comprehensive answer

### 3. View Processing State

The system shows real-time processing state:
- 🔐 Security Check
- 🔍 Query Processing
- 📊 Search Execution
- 💡 Answer Generation

## 🔧 Configuration

### Adjust Ollama Settings

Edit the environment variables in `.env`:

```bash
OLLAMA_CONTEXT_LENGTH=8192
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_KEEP_ALIVE=5m
```

### Change Models

**Ollama Model:**
```bash
ollama pull llama3.2:latest
# Update .env: OLLAMA_MODEL_NAME=llama3.2:latest
```

**Embedding Model:**
Update in `.env`:
```bash
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## 📊 Logging

All operations are logged to the `logs/` directory with the following format:

```
logs/
├── embeddings_YYYYMMDD.log
├── pdf_extractor_YYYYMMDD.log
├── weaviate_client_YYYYMMDD.log
├── ingestion_service_YYYYMMDD.log
├── rag_agent_YYYYMMDD.log
└── streamlit_app_YYYYMMDD.log
```

Each log entry includes:
- Timestamp
- Module name
- Log level (INFO, WARNING, ERROR)
- Detailed message

## 🛠️ Development

### Project Structure Conventions

- **Application Layer**: Contains use cases and orchestrates domain logic
- **Domain Layer**: Core business logic, independent of external systems
- **Infrastructure Layer**: Implementations of external services and databases
- **Presentation Layer**: User interface and API endpoints

### Adding New Features

1. Define domain models in `domain/models/`
2. Implement business logic in `domain/services/`
3. Create use cases in `application/services/`
4. Add UI components in `presentation/streamlit/`

### Error Handling

All critical operations include try-except blocks with logging:

```python
try:
    result = perform_operation()
    logger.info("Operation successful")
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise
```

## 🐛 Troubleshooting

### Issue: Ollama Connection Error

**Solution:**
```bash
# Ensure Ollama is running
ollama serve

# Check if model is available
ollama list

# Pull model if missing
ollama pull llama3.2:3b
```

### Issue: Weaviate Connection Error

**Solution:**
```bash
# Check if Weaviate is running
docker ps | grep weaviate

# Restart Weaviate
docker-compose down
docker-compose up -d
```

### Issue: Gemini API Error

**Solution:**
- Verify your API key in `.env`
- Check API quota at: https://makersuite.google.com/
- Ensure `GEMINI_API_KEY` is set correctly

### Issue: Import Errors

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 📦 Dependencies

### Core Libraries

- **LangChain**: LLM orchestration framework
- **LangGraph**: State management for LLM workflows
- **Streamlit**: Web interface
- **Weaviate**: Vector database
- **Sentence Transformers**: Text embeddings
- **Google Generative AI**: PDF extraction with vision
- **pdf2image**: PDF to image conversion

### Full Dependencies

See `requirements.txt` for complete list.

## 🔒 Security

- Query security checks before processing
- Input validation and sanitization
- Environment-based configuration
- No hardcoded credentials

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow DDD principles
4. Add comprehensive logging
5. Write tests for new features
6. Submit a pull request

## 📧 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review error messages in the Streamlit interface
- Ensure all services (Ollama, Weaviate) are running

## 🎓 Additional Notes

### Why DDD Architecture?

- **Maintainability**: Clear separation of concerns
- **Testability**: Easy to unit test domain logic
- **Scalability**: Can swap implementations without affecting core logic
- **Clarity**: Easy to understand project structure

### Performance Tips

1. **Adjust chunk size** in `domain/services/semantic_chunker.py`
2. **Increase workers** in `.env`: `MAX_WORKERS=20`
3. **Use GPU** for embeddings (change PyTorch installation)
4. **Optimize Ollama** parameters for your hardware

---

**Built with ❤️ using DDD principles and modern RAG techniques**

