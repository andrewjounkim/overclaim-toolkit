"""Turn a `claude -p --output-format stream-json` log into a short readable transcript.

usage: python render_transcript.py session.jsonl > session.md
Tool calls are kept (that is the evidence); long tool results are trimmed.
"""
import json
import sys

LIMIT = 600

for line in open(sys.argv[1]):
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        print(f"**session** model={ev.get('model')} mcp={[s['name'] + ':' + s['status'] for s in ev.get('mcp_servers', [])]}\n")
    msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
    for c in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
        if c.get("type") == "text" and ev["type"] == "assistant":
            print(f"**assistant:** {c['text']}\n")
        elif c.get("type") == "tool_use":
            print(f"**tool call → `{c['name']}`** `{json.dumps(c['input'])[:LIMIT]}`\n")
        elif c.get("type") == "tool_result":
            body = c.get("content")
            if isinstance(body, list):
                body = " ".join(b.get("text", "") for b in body)
            body = str(body)
            more = f" … [{len(body) - LIMIT} more chars trimmed]" if len(body) > LIMIT else ""
            print("<details><summary>tool result</summary>\n\n```\n" + body[:LIMIT] + more + "\n```\n</details>\n")
    if ev.get("type") == "result":
        print(f"**result:** {ev.get('subtype')}, {ev.get('num_turns')} turns, ${ev.get('total_cost_usd', 0):.2f}")
