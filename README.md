# Captain Selector
Randomly picks two football captains with weighted fairness based on past selection history.

## Description

Every Sunday, a group of friends plays football and splits into two teams by having two captains pick players. The selection should feel fair — ideally, everyone gets a turn as captain roughly equally over time. The obvious solution of asking an LLM to "pick randomly" turned out to produce biased results, with the same names appearing repeatedly.

This program solves that by maintaining a persistent log of every session. When picking captains, it assigns each player a weight inversely proportional to how many times they've already been captain — so players who've had fewer turns are more likely to be picked. It's not strict rotation; it's probabilistic fairness. Someone who's never been captain won't always get picked, but they'll have a meaningfully higher chance.

After selection, a coin toss determines who picks first. The session can optionally be saved to the CSV log, which feeds into future weight calculations.

## Features

- Weighted random selection — the more times you've been captain, the lower your chances next time
- Persistent history via CSV log — weights carry across every session
- Coin toss with dramatic flair to determine first pick
- Bulk name input — paste the WhatsApp group list directly
- Optional logging with a custom date entry per session

## Requirements

- Python 3.6+
- No external libraries — uses only `random`, `time`, `csv`, `sys`, `os` from the standard library

## Installation

No installation needed. Clone or download the files and run directly.

```bash
git clone <repo-url>
cd captain-selector
```

Ensure `captain_log.csv` is in the same directory as `captains.py`, or let the program create it on first run.

## Usage

```bash
python captains.py
```

**Step-by-step walkthrough:**

1. The program prompts you to paste a list of player names, one per line.
2. Signal end of input with `Ctrl+D` on Mac/Linux or `Ctrl+Z` then Enter on Windows.
3. The program calculates weights from the log and picks two captains.
4. A coin toss determines who picks first.
5. You're asked if you want to log the session. Enter `y` to save, `n` to skip.
6. If logging, enter the date of play in `DD-MM-YYYY` format.

**Example input:**
```
Sahil
Kabir
Parth
Kunal
Dev
Tanish
```

**Example output:**
```
✅ Imported 6 players.
📣 SELECTED CAPTAINS: Kabir & Dev
🏆 DEV wins the toss and picks first!
```

## Why LLMs Keep Picking the Same Names

When people used LLMs to pick captains, the same players kept getting selected. This isn't random bad luck — it's structural:

**LLMs are not random number generators.** They predict the next most probable token. When asked to "randomly pick two names" from a list, they pattern-match against what a "fair" or "typical" pick looks like from training data, which introduces systematic bias.

**Positional bias.** LLMs pay unequal attention to names in a list. Names at the top or bottom of the input (primacy and recency effects) are disproportionately salient, making them more likely to be selected regardless of the instruction to be random.

**No state or memory.** An LLM has no knowledge of who was captain last week. Without that context, it has no mechanism to avoid repeat picks. Even if you paste the history into the prompt, the model is reasoning about it, not enforcing hard probability constraints.

**Instruction-following and "reasonableness."** LLMs subtly optimise for responses that seem reasonable to a human reader. Certain names in a group chat feel more "captain-like" due to how they're written, how often they appear in context, or implicit social signals — and the model picks up on these, producing the same choices repeatedly.

The result is a selection that feels random but is quietly deterministic and biased. A proper weighted random algorithm with persistent state is the only real fix.

## Limitations

- The GK rule (players tagged with "gk" in their name) requires at least two GKs to be present, otherwise the program crashes. In most casual sessions with one GK, this is a liability.
- Date input is not validated — any string is accepted.
- Name input is case-insensitive but assumes consistent spelling across sessions. "Kabir" and "Kabeer" are treated as different players.
- No way to correct or delete a logged session without manually editing the CSV.

## Author

Samarth Goradia