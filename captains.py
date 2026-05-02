import random, time, sys


class TeamSelector:
    def __init__(self):
        self.players = []

    def get_players_bulk(self):
        # Allows users to paste a list of names at once
        print("⚽ Welcome to Captain Picker ⚽")
        print("------------------------------------------")
        print("Paste your list of players below (one per line).")
        print("Press Enter, then Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) to finish.")
        
        # Read all input from terminal at once
        input_data = sys.stdin.read()
        
        # Split by lines and clean up whitespace
        raw_names = [name.strip() for name in input_data.splitlines() if name.strip()]
        
        if len(raw_names) < 2:
            raise ValueError("⚠️ You need at least 2 players to form teams!")
            
        self.players = raw_names
        print(f"\n✅ Successfully imported {len(self.players)} players.")

    def select_captains(self):
        # Logic-based selection with GK rule handling
        print("\n⏳ Analyzing player list and selecting captains...")
        time.sleep(1)
        
        gks = [p for p in self.players if "gk" in p.lower()]
        outfield = [p for p in self.players if "gk" not in p.lower()]

        # Pick the first captain
        cap1 = random.choice(self.players)
        
        # Determine the pool for the second captain
        if "gk" in cap1.lower():
            if len(gks) < 2:
                raise ValueError("🚨 Captain 1 is a GK, but no other GKs are available!")
            cap2 = random.choice([g for g in gks if g != cap1])
        else:
            if len(outfield) < 2:
                raise ValueError("🚨 Captain 1 is an outfield player, but no other outfield players are available!")
            cap2 = random.choice([o for o in outfield if o != cap1])
            
        return cap1, cap2

    def perform_toss(self, c1, c2):
    # Simulated coin toss animation
        print("\n🪙 COIN TOSS IN PROGRESS...")
        for i in range(3):
            time.sleep(0.5)
            print("...flicking...")
            
        winner = random.choice([c1, c2])
        print(f"\n🏆 AND THE WINNER IS: {winner.upper()}!")
        return winner

def main():
    selector = TeamSelector()
    
    try:
        selector.get_players_bulk()
        c1, c2 = selector.select_captains()
        
        print(f"\n📣 CAPTAINS: {c1.title()} & {c2.title()}")
        winner = selector.perform_toss(c1, c2)
        
        print(f"\n👉 {winner.title()}, you have the first pick!")
        
    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()