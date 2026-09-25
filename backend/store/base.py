from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseStore(ABC):
    @abstractmethod
    def add_document(self, doc_id: str, filename: str, file_type: str, status: str, file_path: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_documents(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def search_chunks(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        pass

    @abstractmethod
    def query_metrics(self, mine: Optional[str] = None, subsidiary: Optional[str] = None, 
                      parameter: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_topics(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_conflicts(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_conflict(self, conflict: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def update_conflict_status(
        self,
        status: str,
        conflict_id: Optional[int] = None,
        mine: Optional[str] = None,
        year: Optional[str] = None,
        parameter: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass
