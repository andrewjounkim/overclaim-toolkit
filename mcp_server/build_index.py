"""Build the search index over my past projects.

usage: python build_index.py            (re-run any time; it rebuilds from scratch)

Each document is a chunk of one file: a markdown section, or a ~40-line
window of code. Every chunk keeps its project, file path and starting line so
search results can be cited as file:line.
"""

import re
import sys
from pathlib import Path

import chromadb

HERE = Path(__file__).parent
INDEX_DIR = HERE / "index"
PROJECTS_FILE = HERE / "projects.txt"   # one absolute project path per line

TEXT_EXT = {".md", ".py", ".js", ".html", ".toml", ".txt"}
SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", "dist", "build", "chroma_store",
             "data", "__pycache__", "static", "fonts", "public", "images", "sprites"}
MAX_FILE_BYTES = 150_000
CODE_WINDOW = 40


def project_files(root: Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS or part.startswith((".", "dist")) for part in rel.parts[:-1]):
            continue
        if path.is_file() and path.suffix in TEXT_EXT and path.stat().st_size <= MAX_FILE_BYTES:
            yield path


def chunk_markdown(lines):
    """Split at headings so a chunk is one section of a README or log."""
    start = 0
    for i, line in enumerate(lines):
        if i > start and re.match(r"#{1,4} ", line):
            yield start, lines[start:i]
            start = i
    yield start, lines[start:]


def chunk_code(lines):
    for start in range(0, len(lines), CODE_WINDOW):
        yield start, lines[start:start + CODE_WINDOW]


def chunks(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    splitter = chunk_markdown if path.suffix == ".md" else chunk_code
    for start, block in splitter(lines):
        text = "\n".join(block).strip()
        if len(text) >= 40:   # skip blank or near-empty pieces
            # Long sections get cut; the embedding model only reads the first ~256 tokens anyway.
            yield start + 1, text[:2000]


def main():
    roots = [Path(p.strip()).expanduser() for p in PROJECTS_FILE.read_text().splitlines()
             if p.strip() and not p.startswith("#")]
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    if "projects" in [c.name for c in client.list_collections()]:
        client.delete_collection("projects")
    collection = client.create_collection("projects")

    ids, docs, metas = [], [], []
    for root in roots:
        if not root.is_dir():
            print(f"skipping missing project {root}", file=sys.stderr)
            continue
        for path in project_files(root):
            rel = str(path.relative_to(root))
            for line, text in chunks(path):
                ids.append(f"{root.name}:{rel}:{line}")
                docs.append(text)
                metas.append({"project": root.name, "path": str(path), "file": rel, "line": line})
    for i in range(0, len(ids), 200):
        collection.add(ids=ids[i:i + 200], documents=docs[i:i + 200], metadatas=metas[i:i + 200])
    print(f"indexed {len(ids)} chunks from {len(roots)} projects into {INDEX_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
