
---

# log_monitor.py

```python
"""
log_monitor.py

A small interactive tool that watches a log file and alerts you
whenever one of your keywords appears in a new line.

Usage:
    python log_monitor.py

Then follow the menu.
"""

import os
import time
import threading
from datetime import datetime


# Default log file — change this if you use a different path.
DEFAULT_PATH = r"C:\Program Files (x86)\MTA San Andreas 1.6\MTA\logs\console.log"


class FileWatcher:
    """Watches a file in a background thread and reacts to keyword matches."""

    def __init__(self, file_path, keywords, check_interval=2):
        self.file_path = file_path
        self.keywords = [k.strip().lower() for k in keywords if k.strip()]
        self.check_interval = check_interval
        self.last_position = 0
        self.running = False
        self.thread = None
        self.seen_matches = set()
        self.alert_count = 0

    def _alert(self, keyword, line):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.alert_count += 1

        print("\n" + "=" * 60)
        print(f"[!] WARNING! [{timestamp}]  (total alerts: {self.alert_count})")
        print(f"    Keyword found: '{keyword}'")
        print(f"    Line: {line.strip()}")
        print("=" * 60 + "\n")

        # Beep — different method per platform
        try:
            if os.name == "nt":
                import winsound
                winsound.Beep(1000, 500)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass

        # Keep a record of every match
        try:
            with open("alerts.log", "a", encoding="utf-8") as log:
                log.write(f"[{timestamp}] {keyword} -> {line.strip()}\n")
        except Exception:
            pass

    def _check_new_content(self):
        try:
            if not os.path.exists(self.file_path):
                return

            current_size = os.path.getsize(self.file_path)

            # File was truncated or rotated — start over
            if current_size < self.last_position:
                self.last_position = 0

            if current_size == self.last_position:
                return

            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()

            if not new_content:
                return

            for line in new_content.splitlines():
                line_lower = line.lower()
                for kw in self.keywords:
                    if kw in line_lower:
                        key = (kw, line.strip())
                        if key not in self.seen_matches:
                            self.seen_matches.add(key)
                            self._alert(kw, line)

        except Exception as e:
            print(f"[ERROR] Reading file: {e}")

    def _loop(self):
        # Skip whatever is already in the file
        try:
            if os.path.exists(self.file_path):
                self.last_position = os.path.getsize(self.file_path)
        except Exception:
            self.last_position = 0

        print("\n[OK] Monitoring started.")
        print(f"     File: {self.file_path}")
        print(f"     Keywords ({len(self.keywords)}): {', '.join(self.keywords)}")
        print(f"     Checking every {self.check_interval}s...")
        print("     Press Ctrl+C to stop.\n")

        while self.running:
            self._check_new_content()
            time.sleep(self.check_interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


# ---------- UI helpers ----------

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 60)
    print("      PERSONAL TERMINAL - FILE MONITOR & ALERT TOOL")
    print("=" * 60)


def pick_file():
    print("\n[1] Choose file path")
    print(f"    (type 1 to auto-select: {DEFAULT_PATH})")
    path = input("> Path or 1: ").strip().strip('"')

    if path == "1":
        print(f"[OK] Auto-selected: {DEFAULT_PATH}")
        return DEFAULT_PATH

    if not path:
        print("[ERROR] No path entered.")
        return None

    if not os.path.exists(path):
        print("[ERROR] File not found!")
        return None

    return path


def pick_keywords_from_txt():
    """Load keywords from a .txt file — one per line."""
    path = input("\n  Enter path to keyword .txt file: ").strip().strip('"')
    if not path:
        print("[ERROR] No file path entered.")
        return None

    if not os.path.exists(path):
        print("[ERROR] File not found!")
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return None

    if not keywords:
        print("[ERROR] The file contains no keywords.")
        return None

    print(f"[OK] Loaded {len(keywords)} keyword(s) from {path}")
    sample = ", ".join(keywords[:10]) + (" ..." if len(keywords) > 10 else "")
    print(f"     Sample: {sample}")
    return keywords


def pick_keywords_manually():
    print("\n[2] Enter keywords one per line.")
    print("    Type  ++++  on an empty line to finish.")
    keywords = []
    while True:
        line = input(f"  Keyword #{len(keywords) + 1}: ").strip()
        if line == "++++":
            break
        if line:
            keywords.append(line)

    if not keywords:
        print("[ERROR] No keywords entered.")
        return None
    return keywords


def pick_keywords():
    print("\n[2] How do you want to provide keywords?")
    print("    [1] Type manually (finish with ++++)")
    print("    [2] Load from a .txt file")
    choice = input("> ").strip()

    if choice == "1":
        return pick_keywords_manually()
    elif choice == "2":
        return pick_keywords_from_txt()

    print("[ERROR] Invalid choice.")
    return None


def pick_interval():
    val = input("\n[3] Check interval in seconds (default 2): ").strip()
    try:
        return float(val) if val else 2.0
    except ValueError:
        return 2.0


# ---------- Main loop ----------

def main():
    clear_screen()
    print_banner()

    while True:
        print("\n--- MAIN MENU ---")
        print("  [1] Start monitoring")
        print("  [2] Show alerts.log")
        print("  [3] Clear alerts.log")
        print("  [4] Exit")

        choice = input("> ").strip()

        if choice == "4":
            print("Goodbye!")
            break

        elif choice == "2":
            if os.path.exists("alerts.log"):
                print("\n--- alerts.log ---")
                with open("alerts.log", "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print("[INFO] No alerts.log yet.")
            input("Press Enter to return to menu...")

        elif choice == "3":
            if os.path.exists("alerts.log"):
                open("alerts.log", "w").close()
                print("[OK] alerts.log cleared.")
            else:
                print("[INFO] No alerts.log to clear.")
            time.sleep(1)

        elif choice == "1":
            path = pick_file()
            if not path:
                input("Press Enter to return...")
                continue

            keywords = pick_keywords()
            if not keywords:
                input("Press Enter to return...")
                continue

            interval = pick_interval()

            watcher = FileWatcher(path, keywords, check_interval=interval)
            watcher.start()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[STOP] Stopping...")
                watcher.stop()
                print(f"[OK] Stopped. Total alerts: {watcher.alert_count}")
                input("Press Enter to return to menu...")

        else:
            print("[ERROR] Invalid choice.")


if __name__ == "__main__":
    main()