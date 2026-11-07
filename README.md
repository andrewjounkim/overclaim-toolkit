> **⚠️ DRAFT WRITTEN BY AI. The course requires the README to be written by me. Rewrite every section in my own words, then delete this line.**

# Overclaim Toolkit

Two tools for coding agents (Claude Code, Codex) that I built for CMU 15-113 HW8, for the kind of app I keep making: ones that show predictions, picks, or health information.

| Piece | Kind | What it does |
|---|---|---|
| [`skills/overclaim-check/`](skills/overclaim-check/SKILL.md) | Skill (a checker) | Reviews a change and reports wording or fallbacks that claim more than the code supports. It never edits. |
| [`mcp_server/`](mcp_server/server.py) → `search_my_projects` | MCP tool (new capability) | Semantic search over my own past projects' READMEs, prompt logs, specs, and code, so an agent can see how I handled the same problem before. |

## The skill: `overclaim-check`

**What it does.** It reads the diff and every user-facing string, then reports each claim the code can't back up. There are five categories: accuracy that was never measured, advice the app can't give, invented data, false certainty, and AI text not grounded in retrieved data. Each finding quotes the claim with `file:line` and explains what the code actually does. If an earlier project of mine dealt with the same problem, it cites that as a precedent. The output format is fixed, so runs can be compared.

**When it triggers.** It triggers when an agent is asked to check, review, or approve a diff, branch, PR, or feature in an app that shows forecasts, picks, rankings, "best" choices, scores, or betting, health, or money information. It also triggers on short requests like "check this before I merge". Version 1's description didn't trigger at all; see [ITERATION.md](ITERATION.md).

**Why I built it (evidence from my prompt logs).** I typed the same rule into almost every project:

> "This is an educational statistical model, not a proven betting system. Do not claim accuracy, profitability, or an advantage over sportsbooks." (HW3, Strikeout Lab, prompt 1)
>
> "Never silently replace failed API calls with invented statistics." (HW3, Strikeout Lab, prompt 1)
>
> "Every result shown to the user should include a short disclaimer that this is an educational tool, not a medical diagnosis." (HW6, DiagKnows, prompt 4)
>
> "…uses an LLM (grounded only in retrieved data, never invented)…" (HW4, PaperTrail, project brief)

The AI still drifted toward the claims I had banned. In Strikeout Lab I asked which pitchers were *"best to bet on"*, and the log notes that a "best bets" ranking *"would claim an advantage nobody has shown."* DiagKnows labeled a weak match as *"high confidence"* until a test caught it.

## The MCP tool: `search_my_projects`

**What it does.** `search_my_projects(query, project="", n_results=5)` returns the closest passages from my past projects. Each passage comes with its project, `file:line`, and a match strength: **strong** (distance < 1.1), **possible** (< 1.4), or **probably unrelated**. The index is a ChromaDB collection with 575 chunks from 8 projects. Markdown files are split by heading, and code into 40-line windows.

**Why I built it.** An agent has no way to know what I did in an earlier project, so I kept pointing at old work by hand or pasting old rules back in:

> "just like strikeout lab can you also put in an image of it" (HW4, PaperTrail, portfolio prompt)
>
> "keep this in mind too for the code Remember, keep API keys and other secrets out of the repo…" (HW3, Strikeout Lab, prompt 8; the same rule shows up again in the PaperTrail brief and the Eye Strain spec)

The agent can't open another repo's history unless I name the exact file, and it has no index of what's in my other projects. This tool gives it that reach.

**How I picked the cutoffs.** I learned this in HW6: vector search always returns *something*. So I ran real queries and nonsense queries and compared the numbers. The best real matches scored 0.97–1.30. "Recipe for chocolate chip cookies", "the stock market closed higher on Tuesday", and "who won the 1998 world cup" never scored better than 1.49.

## Install

You need Python 3.10+ (I tested on 3.14).

```bash
git clone https://github.com/andrewjounkim/overclaim-toolkit ~/overclaim-toolkit
cd ~/overclaim-toolkit
python3 -m venv .venv
./.venv/bin/pip install -r mcp_server/requirements.txt
```

**1. Choose what to index.** Edit `mcp_server/projects.txt`: one absolute path per line. ⚠️ The paths in it are **machine-specific** and point to my computer. Then build the index (the first run downloads a ~79 MB embedding model):

```bash
./.venv/bin/python mcp_server/build_index.py
```

**2. Install the skill.** Copy or symlink the folder:

| Tool | Where the skill goes |
|---|---|
| Claude Code | `~/.claude/skills/overclaim-check/` (all projects) or `<repo>/.claude/skills/overclaim-check/` |
| Codex | `~/.agents/skills/overclaim-check/` (all projects) or `<repo>/.agents/skills/overclaim-check/` |

```bash
ln -s ~/overclaim-toolkit/skills/overclaim-check ~/.claude/skills/overclaim-check
ln -s ~/overclaim-toolkit/skills/overclaim-check ~/.agents/skills/overclaim-check
```

**3. Register the MCP server.** Replace `/Users/andrewjounkim` with your own home folder (⚠️ **machine-specific**). Both paths must be absolute, and `command` must point to the venv's Python, not the system `python3`.

Claude Code: put this in a `.mcp.json` file (this repo has one), then pass it with `--mcp-config`, or run `claude mcp add`:

```json
{
  "mcpServers": {
    "my-projects": {
      "command": "/Users/andrewjounkim/overclaim-toolkit/.venv/bin/python",
      "args": ["/Users/andrewjounkim/overclaim-toolkit/mcp_server/server.py"]
    }
  }
}
```

Codex: add this to `~/.codex/config.toml`:

```toml
[mcp_servers.my_projects]
command = "/Users/andrewjounkim/overclaim-toolkit/.venv/bin/python"
args = ["/Users/andrewjounkim/overclaim-toolkit/mcp_server/server.py"]
```

Check it: `codex mcp list` should show `my_projects  enabled`. In Claude Code, `/mcp` should show `my-projects`.

**Heads-up: the class's example code no longer runs.** `from mcp.server.fastmcp import FastMCP` fails on `mcp` 2.x. The class was renamed `MCPServer` and lives in `mcp.server.mcpserver`. This repo uses the 2.x name.

## Where I confirmed it works

| | Claude Code 2.1.319 | Codex CLI 0.163 |
|---|---|---|
| Skill loads and triggers | ✅ (Sonnet 5.5 and Opus 5.5 sessions, see DEMONSTRATION.md) | ⚠️ <!-- TODO: fill in after the Codex run --> |
| MCP tool is called | ✅ | ✅ registered (`codex mcp list`); ⚠️ call not yet confirmed, usage limit hit |

## Borrowed or adapted

- The skill's layout (what to do → output format → rules) follows the course's `spec-check` example. The categories, the "disclaimer must be where the claim is" rule, and the precedent rule are mine.
- The search setup (ChromaDB `PersistentClient`, the default embedding model, choosing a cutoff from measured distances) is reused from my HW6 project, DiagKnows.
- I didn't install any third-party skills.

## How I used AI

<!-- TODO (me): rewrite this in my own words. -->
I built this with Claude Code (Opus 5.5) in VS Code. I chose the idea, Claude implemented it, and I directed the changes. It went through my HW3–HW7 prompt logs for repeated instructions and brainstormed skill and MCP pairings. I chose overclaim-check + search_my_projects. I had first turned down a version that copied the worked example too closely. Claude then wrote the indexer, the server, and the skill, and ran headless Claude Code sessions for the demonstration runs. The doer ran on Sonnet 5.5 and the checkers on Opus 5.5. The transcripts are in [`transcripts/`](transcripts/).

## Files

```
skills/overclaim-check/SKILL.md   the checker (current version, v3)
skills/banana-smoke/SKILL.md      the trivial skill I used first to confirm skills load
mcp_server/server.py              the MCP server (one tool)
mcp_server/build_index.py         builds the ChromaDB index from projects.txt
iteration/SKILL.v1.md, v2.md      earlier skill versions (see ITERATION.md)
transcripts/                      rendered session transcripts for every run
demo/render_transcript.py         turns `claude -p --output-format stream-json` logs into those transcripts
```
