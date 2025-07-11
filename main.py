from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from es_utils import search_by_text
from summarizer import summarize_code, summarize_code_stream
from datetime import datetime
import markdown  # Added for markdown to HTML conversion
import ast
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/summarizer")
async def websocket_summarizer(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for the query from the client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "summarize":
                query = message.get("query", "")
                k = message.get("k", 3)

                # Get search results
                results = search_by_text(query, top_k=k)
                formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

                # Send initial status
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "query": query,
                    "results_count": len(formatted_results)
                }))

                # Stream the summary
                async for chunk in summarize_code_stream(formatted_results, query):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk
                    }))

                # Send completion
                await websocket.send_text(json.dumps({
                    "type": "complete"
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search")
async def search(q: str = Query(..., min_length=3), k: int = 3):
    # Get search results
    results = search_by_text(q, top_k=k)
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

    return templates.TemplateResponse(
        "search_results.html",
        {"request": {}, "query": q, "results": formatted_results}
    )

@app.get("/summarizer")
async def summarizer(q: str = Query(..., min_length=3), k: int = 3):
    # Get search results
    results = search_by_text(q, top_k=k)
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

    # Get summary of top 3 results
    summary = summarize_code(formatted_results, q)
    summary_html = markdown.markdown(summary, extensions=['fenced_code', 'codehilite']) if summary else ""  # Convert markdown to HTML with extensions

    return templates.TemplateResponse(
        "search_results.html",
        {"request": {}, "query": q, "results": formatted_results, "summary": summary_html}
    )

@app.get("/summarizer/stream")
async def summarizer_stream(q: str = Query(..., min_length=3), k: int = 3):
    """Stream the summarization process using Server-Sent Events."""

    async def generate_summary():
        # Get search results
        results = search_by_text(q, top_k=k)
        formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

        # Send initial data
        yield f"data: {json.dumps({'type': 'start', 'query': q, 'results_count': len(formatted_results)})}\n\n"

        # Stream the summary
        async for chunk in summarize_code_stream(formatted_results, q):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(
        generate_summary(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/summarizer/streaming-ui")
async def summarizer_streaming_ui(q: str = Query(..., min_length=3), k: int = 3):
    """Serve the streaming UI template."""
    # Get search results for display
    results = search_by_text(q, top_k=k)
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

    return templates.TemplateResponse(
        "search_results_streaming.html",
        {"request": {}, "query": q, "results": formatted_results}
    )

@app.get("/summarizer/websocket-ui")
async def summarizer_websocket_ui(q: str = Query("", min_length=0), k: int = 3):
    """Serve the WebSocket streaming UI template."""
    # Get search results for display if query is provided
    results = []
    if q:
        results = search_by_text(q, top_k=k)
    formatted_results = [{k: v for k, v in result.items() if k != "embedding"} for result in results]

    return templates.TemplateResponse(
        "search_results_websocket.html",
        {"request": {}, "query": q, "results": formatted_results}
    )

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
    return templates.TemplateResponse("ast_visualizer.html", {"request": {}})
