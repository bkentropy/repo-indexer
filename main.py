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
async def get_ast(code: str):
    try:
        # Parse the code into AST
        tree = ast.parse(code)
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
                        result[field] = value  # Don't add quotes to string values
                    elif isinstance(value, (int, float, bool)):
                        result[field] = str(value)
                    else:
                        result[field] = str(value)
                return result
            return str(node)

        # Special handling for simple expressions
        if isinstance(tree, ast.Module) and len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            expr = tree.body[0].value
            if isinstance(expr, ast.Name):
                return {"type": "Name", "id": expr.id}
            elif isinstance(expr, ast.Str):
                return {"type": "Str", "s": expr.s}
            elif isinstance(expr, ast.Num):
                return {"type": "Num", "n": expr.n}
            elif isinstance(expr, ast.Constant):
                return {"type": "Constant", "value": expr.value}
            else:
                return ast_to_dict(expr)
        
        ast_json = ast_to_dict(tree)
        return JSONResponse(ast_json)
        
    except SyntaxError:
        return JSONResponse({"error": "Invalid Python code"}, status_code=400)

@app.get("/ast-visualizer")
async def ast_visualizer():
    return templates.TemplateResponse("ast_visualizer.html", {"request": {}})
