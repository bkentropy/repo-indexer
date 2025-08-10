from embedding_client import EmbeddingClient

# Initialize the client
embedding_client = EmbeddingClient("http://localhost:8001")

# Get embeddings for a single text
embedding = embedding_client.get_embeddings("Your text here")[0]

# Get embeddings for multiple texts
embeddings = embedding_client.get_embeddings(["First text", "Second text"])
print(embeddings)
