import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    fixes = [
        ("disponible", "available"),
        ("disponible", "DISPONIBLE"),
        ("emprunte",   "EMPRUNTE"),
        ("reserve",    "RESERVE"),
    ]
    total = 0
    for new_val, old_val in fixes:
        r = conn.execute(text(f"UPDATE livre SET status = '{new_val}' WHERE status = '{old_val}'"))
        total += r.rowcount
    conn.commit()
    print(f"[OK] {total} rows fixed.")
