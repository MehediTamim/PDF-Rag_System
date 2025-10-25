import streamlit as st
import uuid
from pathlib import Path
import tempfile
import time

from application.services.ingestion_service import IngestionPipeline
from application.services.rag_agent import RAGAgent
from infrastructure.database.weaviate_client import WeaviateRAG
from config.settings import settings
from utils.logger import Logger

logger = Logger.get_logger('streamlit_app')

st.set_page_config(
    page_title="RAG Chat System",
    page_icon="📚",
    layout="wide"
)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Bengali:wght@400;500;600&display=swap');

:root{
  --bg:#0c0f1a; --panel:#121628; --panel2:#171c32; --muted:#a9b2c7;
  --primary:#7c6cff; --primary-2:#5b8cff; --accent:#2dd4bf;
}
html, body, [class*="css"] { font-family: Inter,'Noto Sans Bengali',system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; }
.stApp { background: radial-gradient(90% 160% at 0% 0%, #11162c 0%, #0b0e19 55%) fixed; }
.block-container { padding-top: 1rem; }

/* Sidebar */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg, #10152a 0%, #0e1224 100%);
  border-right: 1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] .stButton>button{
  border-radius: 10px; font-weight: 600;
}

/* Processing pills */
.processing-state{
  font-size:.9rem; color:#8ab4ff; background:rgba(138,180,255,.08);
  border:1px solid rgba(138,180,255,.18); padding:.5rem .6rem; border-radius:10px;
}

/* Chat input */
div[data-testid="stChatInput"] textarea{
  background: var(--panel); color:#e8ecf6; border-radius:12px !important;
  border:1px solid rgba(255,255,255,.10) !important;
}
div[data-testid="stChatInput"] textarea:focus{
  border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(124,108,255,.25) !important;
}

/* Primary buttons */
.stButton>button{
  background: linear-gradient(135deg, var(--primary), var(--primary-2));
  color:#fff; border:0; border-radius:12px; font-weight:600; padding:.55rem .9rem;
  box-shadow: 0 10px 30px rgba(124,108,255,.28);
}
.stButton>button:hover{ filter:brightness(1.06); transform: translateY(-1px); }

/* Slim scrollbars */
*::-webkit-scrollbar{ width:10px; height:10px }
*::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.14); border-radius:10px }
*::-webkit-scrollbar-thumb:hover{ background:rgba(255,255,255,.24) }
</style>
""", unsafe_allow_html=True)

# Gradient header (ChatGPT/Grok-like)
# st.markdown("""
# <div style="display:flex;align-items:center;gap:.85rem;margin:.2rem 0 1rem 0;">
#   <div style="font-size:1.9rem">💬</div>
#   <div>
#     <div style="font-size:1.55rem;font-weight:800;
#       background:linear-gradient(90deg,#cfd2ff,#7c6cff,#2dd4bf);
#       -webkit-background-clip:text;background-clip:text;color:transparent;">
#       RAG Chat System
#     </div>
#     <div style="font-size:.9rem;color:#a9b2c7">ChatGPT‑style interface · clean dark theme</div>
#   </div>
#   </div>
# """, unsafe_allow_html=True)

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_collection_name" not in st.session_state:
    st.session_state.current_collection_name = None

if "current_pdf_name" not in st.session_state:
    st.session_state.current_pdf_name = None

if "uploading" not in st.session_state:
    st.session_state.uploading = False

if "rag_agent" not in st.session_state:
    st.session_state.rag_agent = None

if "ingestion_pipeline" not in st.session_state:
    st.session_state.ingestion_pipeline = None

if "weaviate_client" not in st.session_state:
    try:
        st.session_state.weaviate_client = WeaviateRAG()
        logger.info("Weaviate client initialized in Streamlit")
    except Exception as e:
        st.error(f"Failed to connect to Weaviate: {e}")
        logger.error(f"Failed to initialize Weaviate in Streamlit: {e}")
        st.session_state.weaviate_client = None

if "available_collections" not in st.session_state:
    st.session_state.available_collections = []
    if st.session_state.weaviate_client:
        try:
            collections = st.session_state.weaviate_client.list_all_collections()
            if collections:
                st.session_state.available_collections = collections
                logger.info(f"Loaded {len(collections)} collections")
        except Exception as e:
            logger.error(f"Error loading collections: {e}")

if "collection_metadata" not in st.session_state:
    st.session_state.collection_metadata = {}

with st.sidebar:
    st.title("📚 PDF Upload")

    if st.session_state.current_collection_name:
        display_name = st.session_state.collection_metadata.get(
            st.session_state.current_collection_name,
            st.session_state.current_collection_name
        )
        st.success(f"📄 Active: {display_name}")

        if st.session_state.weaviate_client:
            try:
                count = st.session_state.weaviate_client.get_collection_object_count(
                    st.session_state.current_collection_name
                )
                if count is not None:
                    st.info(f"📊 Documents: {count}")
            except Exception as e:
                logger.error(f"Error getting document count: {e}")

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        disabled=st.session_state.uploading
    )

    if uploaded_file:
        if st.button("Process PDF", disabled=st.session_state.uploading, use_container_width=True):
            st.session_state.uploading = True
            st.rerun()

    if st.session_state.uploading and uploaded_file:
        with st.spinner("🔄 Processing PDF..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                collection_uuid = str(uuid.uuid4()).replace('-', '_')
                collection_name = f"pdf_{collection_uuid}"

                status_text.text("Step 1/4: Saving PDF...")
                progress_bar.progress(25)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                status_text.text("Step 2/4: Initializing pipeline...")
                progress_bar.progress(40)

                if st.session_state.ingestion_pipeline is None:
                    st.session_state.ingestion_pipeline = IngestionPipeline(use_chunking=True)

                status_text.text("Step 3/4: Extracting and chunking...")
                progress_bar.progress(50)

                original_name = uploaded_file.name

                actual_collection = st.session_state.ingestion_pipeline.ingest_pdf(
                    tmp_path,
                    max_workers=4,
                    collection_name=collection_name
                )

                status_text.text("Step 4/4: Initializing RAG agent...")
                progress_bar.progress(90)

                if st.session_state.rag_agent:
                    st.session_state.rag_agent.close()

                st.session_state.rag_agent = RAGAgent(collection_name=actual_collection)

                st.session_state.current_collection_name = actual_collection
                st.session_state.current_pdf_name = original_name

                st.session_state.collection_metadata[actual_collection] = original_name

                if actual_collection not in st.session_state.available_collections:
                    st.session_state.available_collections.append(actual_collection)

                if actual_collection not in st.session_state.conversations:
                    st.session_state.conversations[actual_collection] = []

                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")

                Path(tmp_path).unlink()

                time.sleep(1)
                st.session_state.uploading = False
                st.success("PDF processed successfully!")
                logger.info(f"PDF uploaded and processed: {original_name}")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                logger.error(f"Error in PDF upload: {e}")
                st.session_state.uploading = False
                st.rerun()

    st.markdown("---")

    if st.session_state.available_collections:
        st.subheader("📝 All Collections")

        if st.button("🔄 Refresh Collections", use_container_width=True):
            if st.session_state.weaviate_client:
                try:
                    collections = st.session_state.weaviate_client.list_all_collections()
                    if collections:
                        st.session_state.available_collections = collections
                        logger.info("Collections refreshed")
                        st.rerun()
                except Exception as e:
                    logger.error(f"Error refreshing collections: {e}")

        st.markdown("---")

        for collection_name in st.session_state.available_collections:
            display_name = st.session_state.collection_metadata.get(
                collection_name,
                collection_name
            )

            msg_count = len(st.session_state.conversations.get(collection_name, [])) // 2

            doc_count = ""
            if st.session_state.weaviate_client:
                try:
                    count = st.session_state.weaviate_client.get_collection_object_count(collection_name)
                    if count is not None:
                        doc_count = f" • {count} docs"
                except Exception as e:
                    logger.error(f"Error getting doc count for {collection_name}: {e}")

            button_type = "primary" if collection_name == st.session_state.current_collection_name else "secondary"

            if st.button(
                f"📄 {display_name}\n{msg_count} msgs{doc_count}",
                key=f"thread_{collection_name}",
                use_container_width=True,
                type=button_type
            ):
                try:
                    st.session_state.current_collection_name = collection_name
                    st.session_state.current_pdf_name = display_name

                    if collection_name not in st.session_state.conversations:
                        st.session_state.conversations[collection_name] = []

                    if st.session_state.rag_agent:
                        st.session_state.rag_agent.close()

                    st.session_state.rag_agent = RAGAgent(collection_name=collection_name)
                    logger.info(f"Switched to collection: {collection_name}")

                    st.rerun()
                except Exception as e:
                    st.error(f"Error switching collection: {e}")
                    logger.error(f"Error switching to collection {collection_name}: {e}")
    else:
        st.info("No collections found. Upload a PDF to get started!")

st.title("💬 RAG Chat System")

if st.session_state.current_collection_name is None:
    st.info("👈 Please upload a PDF or select a collection from the sidebar to start chatting.")
else:
    current_conv = st.session_state.conversations.get(st.session_state.current_collection_name, [])

    chat_container = st.container()
    with chat_container:
        for message in current_conv:
            role = message["role"]
            content = message["content"]

            if role == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)

    user_query = st.chat_input("Ask a question about the PDF...", disabled=st.session_state.uploading)

    if user_query:
        current_conv.append({"role": "user", "content": user_query})
        st.session_state.conversations[st.session_state.current_collection_name] = current_conv

        with st.container():
            state_placeholder = st.empty()
            node_placeholder = st.empty()
            answer_placeholder = st.empty()

            try:
                chat_history = current_conv[-2:] if len(current_conv) >= 2 else current_conv

                if chat_history:
                    st.info(f"💬 Using chat context: {len(chat_history)} previous message(s)")

                full_answer = ""

                for node_name, node_state in st.session_state.rag_agent.stream_query(user_query, chat_history=chat_history):
                    if node_name == "query_processor":
                        state_placeholder.markdown('<div class="processing-state">🔄 Processing Query...</div>', unsafe_allow_html=True)

                        security_status = node_state.get('security_status', 'checking...')
                        processed_query = node_state.get('processed_query', 'processing...')

                        node_info = f"""
                        <div class="agent-node">
                        📌 <b>Node:</b> query_processor<br>
                        🔒 <b>Security Status:</b> {security_status}<br>
                        📝 <b>Processed Query:</b> {processed_query}
                        </div>
                        """
                        node_placeholder.markdown(node_info, unsafe_allow_html=True)

                    elif node_name == "search_tool":
                        state_placeholder.markdown('<div class="processing-state">🔎 Searching Documents...</div>', unsafe_allow_html=True)

                        search_type = node_state.get('search_type', 'unknown')
                        results = node_state.get('search_results', [])
                        retry_count = node_state.get('retry_count', 0)

                        node_info = f"""
                        <div class="agent-node">
                        📌 <b>Node:</b> search_tool<br>
                        🔍 <b>Search Type:</b> {search_type}<br>
                        📊 <b>Results Found:</b> {len(results)}<br>
                        🔄 <b>Retry Count:</b> {retry_count}
                        </div>
                        """
                        node_placeholder.markdown(node_info, unsafe_allow_html=True)

                    elif node_name == "answer_generator":
                        state_placeholder.markdown('<div class="processing-state">✨ Generating Answer...</div>', unsafe_allow_html=True)

                        node_info = f"""
                        <div class="agent-node">
                        📌 <b>Node:</b> answer_generator<br>
                        ⏳ <b>Status:</b> Streaming response...
                        </div>
                        """
                        node_placeholder.markdown(node_info, unsafe_allow_html=True)

                        full_answer = node_state.get('final_answer', '')

                state_placeholder.empty()
                node_placeholder.empty()

                assistant_box = st.chat_message("assistant", avatar="🤖")
                stream_placeholder = assistant_box.empty()

                displayed = ""
                for char in full_answer:
                    displayed += char
                    stream_placeholder.markdown(displayed + "▌")
                    time.sleep(0.01)

                stream_placeholder.markdown(full_answer)

                current_conv.append({"role": "assistant", "content": full_answer})
                st.session_state.conversations[st.session_state.current_collection_name] = current_conv

                logger.info(f"Query answered successfully for collection: {st.session_state.current_collection_name}")

            except Exception as e:
                state_placeholder.empty()
                node_placeholder.empty()
                st.error(f"Error generating response: {str(e)}")
                logger.error(f"Error in query processing: {e}")
                current_conv.append({"role": "assistant", "content": f"Error: {str(e)}"})
                st.session_state.conversations[st.session_state.current_collection_name] = current_conv

        st.rerun()
