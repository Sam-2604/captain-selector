# Captain Selector
Randomly picks two football captains with weighted fairness based on past selection history.

## Description

Every Sunday, a group of friends plays football and splits into two teams by having two captains pick players. The selection should feel fair — ideally, everyone gets a turn as captain roughly equally over time. The obvious solution of asking an LLM to "pick randomly" turned out to produce biased results, with the same names appearing repeatedly.

This program solves that by maintaining a persistent log of every session. When picking captains, it assigns each player a weight inversely proportional to how many times they've been captain before — so players who've had fewer turns are more likely to be picked. It's not strict rotation; it's probabilistic fairness. Someone who's never been captain won't always get picked, but they'll have a meaningfully higher chance. Additionally, whoever was captain last week is automatically excluded from this week's selection, preventing back-to-back repeats entirely.

After selection, a coin toss determines who picks first. The session can optionally be saved to the CSV log, which feeds into future weight calculations.

## Features

- Weighted random selection — the more times you've been captain, the lower your chances next time
- Consecutive session block — last session's two captains are ineligible this session
- Persistent history via CSV — weights carry across every session automatically
- Duplicate name detection — warns and deduplicates if the same name is entered twice
- Weight summary — shows the 3 players least likely to be picked this session (most overdue)
- Coin toss to determine first pick
- Friendly line-by-line name input — no terminal shortcuts required
- Date validation — rejects malformed dates before writing to the log

## Requirements

- Python 3.6+
- No external libraries — uses only `random`, `time`, `csv`, `sys`, `os`, `datetime` from the standard library

## Installation

No installation needed. Clone or download the files and run directly.

```bash
git clone <repo-url>
cd captain-selector
```

Place `captain_log.csv` in the same directory as `captains.py`, or let the program create it on first run.

## Usage

```bash
python captains.py
```

**Step-by-step walkthrough:**

1. Enter player names one per line when prompted.
2. Press Enter on a blank line to finish input.
3. The program warns about any duplicate names and removes them.
4. It shows which players are blocked (last session's captains) and the 3 players currently least likely to be picked.
5. Two captains are selected using weighted random sampling.
6. A coin toss determines who picks first.
7. You're asked if you want to log the session. Enter `y` to save, `n` to skip.
8. If logging, enter the date in `DD-MM-YYYY` format. The program will re-prompt until the format is valid.

**Example input:**
```
Sahil
Kabir
Parth
Kunal
Dev
Tanish

```
*(blank line ends input)*

**Example output:**
```
✅ Imported 6 players.

🚫 Blocked from this session (last session's captains): Aagam, Sam

📊 Least likely picks this session (most times captain):
   Kabir — captain 5x (weight: 0.17)
   Kunal — captain 4x (weight: 0.20)
   Aagam — captain 4x (weight: 0.20)

📣 SELECTED CAPTAINS: Parth & Dev
🏆 DEV wins the toss and picks first!
```

## Why LLMs Keep Picking the Same Names

When people used LLMs to pick captains, the same players kept getting selected. This isn't random bad luck — it's structural.

**LLMs are not random number generators.** They predict the next most probable token. When asked to "randomly pick two names" from a list, they pattern-match against what a "fair" or "typical" pick looks like based on training data, which introduces systematic bias.

**Positional bias.** LLMs pay unequal attention to names depending on where they appear in the input. Names at the top or bottom of a list (primacy and recency effects) are disproportionately salient, making them more likely to be selected regardless of the instruction.

**No state or memory.** An LLM has no knowledge of who was captain last week. Without that context, it has no mechanism to avoid repeat picks. Even if you paste the history into the prompt, the model is reasoning about it — not enforcing probabilistic constraints — so it can still produce the same outputs.

**Instruction-following and "reasonableness."** LLMs subtly optimise for responses that feel reasonable to a human reader. Certain names in a group chat may feel more "captain-like" due to how they're written, how often they appear in context, or implicit social signals the model picks up on. The result is a selection that appears random but is quietly biased and consistent across runs.

A weighted random algorithm with persistent state is the only real fix.

## Limitations

- If only one GK is present in the session, a GK cannot be selected as captain (the program falls back to outfield-only selection).
- Name matching is case-insensitive but assumes consistent spelling across sessions. "Kabir" and "Kabeer" are treated as different players.
- No way to edit or delete logged sessions without manually editing the CSV — intentional, to prevent accidental history corruption.
- The consecutive session block only looks at the immediately preceding session, not a rolling window.
- Weights are based on captaincy count across all logged sessions, not appearances. Players who attend less frequently accumulate captaincy count slower, making them appear overdue when they may not be relative to their actual attendance. Fixing this would require tracking attendance per session — currently not logged.

## Author

Samarth Goradia