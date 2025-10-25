from typing import TypedDict, List, Dict, Any


class RAGState(TypedDict):
    user_query: str
    collection_name: str
    security_status: str
    processed_query: str
    search_type: str
    search_results: List[Dict[str, Any]]
    evaluation_result: str
    final_answer: str
    retry_count: int
    chat_history: List[Dict[str, str]]
    session_id: str
