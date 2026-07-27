"""
Reassign all data from the demo seed UID to the real Firebase UID.
demo_adriax45_uid -> TMti8ciOrQbO2n3soWErc1dILTo1 (real Firebase UID for adriax45@gmail.com)
"""

import psycopg2

OLD_UID = "demo_adriax45_uid"
NEW_UID = "TMti8ciOrQbO2n3soWErc1dILTo1"

# Tables with a user_id column (child tables + users)
CHILD_TABLES = [
    "categories",
    "gastos_ingresos",
    "ahorro",
    "creditos",
    "deudas",
    "afore",
    "gbm_portfolio",
    "aportaciones",
    "conversation_sessions",
]

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()

# Disable FK checks during reassignment
cur.execute("SET session_replication_role = 'replica';")
c.commit()

print(f"Reassigning data: {OLD_UID} -> {NEW_UID}")
print("=" * 60)

# 1. Ensure a users row exists for the real UID.
#    Update the existing demo user's UID to the real Firebase UID.
cur.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (NEW_UID,))
new_exists = cur.fetchone()[0] > 0

if new_exists:
    # Real UID user row already exists; delete demo row after moving children
    print(f"  users: real UID row already exists, will delete demo row")
else:
    # Rename demo user to real UID
    cur.execute("UPDATE users SET user_id = %s WHERE user_id = %s", (NEW_UID, OLD_UID))
    print(f"  users: renamed {OLD_UID} -> {NEW_UID} ({cur.rowcount} row)")
    c.commit()

# 2. Reassign all child tables
for tbl in CHILD_TABLES:
    cur.execute(f"UPDATE {tbl} SET user_id = %s WHERE user_id = %s", (NEW_UID, OLD_UID))
    print(f"  {tbl}: {cur.rowcount} rows reassigned")
    c.commit()

# 3. If real UID row already existed, remove leftover demo user row
if new_exists:
    cur.execute("DELETE FROM users WHERE user_id = %s", (OLD_UID,))
    print(f"  users: deleted demo row ({cur.rowcount} row)")
    c.commit()

# Re-enable FK checks
cur.execute("SET session_replication_role = 'origin';")
c.commit()

print("=" * 60)
print("Reassignment complete!")

# Verify
print("\n=== VERIFY ===")
for tbl in ["gastos_ingresos", "ahorro", "creditos", "deudas", "afore", "gbm_portfolio", "aportaciones", "categories"]:
    cur.execute(f"SELECT user_id, COUNT(*) FROM {tbl} GROUP BY user_id")
    for r in cur.fetchall():
        print(f"  {tbl}: {r[0]} -> {r[1]} rows")

c.close()
