# Iteration: how the skill failed and what I changed

The earlier versions are saved in [`iteration/SKILL.v1.md`](iteration/SKILL.v1.md) and [`iteration/SKILL.v2.md`](iteration/SKILL.v2.md). The current one is [`skills/overclaim-check/SKILL.md`](skills/overclaim-check/SKILL.md) (v3). For each change I reran the **same prompt on the same diff with the same permissions**, so the skill was the only thing that changed.

## Failure 0: the skill wasn't installed at all

**What happened.** My first checker session ([transcript](transcripts/run1/checker_v1.md)) did an ordinary code review and called the feature ready to merge. It never mentioned "top pick" wording, and it never called the search tool.

**Diagnosis.** That session's startup record lists the available skills, and `overclaim-check` wasn't among them. I had switched project ideas partway through. When I deleted the old skill's symlinks, I never made new ones for this skill. This is the failure the assignment warns about: "discovering that your agent was never reading your skill at all." My smoke-test skill (`banana-smoke`) had passed earlier, so the loading mechanism worked. The skill just wasn't there.

**Fix.** I symlinked it into `~/.claude/skills/` and `~/.agents/skills/`, and now I check the startup skill list before trusting a run.

## Failure 1: the description never triggered (v1 → v2)

**What happened.** With the skill installed and listed (`listed: True` in [checker_v1b](transcripts/run1/checker_v1b.md)), Opus **still didn't load it**. The prompt was `check the new pitcher of the day feature on this branch (uncommitted changes) before i merge it`, and the model went straight to a generic diff review.

**v1 description:**
> Finds places where an app or its docs claim more than the code can back up, such as unvalidated accuracy, betting or medical advice, made-up fallback data, or certainty the model doesn't have. Reports only, never edits. Use when reviewing an app that makes predictions, scores, recommendations, or health/money claims, or before submitting or deploying one.

**Diagnosis.** The description is written around *what the skill finds* and *what kind of app* it's for. My request was about an *action*: check a feature, before merging. Two gaps:
1. "Check this branch before I merge" reads as a request for a normal code review, and nothing in v1 says this skill is part of a code review.
2. A "pitcher of the day" card doesn't sound like "an app that makes predictions" unless you already know what the app does. The words that would match ("pick", "best", "ranking", "feature", "diff", "merge") weren't in the description.

**v2 description:**
> Use whenever you check, review, or approve a change (a diff, branch, PR, or new feature) to an app that shows users forecasts, picks, rankings, "best" choices, scores, confidence labels, or anything about betting, health, or money, even when the user only says "check this" or "review before I merge". Run it alongside any normal code review. It reports wording and fallbacks that claim more than the code supports …, never edits.

**Rerun result** ([checker_v2](transcripts/run1/checker_v2.md)): the skill loaded on the second tool call (`Skill {"skill": "overclaim-check"}`), followed by 3 searches and a report in the right format. In run 2 it also triggered on different wording ("is the hot streak thing … ok to merge?").

## Failure 2: made-up precedents (v2 → v3)

**What happened.** The v2 report looked good, but two of its three findings cited the same passage, `DiagKnows/main.py:81`, as the "precedent". When I looked at what the tool actually returned, the search for finding 2 had come back with **only "probably unrelated" results (1.43–1.46)**. The checker reused the DiagKnows passage from a different finding's search and called it support for "wrong source label", which it doesn't really support.

**Diagnosis.** I caused this. v1/v2 said *"For every finding, call `search_my_projects` once … and cite that passage as the precedent"*, and the output format had a required `Precedent:` line. That told the model a precedent was expected, so it filled the slot even when nothing matched. The tool's docstring says "do not present them as evidence", but the skill's rule overrode it.

**v3 changes:**
- I added a rule: *"A precedent must come from a search made for that finding, be marked "strong" or "possible", and actually deal with the same problem. Never reuse a passage from another finding's search. If nothing qualifies, write "none found": a stretched precedent is worse than none."*
- The Precedent line now has to include the strength the tool reported, so I can audit it.
- The search step now says to ask about one concern per query (see the MCP section below).

**Rerun result** ([checker_v3](transcripts/run1/checker_v3.md), same diff): four findings say `Precedent: none found`. The one precedent left is a strong, relevant match (`strikeout-lab/views/today.py:55`), the season-mismatch warning the new card is missing. In run 2 ([transcript](transcripts/run2/checker_v3.md)), both precedents were strong and on topic.

**What v3 cost.** The v2 report had one good precedent: the Strikeout Lab prompt log entry where I turned down a "best bets" ranking. v3 dropped it, because it didn't run a search for the "top pick" finding. The stricter rule removes padding, but it can also miss a real precedent if the model skips a search.

## The MCP tool also changed

- **The class's example code didn't run.** `from mcp.server.fastmcp import FastMCP` raises `ModuleNotFoundError` on `mcp` 2.3.0, because the class was renamed to `MCPServer`. I switched to the 2.x name and noted it in the README.
- **Cutoffs come from measured distances, not guesses.** The best real matches scored 0.97–1.30; nonsense queries never got under 1.49. So strong < 1.1, possible < 1.4, and anything else is labeled "probably unrelated". This is the HW6 lesson again: search always returns *something*.
- **Noise in the index.** The first index returned built service-worker files (`dist-pages/sw.js`) and CSS for off-topic queries, so I excluded `dist*` folders and `.css`. That took it from 629 chunks to 575.
- **Doers write mixed queries.** Both doer sessions packed several topics into one query. Run 1's top hit was an unrelated Orchestra Panic prompt at 1.19. Asked on its own, the betting-disclaimer question finds the exact Strikeout Lab passage at 0.98. Not every split query did better ("label saying the model is unvalidated" alone came back weaker, at 1.45), but the right passage only showed up when asked alone. The doers never see the skill, so I put "Ask about ONE concern per call" in the **tool's docstring**, which every agent reads. <!-- TODO: rerun a doer to see if its queries got more focused -->

## Still not fixed

- **Severity drifts between runs.** On the same diff, the "lineup not posted yet" label was MEDIUM in v2 and HIGH in v3. The skill names HIGH/MEDIUM/LOW but never defines them. The next version should define each one, e.g. HIGH = a false statement a user will see in normal use.
- **The checker can't run tests** with the read-only permissions I gave it, so it can only *report* claims like "167 tests pass", not confirm them. That's acceptable for a checker, but worth knowing.
