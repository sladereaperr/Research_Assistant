import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import uuid

class MemoryManager:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=False
        ))
        self.collection = self.client.create_collection(
            name="research_memory",
            metadata={"hnsw:space": "cosine"}
        )
        self.summary_memory = []
    
    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Add a memory to vector store"""
        doc_id = str(uuid.uuid4())
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        
        # Also add to summary memory
        self.summary_memory.append({
            "text": text,
            "metadata": metadata
        })
    
    def search_memory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search memories"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        memories = []
        if results['documents']:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                memories.append({
                    "text": doc,
                    "metadata": metadata
                })
        
        return memories
    
    def get_summary(self) -> List[Dict[str, Any]]:
        """Get all summary memory"""
        return self.summary_memory

# Global memory instance
memory_manager = MemoryManager()