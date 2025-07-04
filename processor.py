import ast
import os
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_chunks_from_file(file_path: Path) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = max(
                [child.lineno for child in ast.walk(node) if hasattr(child, "lineno")],
                default=start_line
            )
            code = "\n".join(source.splitlines()[start_line:end_line])
            chunks.append({
                "name": getattr(node, "name", "<unknown>"),
                "type": type(node).__name__,
                "code": code,
                "start_line": start_line + 1,
                "end_line": end_line
            })

    return chunks

def embed_chunks(chunks: List[Dict], file_path: str, repo_name: str) -> List[Dict]:
    texts = [chunk["code"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]
        chunk["file_path"] = file_path
        chunk["repo"] = repo_name

    return chunks
