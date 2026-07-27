"""Test Task 12: Aportaciones - verify Afore default exists and aportaciones endpoint works."""
import psycopg2
import httpx

UID = "TMti8ciOrQbO2n3soWErc1dILTo1"

c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()

print("=== R7.1: Afore aportacion exists in DB ===")
cur.execute("SELECT id, target_name, frequency FROM aportaciones WHERE user_id = %s AND LOWER(target_name) = 'afore'", (UID,))
afore = cur.fetchone()
if afore:
    print(f"  ✓ Found: id={afore[0][:8]}... name={afore[1]} freq={afore[2]}")
else:
    print("  ✗ Afore aportacion NOT found in DB")

print("\n=== R7.2: Aportacion status persistence ===")
cur.execute("SELECT record_id, meta_value FROM account_metadata WHERE user_id = %s AND table_name = 'aportacion_status'", (UID,))
statuses = cur.fetchall()
print(f"  Saved statuses: {len(statuses)}")
for s in statuses[:5]:
    print(f"    {s[0][:8]}... = {s[1]}")

print("\n=== R7.3: Afore voluntary contribution in metadata ===")
cur.execute("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = %s AND table_name = 'afore'", (UID,))
afore_meta = cur.fetchall()
if afore_meta:
    for m in afore_meta:
        print(f"  ✓ {m[1]} = {m[2]}")
else:
    print("  ✗ No afore metadata (voluntary_contribution not synced)")

print("\n=== Endpoint test: GET /api/aportaciones ===")
# Can't test auth-required endpoint without token, but check it's registered
resp = httpx.get("http://127.0.0.1:8000/openapi.json", timeout=10)
spec = resp.json()
aport_paths = [p for p in spec["paths"] if "aportaciones" in p]
print(f"  Aportaciones endpoints: {len(aport_paths)}")
for p in sorted(aport_paths):
    methods = list(spec["paths"][p].keys())
    print(f"    {', '.join(m.upper() for m in methods):<12} {p}")

c.close()
print("\nDone!")
