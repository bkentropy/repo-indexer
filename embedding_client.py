import requests
from typing import List, Union

class EmbeddingClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        
    def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Get embeddings for one or more texts.
        
        Args:
            texts: A single string or a list of strings to get embeddings for
            
        Returns:
            A list of embedding vectors (each vector is a list of floats)
        """
        if isinstance(texts, str):
            texts = [texts]
            
        response = requests.post(
            f"{self.base_url}/embed",
            json={"texts": texts}
        )
        response.raise_for_status()
        return response.json()["embeddings"]
    
    def health_check(self) -> bool:
        """Check if the embedding service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
