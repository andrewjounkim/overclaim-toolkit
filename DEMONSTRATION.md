# Demonstration

**The real task:** adding two features to **Strikeout Lab**, my HW3 MLB strikeout app (live repo [andrewjounkim/strikeout-lab](https://github.com/andrewjounkim/strikeout-lab)). Betting-flavored features are where this app is most likely to overclaim. Each feature went on its own local branch (`demo/pitcher-of-the-day` and `demo/hot-streak`), and neither branch has been merged or pushed.

**Setup for every run.** Each session was a separate headless Claude Code process (`claude -p`) with a fresh context. The only MCP server loaded was this one (`--strict-mcp-config`).

| Role | Model | Allowed tools |
|---|---|---|
| Doer | Claude **Sonnet 5.5** | `search_my_projects`, file read/edit, pytest, git diff/status |
| Checker | Claude **Opus 5.5** (a different model) | `search_my_projects`, the Skill tool, read-only tools, git diff/status/log. `Edit`, `Write`, and `NotebookEdit` were blocked. |

None of the prompts mention the skill or the tool. The transcripts below are trimmed. The full rendered versions are in [`transcripts/`](transcripts/), and every tool call is shown there.

---

## Run 1: "Pitcher of the day" card

### Doer ([full transcript](transcripts/run1/doer.md))

> **Prompt:** `add a pitcher of the day card to the homepage that picks the best strikeout pitcher pitching today and shows why. keep it consistent with how i've handled this kind of thing in my past projects. run the tests when done. dont commit.`

```
tool call → ToolSearch            {"query": "select:mcp__my-projects__search_my_projects"}
tool call → Bash                  git ls-files && cat README.md | head -60
tool call → mcp__my-projects__search_my_projects
            {"query": "how I labeled an unvalidated model or pick, disclaimer wording, and rules I gave the AI", "n_results": 8}
   result:  ## orchestra-panic-phase2/prompt_log.md:43  (possible, distance 1.19) ...
tool call → Read views/home.py, slate.py, prompt_log.md, views/today.py, ... (10 more reads/greps)
...
assistant: The pitcher of the day card is built, but I couldn't run the tests. Both `python3 -m pytest`
           attempts were blocked at the permission prompt ...
```

**Result:** 4 files changed, +150 lines. The card has a disclaimer caption ("It is a forecast, not a bet: the model has never been tested against real results") and a docstring that says "Best here only means the model's highest expected strikeouts." The doer called `python3` instead of the venv, so it couldn't run the tests. When I ran them, 2 of the new tests failed (167 passed).

**What the tool call shows:** the doer reached for the tool on its own, but its query packed three topics together. The top hit was an unrelated Orchestra Panic prompt at "possible" strength. This led to a docstring change (see ITERATION.md).

### Checker, final version v3 ([full transcript](transcripts/run1/checker_v3.md))

> **Prompt:** `check the new pitcher of the day feature on this branch (uncommitted changes) before i merge it`

```
tool call → Bash   git diff
tool call → Skill  {"skill": "overclaim-check"}                               ← the skill loads
tool call → Bash   (reads slate.py, model.py, today.py, context.py)
tool call → mcp__my-projects__search_my_projects {"query": "saying a lineup is not posted when it actually failed to load"}
tool call → mcp__my-projects__search_my_projects {"query": "warning when the selected season doesn't match the slate date"}
tool call → mcp__my-projects__search_my_projects {"query": "top-ranked result driven by a manual default value instead of real data"}
tool call → mcp__my-projects__search_my_projects {"query": "showing caveat notes like clamped probability or few starts next to a highlighted pick"}
```

Report (trimmed):

```
[HIGH] 3 — Invented data
Claim: "{opponent} strike out {team_rate} of the time (lineup not posted yet)" — views/home.py:204
Why it's unsupported: basis == "team" doesn't mean the lineup is missing. It is also "team" when
the batter stats fail to load: home.py:189 falls back to hitters = {} with no message ... The Today
page shows a warning for this (today.py:61).
Precedent: none found

[MEDIUM] 4 — False certainty
Claim: "Pitcher of the day" — views/home.py:219
Why it's unsupported: in live mode the card always uses today's schedule, but the stats come from
whatever season is picked in the sidebar (context.py:173) ... with no warning.
Precedent: strikeout-lab/views/today.py:55 (strong): the Today page warns "This slate is from
{year}, but the statistics come from the {season} season selected in the sidebar."

[MEDIUM] 4 — False certainty   card drops every row["notes"] caveat (clamped probability, 1-start workload)
[LOW] 3 — Invented data        the ranking can rest on the manual 24-batter default
[LOW] 2 — Advice it can't give "Model's top pick" sounds like a tipster; the disclaimer right below covers it

Summary: 1 HIGH, 2 MEDIUM, 2 LOW
```

**Did I agree?** <!-- TODO (me): confirm or push back in my own words. --> I checked the HIGH and the first MEDIUM against the branch code, and both hold up. `home.py` does fall back to `hitters = {}` without the warning that `today.py:61` shows. The year check at `today.py:55` really is missing from the card. The LOW about "top pick" is a judgment call. The checker said itself that the same-page disclaimer covers it, and I would still reword it as "Most expected strikeouts today."

---

## Run 2: "Hot streak" badge

### Doer ([full transcript](transcripts/run2/doer.md))

> **Prompt:** `add a hot streak badge to the browse page for pitchers whose strikeout rate over their last 3 starts is way above their season rate. keep it consistent with how i've handled this kind of thing in my past projects. run the tests with ./.venv/bin/python -m pytest when done. dont commit.`

```
tool call → mcp__my-projects__search_my_projects {"query": "badge or label for a hot streak / recent form computed from stats, wording and thresholds"}
tool call → mcp__my-projects__search_my_projects {"query": "rules I gave the AI about not overclaiming, small sample size caveats, labeling unvalidated signals"}
tool call → mcp__my-projects__search_my_projects {"query": "game log fetch failure fallback: ...", "project": "strikeout-lab"}
...
tool call → Bash  ./.venv/bin/python -m pytest -q
assistant: I added the hot streak badge to Browse, and all 167 tests pass ... Nothing is committed.
```

**Result:** 6 files changed, +147 / −3. The badge needs the last-3-starts strikeout rate to be ≥30% above the season rate **and** ≥2 standard errors above it. The caption calls the cutoffs "not validated" and the badge "descriptive only". I reran the suite myself and got 167 passed.

### Checker v3 ([full transcript](transcripts/run2/checker_v3.md))

> **Prompt:** `is the hot streak thing on this branch ok to merge? (uncommitted changes)` (worded differently from run 1 on purpose)

```
tool call → Skill  {"skill": "overclaim-check"}                               ← triggers again
tool call → mcp__my-projects__search_my_projects {"query": "showing that a value is missing because data was unavailable instead of leaving it blank"}
tool call → mcp__my-projects__search_my_projects {"query": "per-row note when a pitcher's game log is missing so the fallback is labeled"}
```

```
[MEDIUM] 4. False certainty
Claim: "🔥 Hot streak" if p["id"] in streaks else "" — views/browse.py:70
Why it's unsupported: A blank "Form" cell looks the same whether the pitcher was checked and isn't
hot, or couldn't be checked at all ... Offline, the snapshot only saves game logs for about 20 top
starters ... The caption at views/browse.py:80-85 does say so, but only once for the whole table.
Precedent: strikeout-lab/views/lab.py:121 (strong) — when there's no game log you show a reason
right there ... Also slate.py:97 (strong) — you add a note to each affected row.

Summary: 0 HIGH, 1 MEDIUM, 0 LOW
```

It also confirmed what the doer got right: the "2+ standard errors" check really is in the code (`model.py:271`), and the forecast never uses the badge. It also refused to vouch for "167 tests pass" because it couldn't run them itself.

**Did I agree?** <!-- TODO (me): my own words. --> Yes. A missing log gives `streak = None`, so the cell is `""`, the same as "not hot". Run 2's doer was more careful than run 1's, and the checker's report is proportionally shorter. That's what I want from a checker: it didn't invent problems to fill the format.

---

## Consistency across the runs

- **Triggering:** in all three v2/v3 checker sessions, the skill loaded on the second tool call. Two different phrasings were used, and neither named the skill.
- **Format:** every report used the same block format and `Summary:` line, so I can compare them side by side.
- **Same diff, two versions:** checker v2 and v3 on the run 1 diff both found the "lineup not posted" label and the missing caveats. The severity drifted, though: the label was MEDIUM in v2 and HIGH in v3. See ITERATION.md.
- **Codex:** <!-- TODO: add the Codex (GPT) checker run once the usage limit resets, or remove this line. -->
