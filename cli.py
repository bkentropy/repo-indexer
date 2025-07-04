import typer
from pathlib import Path
import shutil
from git import Repo
from processor import extract_chunks_from_file, embed_chunks
from es_utils import ensure_index, index_chunks

app = typer.Typer()

@app.command()
def echo(message: str):
    """
    Echoes the provided message to the console.
    """
    print(message)

@app.command()
def index_repo(github_url: str):
    print("HEY")
    repo_name = github_url.split("/")[-1].removesuffix(".git")
    tmp_dir = Path("/tmp") / repo_name

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    Repo.clone_from(github_url, tmp_dir)

    ensure_index()

    for py_file in tmp_dir.rglob("*.py"):
        chunks = extract_chunks_from_file(py_file)
        embedded = embed_chunks(chunks, str(py_file.relative_to(tmp_dir)), repo_name)
        index_chunks(embedded)

    print(f"Indexed repo: {repo_name}")

if __name__ == "__main__":
    app()
