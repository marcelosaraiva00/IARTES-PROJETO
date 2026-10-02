import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "iartes.db"
c = sqlite3.connect(db)
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("TABLES:", tables)
for t in tables:
    print(f"\n--- {t} ---")
    for col in c.execute(f"PRAGMA table_info({t})"):
        print(col)
indexes = c.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
print("\nINDEXES:")
for idx in indexes:
    print(idx)
