from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from embedding_model import ModelCache
import uvicorn
from typing import List, Union

app = FastAPI(title="Embedding Service",
              description="A standalone service for generating embeddings")

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
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("embedding_service:app", 
                host="0.0.0.0", 
                port=8001,  # Different port from your main FastAPI app
                reload=False)  # Disable reload to keep model in memory
