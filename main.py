from fastapi import FastAPI, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from es_utils import search_by_text
from summarizer import summarize_code
from datetime import datetime
import markdown  # Added for markdown to HTML conversion

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/search")
async def search(q: str = Query(..., min_length=3), k: int = 5):
    # Get search results
    results = search_by_text(q, top_k=k)
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]
    
    # Get summary of top 3 results
    summary = summarize_code(formatted_results, q)
    summary_html = markdown.markdown(summary) if summary else ""  # Convert markdown to HTML
    
    return templates.TemplateResponse(
        "search_results.html",
        {"request": {}, "query": q, "results": formatted_results, "summary": summary_html}
    )

@app.get("/")
async def root():
    return {"status": datetime.now().isoformat()}