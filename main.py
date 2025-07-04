from fastapi import FastAPI, Query
from es_utils import search_by_text

app = FastAPI()

@app.get("/search")
def search(q: str = Query(..., min_length=3), k: int = 5):
    results = search_by_text(q, top_k=k)
    # Exclude the embedding field from results
    return {"results": [{k: v for k, v in result.items() if k != "embedding"} for result in results]}
