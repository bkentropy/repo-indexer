from fastapi import FastAPI, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from es_utils import search_by_text
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/search")
async def search(q: str = Query(..., min_length=3), k: int = 5):
    results = search_by_text(q, top_k=k)
    # Exclude the embedding field and prepare results
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]
    return templates.TemplateResponse(
        "search_results.html",
        {"request": {}, "query": q, "results": formatted_results}
    )

@app.get("/")
async def root():
    return {"status": datetime.now().isoformat()}