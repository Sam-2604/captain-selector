import random, time, csv, sys, os
from datetime import datetime


class CaptainSelector:
    def __init__(self, log_file="captain_log.csv"):
        self.log_file = log_file
        self.players = []
        self.history = {}
        self.last_captains = set()
        self.load_history()

    def load_history(self):
        """Reads previous sessions to count captaincy frequency and record last session's captains."""
        if not os.path.exists(self.log_file):
            return

        try:
            rows = []
            with open(self.log_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
                    for cap_key in ["Captain 1", "Captain 2"]:
                        name = row[cap_key].strip().lower()
                        self.history[name] = self.history.get(name, 0) + 1

            # Store last session's captains — neither can be picked this session
            if rows:
                last = rows[-1]
                self.last_captains = {
                    last["Captain 1"].strip().lower(),
                    last["Captain 2"].strip().lower()
                }
        except Exception:
            print("⚠️  Could not read history file. Starting with fresh weights.")

    def get_players(self):
        """Accepts names entered one per line. Blank line signals end of input."""
        print("⚽ Welcome to the Captain Selector ⚽")
        print("----------------------------------------------")
        print("Enter player names one per line.")
        print("Press Enter on a blank line when you're done.\n")

        raw_names = []
        while True:
            line = input().strip()
            if not line:
                break
            raw_names.append(line.lower())

        # Detect and warn about duplicates, then deduplicate
        seen = set()
        duplicates = set()
        for name in raw_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        if duplicates:
            for name in duplicates:
                print(f"⚠️  Duplicate detected: '{name.title()}' — keeping one entry.")

        self.players = list(dict.fromkeys(raw_names))  # deduplicate, preserve first occurrence

        if len(self.players) < 2:
            sys.exit("🚨 You need at least 2 players!")

        print(f"\n✅ Imported {len(self.players)} players.")

    def get_weight(self, name):
        """Returns selection weight inversely proportional to captaincy history."""
        count = self.history.get(name, 0)
        return 1 / (count + 1)

    def show_weight_summary(self):
        """Prints the 3 players least likely to be picked (most overdue for captaincy)."""
        # Filter out last session's captains since they're ineligible
        eligible = [p for p in self.players if p not in self.last_captains]
        if not eligible:
            eligible = self.players

        weights = {p: self.get_weight(p) for p in eligible}
        # Sort ascending — lowest weight = most times captained = least likely this session
        least_likely = sorted(weights.items(), key=lambda x: x[1])[:3]

        if self.last_captains:
            blocked = [n.title() for n in self.last_captains if n in {p.lower() for p in self.players}]
            if blocked:
                print(f"\n🚫 Blocked from this session (last session's captains): {', '.join(blocked)}")

        print("\n📊 Least likely picks this session (most times captain):")
        for name, w in least_likely:
            count = self.history.get(name, 0)
            label = "never been captain" if count == 0 else f"captain {count}x"
            print(f"   {name.title()} — {label} (weight: {w:.2f})")

    def pick_captains(self):
        """Picks two captains using weighted random selection, respecting GK and consecutive rules."""
        print("\n⏳ Calculating fair weights and picking captains...")
        time.sleep(1.5)

        # Exclude last session's captains
        eligible = [p for p in self.players if p not in self.last_captains]
        if len(eligible) < 2:
            print("⚠️  Not enough eligible players after excluding last session's captains. Using full pool.")
            eligible = self.players

        gks = [p for p in eligible if "gk" in p]
        outfield = [p for p in eligible if "gk" not in p]

        # Pick Captain 1 from eligible pool
        weights = [self.get_weight(p) for p in eligible]
        cap1 = random.choices(eligible, weights=weights, k=1)[0]

        # Pick Captain 2 based on GK rule
        if "gk" in cap1:
            other_gks = [p for p in gks if p != cap1]
            if not other_gks:
                # Only one GK present — repick cap1 from outfield
                print("⚠️  Only one GK available — repicking Captain 1 from outfield.")
                if not outfield:
                    sys.exit("🚨 Not enough players to pick captains.")
                outfield_weights = [self.get_weight(p) for p in outfield]
                cap1 = random.choices(outfield, weights=outfield_weights, k=1)[0]
                pool = [p for p in outfield if p != cap1]
            else:
                pool = other_gks
        else:
            pool = [p for p in outfield if p != cap1]
            if not pool:
                raise ValueError("🚨 Not enough outfield players to pick two captains.")

        pool_weights = [self.get_weight(p) for p in pool]
        cap2 = random.choices(pool, weights=pool_weights, k=1)[0]

        return cap1, cap2

    def coin_toss(self, c1, c2):
        """Suspenseful coin toss to decide who picks first."""
        print("\n🪙 Flipping the Coin...")
        for _ in range(3):
            time.sleep(0.6)
            print("   ...spinning...")

        winner = random.choice([c1, c2])
        print(f"\n🏆 {winner.upper()} wins the toss and picks first!")
        return winner

    def log_results(self, c1, c2, winner):
        """Saves session data to CSV after validating date input."""
        choice = input("\n📝 Would you like to log this session? (y/n): ").strip().lower()
        if choice != "y":
            print("Done! Results not logged.")
            return

        while True:
            date_str = input("📅 Enter Date of Play (DD-MM-YYYY): ").strip()
            try:
                datetime.strptime(date_str, "%d-%m-%Y")
                break
            except ValueError:
                print("❌ Invalid format. Please use DD-MM-YYYY (e.g., 03-05-2026).")

        file_exists = os.path.isfile(self.log_file)
        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date", "Captain 1", "Captain 2", "Toss Winner"])
            writer.writerow([date_str, c1.title(), c2.title(), winner.title()])

        print(f"✅ Logged to {self.log_file}!")


def main():
    selector = CaptainSelector()
    try:
        selector.get_players()
        selector.show_weight_summary()
        c1, c2 = selector.pick_captains()
        print(f"\n📣 SELECTED CAPTAINS: {c1.title()} & {c2.title()}")

        winner = selector.coin_toss(c1, c2)
        selector.log_results(c1, c2, winner)

    except ValueError as e:
        print(e)


if __name__ == "__main__":
    main()