from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union
import uvicorn

# Import the model cache and create the FastAPI app
from embedding_model import ModelCache

app = FastAPI(
    title="Embedding Service",
    description="A standalone service for generating text embeddings using Sentence Transformers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model cache
model_cache = ModelCache()

class EmbeddingRequest(BaseModel):
    texts: Union[str, List[str]]

@app.post("/embed")
async def get_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for the provided text or list of texts.
    """
    try:
        if isinstance(request.texts, str):
            embeddings = model_cache.encode([request.texts])
            return {"embeddings": embeddings.tolist()}
        else:
            embeddings = model_cache.encode(request.texts)
            return {"embeddings": embeddings.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False  # Disable reload to keep model in memory
    )
