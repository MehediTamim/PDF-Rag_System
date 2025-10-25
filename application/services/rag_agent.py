from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from domain.models.state import RAGState
from config.rag_prompts import (
    SECURITY_CHECK_PROMPT,
    QUERY_PROCESSOR_PROMPT,
    ANSWER_GENERATOR_PROMPT,
    SecurityCheckResponse,
    QueryProcessorResponse
)
from domain.services.rag_tools import RAGTools
from config.settings import settings
from utils.logger import Logger

logger = Logger.get_logger('rag_agent')


class RAGAgent:

    def __init__(self, collection_name: str):
        try:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL_NAME,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0,
                timeout=settings.OLLAMA_TIMEOUT,
            )

            self.tools = RAGTools()
            self.collection_name = collection_name
            self.graph = self._build_graph()

            logger.info(f"RAG agent initialized for collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize RAG agent: {e}")
            raise

    def query_processor(self, state: RAGState) -> RAGState:
        try:
            user_query = state['user_query']

            security_llm = self.llm.with_structured_output(SecurityCheckResponse)
            security_prompt = ChatPromptTemplate.from_template(SECURITY_CHECK_PROMPT)
            security_chain = security_prompt | security_llm
            security_data = security_chain.invoke({"query": user_query})

            if security_data.security_status == 'security_issue':
                state['security_status'] = 'security_issue'
                state['final_answer'] = "Sorry, I cannot process this query due to security concerns."
                logger.warning(f"Security issue detected in query: {user_query}")
                return state

            state['security_status'] = 'safe'

            processor_llm = self.llm.with_structured_output(QueryProcessorResponse)
            processor_prompt = ChatPromptTemplate.from_template(QUERY_PROCESSOR_PROMPT)
            processor_chain = processor_prompt | processor_llm
            processor_data = processor_chain.invoke({"query": user_query})

            state['processed_query'] = processor_data.processed_query
            state['search_type'] = 'semantic' if state['retry_count'] == 0 else 'hybrid'

            logger.debug(f"Query processed: {state['processed_query']}")
            return state

        except Exception as e:
            logger.error(f"Error in query_processor: {e}")
            state['security_status'] = 'error'
            state['final_answer'] = "Error processing your query. Please try again."
            return state

    def search_tool(self, state: RAGState) -> RAGState:
        try:
            query = state['processed_query']
            search_type = state['search_type']

            if search_type == 'semantic':
                results = self.tools.semantic_search(self.collection_name, query, limit=5)
            else:
                results = self.tools.hybrid_search(self.collection_name, query, limit=5)

            state['search_results'] = results

            if not results and state['retry_count'] == 0:
                state['retry_count'] = 1
                state['search_type'] = 'hybrid'
                logger.info("No semantic results, retrying with hybrid search")

            logger.debug(f"Search completed: {len(results)} results ({search_type})")
            return state

        except Exception as e:
            logger.error(f"Error in search_tool: {e}")
            state['search_results'] = []
            return state

    def answer_generator(self, state: RAGState) -> RAGState:
        try:
            user_query = state['user_query']
            results = state['search_results']
            chat_history = state.get('chat_history', [])

            if not results:
                state['final_answer'] = "Sorry, I couldn't find relevant information to answer your question."
                logger.warning("No search results to generate answer from")
                return state

            results_text = "\n".join([f"Page {r['page']}: {r['content']}" for r in results])

            history_text = ""
            if chat_history:
                recent_history = chat_history[-2:] if len(chat_history) >= 2 else chat_history
                for msg in recent_history:
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    history_text += f"{role}: {msg['content']}\n"

            if not history_text:
                history_text = "No previous conversation"

            answer_prompt = ChatPromptTemplate.from_template(ANSWER_GENERATOR_PROMPT)
            answer_chain = answer_prompt | self.llm

            full_answer = ""
            for chunk in answer_chain.stream({
                "query": user_query,
                "results": results_text,
                "chat_history": history_text
            }):
                content = chunk.content
                full_answer += content

            state['final_answer'] = full_answer.strip()

            new_chat_history = chat_history.copy()
            new_chat_history.append({"role": "user", "content": user_query})
            new_chat_history.append({"role": "assistant", "content": full_answer.strip()})
            state['chat_history'] = new_chat_history[-2:]

            logger.info("Answer generated successfully")
            return state

        except Exception as e:
            logger.error(f"Error in answer_generator: {e}")
            state['final_answer'] = "Error generating answer. Please try again."
            return state

    def route_after_query_processor(self, state: RAGState) -> str:
        try:
            if state['security_status'] == 'security_issue':
                return 'end'
            return 'search_tool'
        except Exception as e:
            logger.error(f"Error in route_after_query_processor: {e}")
            return 'end'

    def route_after_search(self, state: RAGState) -> str:
        try:
            if not state['search_results'] and state['retry_count'] == 0:
                return 'search_tool'
            return 'answer_generator'
        except Exception as e:
            logger.error(f"Error in route_after_search: {e}")
            return 'answer_generator'

    def _build_graph(self):
        try:
            workflow = StateGraph(RAGState)

            workflow.add_node("query_processor", self.query_processor)
            workflow.add_node("search_tool", self.search_tool)
            workflow.add_node("answer_generator", self.answer_generator)

            workflow.set_entry_point("query_processor")

            workflow.add_conditional_edges(
                "query_processor",
                self.route_after_query_processor,
                {
                    "search_tool": "search_tool",
                    "end": END
                }
            )

            workflow.add_conditional_edges(
                "search_tool",
                self.route_after_search,
                {
                    "search_tool": "search_tool",
                    "answer_generator": "answer_generator"
                }
            )

            workflow.add_edge("answer_generator", END)

            logger.debug("RAG graph built successfully")
            return workflow.compile()

        except Exception as e:
            logger.error(f"Error building graph: {e}")
            raise

    def query(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            if chat_history is None:
                chat_history = []

            initial_state = {
                'user_query': user_query,
                'collection_name': self.collection_name,
                'security_status': '',
                'processed_query': '',
                'search_type': 'semantic',
                'search_results': [],
                'evaluation_result': '',
                'final_answer': '',
                'retry_count': 0,
                'chat_history': chat_history[-2:],
                'session_id': ''
            }

            result = self.graph.invoke(initial_state)
            logger.info(f"Query completed: {user_query[:50]}...")
            return {
                'answer': result['final_answer'],
                'chat_history': result.get('chat_history', [])
            }

        except Exception as e:
            logger.error(f"Error in query: {e}")
            return {
                'answer': "Error processing query. Please try again.",
                'chat_history': chat_history
            }

    def stream_query(self, user_query: str, chat_history: List[Dict[str, str]] = None):
        try:
            if chat_history is None:
                chat_history = []

            initial_state = {
                'user_query': user_query,
                'collection_name': self.collection_name,
                'security_status': '',
                'processed_query': '',
                'search_type': 'semantic',
                'search_results': [],
                'evaluation_result': '',
                'final_answer': '',
                'retry_count': 0,
                'chat_history': chat_history[-2:],
                'session_id': ''
            }

            for event in self.graph.stream(initial_state):
                node_name = list(event.keys())[0]
                node_state = event[node_name]
                yield node_name, node_state

            logger.info(f"Stream query completed: {user_query[:50]}...")

        except Exception as e:
            logger.error(f"Error in stream_query: {e}")
            yield "error", {"final_answer": "Error processing query. Please try again."}

    def close(self):
        try:
            self.tools.close()
            logger.info("RAG agent closed")
        except Exception as e:
            logger.error(f"Error closing RAG agent: {e}")
