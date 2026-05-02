import random, time, csv, sys, os

class CaptainSelector:
    def __init__(self, log_file="captain_log.csv"):
        self.log_file = log_file
        self.players = []
        self.history = {}
        self.load_history()

    def load_history(self):
        # Reads previous sessions to count captaincy frequency
        if not os.path.exists(self.log_file):
            return
        
        try:
            with open(self.log_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Increment counts for both captains
                    for cap_key in ["Captain 1", "Captain 2"]:
                        name = row[cap_key].lower()
                        self.history[name] = self.history.get(name, 0) + 1
        except Exception:
            print("⚠️ Could not read history file. Starting with fresh weights.")

    def get_players_bulk(self):
        # Accepts names pasted from text messages
        print("⚽ Welcome to the Captain Selector ⚽")
        print("----------------------------------------------")
        print("Paste your list of names (one per line).")
        print("Press Enter, then Ctrl+D (Mac/Linux) or Ctrl+Z (Windows) to finish.")
        
        input_data = sys.stdin.read()
        self.players = [n.strip().lower() for n in input_data.splitlines() if n.strip()]
        
        if len(self.players) < 2:
            sys.exit("🚨 You need at least 2 players!")
        print(f"✅ Imported {len(self.players)} players.")

    def get_weight(self, name):
        # Calculates weight: higher for those who haven't been captains
        count = self.history.get(name, 0)
        return 1 / (count + 1)

    def pick_captains(self):
        # Picks captains using weights while respecting the GK rule
        print("\n⏳ Calculating fair weights and picking captains...")
        time.sleep(1.5)

        gks = [p for p in self.players if "gk" in p]
        outfield = [p for p in self.players if "gk" not in p]

        # 1. Pick Captain 1 from the total pool using weights
        weights = [self.get_weight(p) for p in self.players]
        cap1 = random.choices(self.players, weights=weights, k=1)[0]

        # 2. Pick Captain 2 based on the GK rule
        if "gk" in cap1:
            pool = [p for p in gks if p != cap1]
            if not pool:
                raise ValueError("🚨 GK picked as captain, but no other GKs available!")
        else:
            pool = [p for p in outfield if p != cap1]
            if not pool:
                raise ValueError("🚨 Outfield picked as captain, but no other outfielders available!")

        pool_weights = [self.get_weight(p) for p in pool]
        cap2 = random.choices(pool, weights=pool_weights, k=1)[0]

        return cap1, cap2

    def coin_toss(self, c1, c2):
        # Suspenseful toss to decide who picks first
        print("\n🪙 Flipping the Coin...")
        for _ in range(3):
            time.sleep(0.6)
            print("...spinning...")
        
        winner = random.choice([c1, c2])
        print(f"\n🏆 {winner.upper()} wins the toss and picks first!")
        return winner

    def log_results(self, c1, c2, winner):
        # Saves session data to a CSV if the user agrees
        choice = input("\n📝 Would you like to log this session? (y/n): ").strip().lower()
        if choice != 'y':
            print("Done! Results not logged.")
            return

        date_of_play = input("📅 Enter Date of Play (e.g., DD-MM-YYYY): ").strip()
        
        file_exists = os.path.isfile(self.log_file)
        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date", "Captain 1", "Captain 2", "Toss Winner"])
            writer.writerow([date_of_play, c1.title(), c2.title(), winner.title()])
        
        print(f"✅ Logged to {self.log_file}!")

def main():
    selector = CaptainSelector()
    try:
        selector.get_players_bulk()
        c1, c2 = selector.pick_captains()
        print(f"📣 SELECTED CAPTAINS: {c1.title()} & {c2.title()}")
        
        winner = selector.coin_toss(c1, c2)
        selector.log_results(c1, c2, winner)
        
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()