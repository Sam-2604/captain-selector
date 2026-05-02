# Technical Documentation

## Project Structure

```
captain-selector/
├── captains.py        # Main program — all logic lives here
└── captain_log.csv    # Persistent session log (auto-created on first logged run)
```

`captains.py` contains one class (`CaptainSelector`) and a `main()` entry point. There are no external dependencies beyond the Python standard library.

`captain_log.csv` is both input (history for weight calculation, last session for consecutive block) and output (log of the current session). It must be in the same directory as the script, or the path overridden at instantiation.

---

## Architecture Overview

The program is a single class with a linear execution flow:

```
main()
  └── CaptainSelector()
        ├── load_history()         ← reads CSV on init; populates history + last_captains
        ├── get_players()          ← line-by-line stdin input; deduplicates
        ├── show_weight_summary()  ← prints 3 lowest-weight eligible players
        ├── pick_captains()        ← weighted random selection with GK + consecutive rules
        │     └── get_weight()     ← called per player
        ├── coin_toss()            ← random first-pick decision
        └── log_results()         ← date-validated optional CSV append
```

State is held entirely on the instance (`self.players`, `self.history`, `self.last_captains`). There is no database, no global state, and no inter-session memory beyond the CSV.

---

## Key Functions

### `__init__(self, log_file="captain_log.csv")`
- **Purpose:** Initialises the selector and immediately loads history.
- **Input:** Optional path to the CSV log file.
- **Output:** Populated `self.history` dict and `self.last_captains` set if the log exists.
- **Edge cases:** If the file doesn't exist, history is an empty dict and last_captains is an empty set — all weights default to 1.0 and no players are blocked.

---

### `load_history(self)`
- **Purpose:** Reads the CSV log, counts captaincy frequency, and stores last session's captains.
- **Input:** None (reads `self.log_file`).
- **Output:** Populates `self.history` (name → count) and `self.last_captains` (set of 2 lowercase names from the final row).
- **Edge cases:** File not found is handled silently (empty history). Any other read error prints a warning and proceeds with empty state. Names are stripped of whitespace before use.

---

### `get_players(self)`
- **Purpose:** Reads all player names interactively, one per line. A blank line signals end of input.
- **Input:** Lines from stdin until blank line.
- **Output:** Populates `self.players` as a deduplicated list of lowercase, stripped strings.
- **Edge cases:** Duplicate names trigger a per-name warning and are collapsed to one entry (`dict.fromkeys` preserves first-occurrence order). Fewer than 2 players after deduplication triggers `sys.exit`.

---

### `get_weight(self, name)`
- **Purpose:** Returns a selection weight inversely proportional to captaincy history.
- **Input:** Lowercase player name string.
- **Output:** Float — `1 / (count + 1)`.
- **Behaviour:** Never-captained player → weight `1.0`. Captained once → `0.5`. Five times → `≈0.17`. Weight never reaches zero, so all eligible players always have a non-zero chance.

---

### `show_weight_summary(self)`
- **Purpose:** Prints context before picking — who is blocked and which 3 eligible players are least likely to be chosen this session.
- **Input:** None (uses `self.players`, `self.last_captains`, `self.history`).
- **Output:** Console output only.
- **Logic:** Filters `self.players` to eligible pool (excluding last captains), sorts by weight ascending (lowest weight = most captained = least likely), prints the bottom 3.
- **Edge cases:** If all players are in `self.last_captains` (edge case with very small groups), falls back to the full player list.

---

### `pick_captains(self)`
- **Purpose:** Selects two captains using weighted random sampling, enforcing the consecutive session block and GK pairing rule.
- **Input:** None (uses `self.players`, `self.last_captains`, calls `get_weight`).
- **Output:** Tuple of two lowercase name strings `(cap1, cap2)`.
- **Logic:**
  1. Build eligible pool by excluding `self.last_captains`.
  2. If fewer than 2 eligible players remain, fall back to the full pool with a warning.
  3. Pick Captain 1 from the eligible pool using `random.choices` with computed weights.
  4. Apply GK rule for Captain 2:
     - If Captain 1 is a GK (name contains `"gk"`): Captain 2 must also be a GK.
     - If only one GK is present (no other GK available): print a warning, repick Captain 1 from outfield players only, then pick Captain 2 from remaining outfield.
     - If Captain 1 is outfield: Captain 2 is picked from remaining outfield.
- **Edge cases:** If outfield pool for Captain 2 is empty after the GK fallback, raises `ValueError`.

---

### `coin_toss(self, c1, c2)`
- **Purpose:** Determines which captain picks first.
- **Input:** Two captain name strings.
- **Output:** The winning captain's name string.
- **Behaviour:** `random.choice([c1, c2])` — a fair 50/50. `time.sleep` calls are cosmetic.

---

### `log_results(self, c1, c2, winner)`
- **Purpose:** Optionally appends the current session to the CSV log after validating the date.
- **Input:** Two captain name strings and the toss winner name.
- **Output:** Appends one row to `self.log_file`. Creates the file with headers if it doesn't exist.
- **Date validation:** Uses `datetime.strptime(date_str, "%d-%m-%Y")` in a loop — re-prompts until valid.
- **Edge cases:** User inputs `n` → exits without writing. File path doesn't exist yet → headers are written automatically on first row.

---

## Data Flow

```
captain_log.csv (existing)
       │
       ▼
load_history()
  → self.history    {name: captain_count}
  → self.last_captains  {cap1_name, cap2_name}
       │
       ▼
get_players()  → self.players [name, ...]
       │
       ▼
show_weight_summary()
  ← get_weight() per eligible player
  → console output (blocked names + 3 lowest-weight players)
       │
       ▼
pick_captains()
  ← get_weight() per player
  → (cap1, cap2)
       │
       ▼
coin_toss(cap1, cap2)  → winner
       │
       ▼
log_results(cap1, cap2, winner)
  → appends one row to captain_log.csv
```

The CSV file is the only persistence layer. It is read once at init and appended once at the end (if the user opts in). The program never modifies existing rows.

---

## CSV Format

```
Date,Captain 1,Captain 2,Toss Winner
18-10-2025,Sahil,Deep,Sahil
```

| Field | Format | Notes |
|---|---|---|
| Date | DD-MM-YYYY | Validated by `datetime.strptime` before write |
| Captain 1 | Title case name | Written with `.title()` |
| Captain 2 | Title case name | Written with `.title()` |
| Toss Winner | Title case name | One of Captain 1 or 2 |

The header row has no spaces after commas. `csv.DictReader` reads keys as `"Captain 1"` and `"Captain 2"` exactly, which matches the lookups in `load_history`.

---

## Known Limitations & Future Improvements

**Current limitations:**

- The consecutive session block looks only at the last row in the CSV. If the group skips a week or logs out of order, the "last session" may not reflect the most recent actual game.
- Name matching assumes consistent spelling across sessions. "Kabir" and "Kabeer" accumulate separate histories. This is a user discipline issue, not something the program enforces.
- No CSV editing via the program — intentional design choice to prevent accidental history corruption. Manual CSV edits remain the only option.
- GK captaincy requires at least two GKs. With one GK, the program silently falls back to outfield-only selection.
- Weights are based on captaincy count across all logged sessions, not appearances. Players who attend less frequently accumulate captaincy count slower, making them appear overdue when they may not be relative to their actual attendance. Fixing this would require tracking attendance per session — currently not logged.

**Improvements worth considering:**

- Building a front end for this to make execution easier
- A `--dry-run` flag that shows weighted probabilities and the eligible pool without actually picking, useful for verifying fairness before a session.
- A configurable rolling block window (e.g., block the last N sessions instead of just one).
- A `--stats` flag to print full captaincy history tallied from the CSV without running a session.
