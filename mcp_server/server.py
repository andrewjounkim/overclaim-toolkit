"""MCP server exposing one tool: search_my_projects.

Runs over stdio. Never print() to stdout here; stdout is the MCP protocol
channel, so anything stray corrupts it. Log to stderr instead.
"""

from pathlib import Path

import chromadb
from mcp.server.mcpserver import MCPServer

INDEX_DIR = Path(__file__).parent / "index"

# Picked from measured distances (see README): real matches scored 0.97-1.30,
# off-topic queries ("cookie recipe", "stock market") never came in under 1.49.
STRONG = 1.1
UNRELATED = 1.4

mcp = MCPServer("my-projects")
collection = chromadb.PersistentClient(path=str(INDEX_DIR)).get_collection("projects")


@mcp.tool()
def search_my_projects(query: str, project: str = "", n_results: int = 5) -> str:
    """Semantic search over my own past class projects (READMEs, prompt logs,
    specs, and source code) on this machine. Returns the closest passages, each
    with project, file:line, and a match strength.

    Use this to find how I handled something before: the disclaimer wording I
    used, how I labeled an unvalidated model, what I did when an API call
    failed, a rule I gave the AI, or a bug I already fixed. Search by meaning,
    not exact words.

    Ask about ONE concern per call. "disclaimer that a pick is not betting
    advice" finds the right passage; the same idea mixed with two other topics
    in one query returns vague, unrelated matches. Make several calls instead.

    query: what you are looking for, in plain English, one concern.
    project: optional folder name to search only one project (e.g. "DiagKnows").
    n_results: how many passages to return (1-10).

    Results marked "probably unrelated" mean nothing relevant was found;
    do not present them as evidence.
    """
    where = {"project": project} if project else None
    res = collection.query(query_texts=[query], n_results=max(1, min(n_results, 10)), where=where)
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        strength = ("strong" if dist < STRONG else
                    "possible" if dist < UNRELATED else "probably unrelated")
        out.append(f"## {meta['project']}/{meta['file']}:{meta['line']}  ({strength}, distance {dist:.2f})\n"
                   f"Full path: {meta['path']}\n\n{doc[:1200]}\n")
    return "\n".join(out) or f"No passages found (project filter: {project or 'none'})."


if __name__ == "__main__":
    mcp.run()
