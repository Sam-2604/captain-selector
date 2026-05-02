# Technical Documentation

## Project Structure

```
captain-selector/
├── captains.py        # Main program — all logic lives here
└── captain_log.csv    # Persistent session log (auto-created on first logged run)
```

`captains.py` contains one class (`CaptainSelector`) and a `main()` entry point. There are no external dependencies.

`captain_log.csv` is both the input (history for weight calculation) and the output (log of the current session). It must be in the same directory as the script, or the path must be overridden at instantiation.

---

## Architecture Overview

The program is structured as a single class with a linear execution flow:

```
main()
  └── CaptainSelector()
        ├── load_history()        ← reads CSV on init
        ├── get_players_bulk()    ← stdin input
        ├── pick_captains()       ← weighted random selection
        │     └── get_weight()    ← called per player
        ├── coin_toss()           ← random first-pick decision
        └── log_results()        ← optional CSV append
```

State is held entirely on the instance (`self.players`, `self.history`). There is no database, no global state, and no inter-session memory beyond what's in the CSV.

---

## Key Functions

### `__init__(self, log_file="captain_log.csv")`
- **Purpose:** Initialises the selector and immediately loads history.
- **Input:** Optional path to the CSV log file.
- **Output:** Populated `self.history` dict if the log exists.
- **Edge cases:** If the file doesn't exist yet, history is an empty dict (all weights equal to 1.0).

---

### `load_history(self)`
- **Purpose:** Reads the CSV log and counts how many times each player has been captain.
- **Input:** None (reads `self.log_file`).
- **Output:** Populates `self.history` — a dict mapping lowercase player name → captain count.
- **Edge cases handled:** File not found (skipped silently). Any other read error is caught and a warning is printed.
- **Known bug:** The CSV header uses spaces after commas (`Date, Captain 1, Captain 2, Toss Winner`). `csv.DictReader` reads keys literally, so the actual keys are `" Captain 1"` and `" Captain 2"` (with a leading space). The lookup `row["Captain 1"]` will raise a `KeyError`, which is silently caught by the bare `except Exception`, meaning **history is never actually loaded**. Fix: strip keys or write the header without spaces.

---

### `get_players_bulk(self)`
- **Purpose:** Reads all player names from stdin in one shot.
- **Input:** Multi-line text via stdin, terminated by EOF (`Ctrl+D` / `Ctrl+Z`).
- **Output:** Populates `self.players` as a list of lowercase, stripped name strings.
- **Edge cases:** Fewer than 2 players triggers `sys.exit`.

---

### `get_weight(self, name)`
- **Purpose:** Returns a selection weight for a player inversely proportional to their captain history.
- **Input:** Lowercase player name string.
- **Output:** Float — `1 / (count + 1)` where `count` is times previously captained.
- **Behaviour:** A player never captained gets weight `1.0`. One previous session → `0.5`. Five sessions → `~0.17`. The weight never reaches zero, so everyone always has a non-zero chance.

---

### `pick_captains(self)`
- **Purpose:** Selects two captains using weighted random sampling with the GK rule applied.
- **Input:** None (uses `self.players` and calls `get_weight`).
- **Output:** Tuple of two lowercase name strings `(cap1, cap2)`.
- **Logic:**
  1. Captain 1 is picked from the full player pool using `random.choices` with computed weights.
  2. Captain 2 is picked from a sub-pool:
     - If Captain 1 is a GK (name contains `"gk"`), Captain 2 must also be a GK.
     - If Captain 1 is outfield, Captain 2 must also be outfield.
- **Edge cases:** If the required sub-pool for Captain 2 is empty (e.g. only one GK present), raises `ValueError`.
- **Known issue:** The GK pairing rule (GK must be paired with GK) is almost certainly wrong for casual football. It was likely intended to exclude GKs from captaincy entirely, or to ensure GKs are distributed across teams — neither of which this logic achieves.

---

### `coin_toss(self, c1, c2)`
- **Purpose:** Randomly determines which captain picks first.
- **Input:** Two captain name strings.
- **Output:** The winning captain's name string.
- **Behaviour:** Uses `random.choice([c1, c2])` — a fair 50/50. The `time.sleep` calls are cosmetic.

---

### `log_results(self, c1, c2, winner)`
- **Purpose:** Optionally appends the current session to the CSV log.
- **Input:** Two captain names and the toss winner name.
- **Output:** Writes one row to `self.log_file`. Creates the file with headers if it doesn't exist.
- **Edge cases:** User inputs `n` — exits without writing. Date is not validated; any string is accepted.

---

## Data Flow

```
captain_log.csv (existing)
       │
       ▼
load_history() → self.history {name: count}
                        │
                        ▼
get_players_bulk() → self.players [name, name, ...]
                        │
                        ▼
pick_captains()  ← get_weight() per player
       │
       ▼
coin_toss(cap1, cap2)
       │
       ▼
log_results() → appends row to captain_log.csv
```

The CSV file is the only persistence layer. It is read once on init and appended once at the end of a session (if the user opts in).

---

## CSV Format

```
Date, Captain 1, Captain 2, Toss Winner
18-10-2025,Sahil,Deep,Sahil
```

| Field | Format | Notes |
|---|---|---|
| Date | DD-MM-YYYY | User-entered string, not validated |
| Captain 1 | Title case name | Written with `.title()` |
| Captain 2 | Title case name | Written with `.title()` |
| Toss Winner | Title case name | One of Captain 1 or 2 |

**Note:** The header row has a space after each comma. This causes `load_history()` to silently fail (see Known Limitations).

---

## Known Limitations & Future Improvements

**Bugs to fix first:**

- **Header space bug:** Change `writer.writerow(["Date", "Captain 1", ...])` to write without spaces, and add `.strip()` when reading keys in `load_history()`. This is the most impactful fix — it restores the core weighting feature.
- **GK rule:** Either remove it, or replace it with a clean "exclude GKs from captain eligibility" flag. The current implementation requires two GKs and will crash in the common case of one GK.

**Improvements worth adding:**

- **Date validation:** Parse and validate the date string against `DD-MM-YYYY` using `datetime.strptime` before writing.
- **Friendlier input:** Replace the stdin EOF approach with an input loop that terminates on a blank line. Most users don't know Ctrl+D.
- **Name normalisation:** Warn or deduplicate if the same name appears twice in the input list.
- **Session review:** Print a summary of current weights before picking, so players can see the fairness logic.
- **Undo/edit log:** A simple CLI flag like `--edit-log` to open the CSV in the default editor, or a `--remove-last` option.
- **Streak detection:** Warn if the same player has been captain in consecutive sessions.