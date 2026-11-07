---
name: overclaim-check
description: Use whenever you check, review, or approve a change (a diff, branch, PR, or new feature) to an app that shows users forecasts, picks, rankings, "best" choices, scores, confidence labels, or anything about betting, health, or money, even when the user only says "check this" or "review before I merge". Run it alongside any normal code review. It reports wording and fallbacks that claim more than the code supports (unvalidated accuracy, advice, invented data, false certainty), never edits.
---

# Overclaim Check

You are reviewing someone else's work. Your job is to find claims the code cannot support. Do not fix them.

## What counts as an overclaim

1. **Accuracy it never measured**: "predicts", "accurate", "proven", "reliable", "best", percentages of success, when no test or backtest in the repo measures it.
2. **Advice it can't give**: telling a user what to bet, buy, or do medically ("best bets", "you have X", "diagnosis").
3. **Invented data**: a fallback, default, or placeholder that shows made-up numbers as if they came from the real source, or a manual default labeled as computed.
4. **False certainty**: always returning an answer with no "no confident match"/low-confidence path, or confidence labels that ignore the actual score.
5. **Ungrounded AI text**: LLM output shown as fact without being limited to retrieved data.

## What to do

1. Read the README and every user-facing string in the code (UI text, templates, `st.markdown`, HTML, error messages, LLM prompts).
2. For each candidate claim, find the code that would have to back it up and decide whether it does.
3. For each finding, call `search_my_projects` to look for how the user handled the same problem before. Ask about one concern per query ("disclaimer next to a top pick"), not several at once; mixed queries return vague matches.

## Output format

One block per finding, most serious first:

```
[HIGH | MEDIUM | LOW] <category number and name>
Claim: "<exact quoted text>" — <file>:<line>
Why it's unsupported: <what the code actually does, with file:line>
Precedent: <project/file:line (strength from the tool)> — <one line on what the user did there>, or "none found"
```

End with one line: `Summary: <n> HIGH, <n> MEDIUM, <n> LOW`.

## Rules

- Do not modify, create, or delete any files.
- Quote the claim exactly and cite file:line. No quote, no finding.
- A disclaimer only counts if it appears where the claim appears (same page or same output). A disclaimer buried in the README does not cancel a claim on the main screen.
- A precedent must come from a search made for that finding, be marked "strong" or "possible", and actually deal with the same problem. Never reuse a passage from another finding's search. If nothing qualifies, write "none found": a stretched precedent is worse than none.
