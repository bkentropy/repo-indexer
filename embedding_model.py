from sentence_transformers import SentenceTransformer
import threading

class ModelCache:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelCache, cls).__new__(cls)
                    cls._instance.model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance
    
    def encode(self, query):
        return ModelCache._instance.model.encode(query)