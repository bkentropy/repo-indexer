from fastapi import FastAPI, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from es_utils import search_by_text
from summarizer import summarize_code
from datetime import datetime
import markdown  # Added for markdown to HTML conversion
import ast
import json

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

@app.get("/ast")
async def get_ast():
    try:
        # Query Elasticsearch for all code chunks using search_by_text
        results = search_by_text("", top_k=1000)  # Empty query for match_all
        
        # Process each chunk and create AST
        ast_trees = []
        for hit in results:
            try:
                # Parse the code chunk into AST
                tree = ast.parse(hit["code"])
                
                # Convert AST to JSON
                def ast_to_dict(node):
                    if isinstance(node, ast.AST):
                        result = {"type": node.__class__.__name__}
                        for field in node._fields:
                            value = getattr(node, field)
                            if isinstance(value, (list, tuple)):
                                result[field] = [ast_to_dict(x) for x in value]
                            elif isinstance(value, ast.AST):
                                result[field] = ast_to_dict(value)
                            elif isinstance(value, str):
                                result[field] = value
                            elif isinstance(value, (int, float, bool)):
                                result[field] = str(value)
                            else:
                                result[field] = str(value)
                        return result
                    return str(node)

                # Add metadata to AST tree
                ast_json = ast_to_dict(tree)
                ast_json["metadata"] = {
                    "file_path": hit["file_path"],
                    "start_line": hit["start_line"],
                    "end_line": hit["end_line"],
                    "type": hit["type"]
                }
                ast_trees.append(ast_json)
            except SyntaxError:
                continue  # Skip invalid code chunks
        
        return JSONResponse(ast_trees)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/ast-visualizer")
async def ast_visualizer():
    """Serve the AST visualizer interface."""
    return templates.TemplateResponse(
        "ast_visualizer.html",
        {"request": {}}
    )
