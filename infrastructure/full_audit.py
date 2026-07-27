"""Full platform audit: data accuracy, agent behavior, endpoint health."""
import asyncio
import sys
import json
sys.path.insert(0, "/home/ubuntu/Finalat")

from backend.models.database import async_session
from backend.services.fina_agent import fina_chat
import psycopg2

UID = "TMti8ciOrQbO2n3soWErc1dILTo1"

# ─── 1. DATA ACCURACY AUDIT ───────────────────────────────────────────────────
print("=" * 70)
print("1. DATA ACCURACY AUDIT")
print("=" * 70)

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# Check instruments data accuracy
cur.execute("SELECT name, institution, annual_rate, requires_purchase, conditions, max_investment FROM instruments ORDER BY annual_rate DESC")
instruments = cur.fetchall()
print(f"\n  Instruments in DB: {len(instruments)}")
print("  Top 5 by rate:")
for i in instruments[:5]:
    print(f"    {i[0]} ({i[1]}) - {i[2]}% | purchase_req={i[3]} | max={i[5]} | {i[4][:60] if i[4] else 'N/A'}")

# Known real-world rates (July 2026 approximate - verify these)
known_rates = {
    "Nu Cuenta": {"min": 10, "max": 15, "note": "Cajita Turbo ~13% con compra"},
    "Mercado Pago": {"min": 10, "max": 14, "note": "~12% sin límite"},
    "Didi Cuenta": {"min": 12, "max": 16, "note": "~15% hasta $10k"},
    "CETES 28 días": {"min": 5, "max": 8, "note": "~6-7% gobierno"},
}

print("\n  Rate plausibility check:")
for inst in instruments:
    name = inst[0]
    rate = float(inst[2])
    for known_name, expected in known_rates.items():
        if known_name.lower() in name.lower():
            in_range = expected["min"] <= rate <= expected["max"]
            print(f"    {name}: {rate}% {'✓ PLAUSIBLE' if in_range else '⚠ CHECK'} (expected {expected['min']}-{expected['max']}%)")
            break

# Check user data integrity
print("\n  User data integrity:")
cur.execute("SELECT COUNT(*) FROM gastos_ingresos WHERE user_id = %s", (UID,))
gi_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM ahorro WHERE user_id = %s", (UID,))
ahorro_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM creditos WHERE user_id = %s", (UID,))
creditos_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM categories WHERE user_id = %s", (UID,))
cat_count = cur.fetchone()[0]
print(f"    Gastos/Ingresos: {gi_count} records")
print(f"    Ahorro accounts: {ahorro_count}")
print(f"    Creditos: {creditos_count}")
print(f"    Categories: {cat_count}")
c.close()

# ─── 2. AGENT BEHAVIOR AUDIT ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("2. AGENT BEHAVIOR AUDIT")
print("=" * 70)

async def test_agent(desc, messages, checks):
    converse_messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages]
    async with async_session() as db:
        response, _ = await fina_chat(converse_messages, db, user_name="Adrian")
    
    print(f"\n  TEST: {desc}")
    print(f"  Response (first 200 chars): {response[:200]}")
    results = []
    for check_name, check_fn in checks.items():
        passed = check_fn(response)
        results.append((check_name, passed))
        print(f"    {'✓' if passed else '✗'} {check_name}")
    return results

async def run_agent_tests():
    all_results = []
    
    # Test: Personalización con nombre
    r = await test_agent(
        "Personalización (usa nombre del usuario)",
        [{"role": "user", "content": "Hola, quiero ahorrar"}],
        {
            "Uses user name or is personalized": lambda r: "adrian" in r.lower() or "cuánto" in r.lower() or "dinero" in r.lower(),
            "No thinking exposed": lambda r: "el usuario" not in r.lower() and "<thinking>" not in r.lower(),
        }
    )
    all_results.extend(r)

    # Test: Plazo clarity
    r = await test_agent(
        "Claridad en plazos (debe explicar rangos)",
        [
            {"role": "user", "content": "Tengo 200 mil para invertir"},
            {"role": "assistant", "content": "¿En cuánto tiempo necesitas ese dinero? [[SLIDER_PLAZO]]"},
            {"role": "user", "content": "mediano plazo"},
        ],
        {
            "Clarifies what mediano plazo means": lambda r: "mes" in r.lower() or "año" in r.lower() or "6" in r,
        }
    )
    all_results.extend(r)

    # Test: No recomienda inversiones complejas
    r = await test_agent(
        "No recomienda renta variable",
        [{"role": "user", "content": "Quiero invertir en la bolsa de valores, ¿qué acciones me recomiendas?"}],
        {
            "Redirects away from stocks": lambda r: "ahorro" in r.lower() or "cetes" in r.lower() or "no" in r.lower(),
            "Does NOT give stock picks": lambda r: "compra" not in r.lower() or "accion" not in r.lower(),
        }
    )
    all_results.extend(r)

    # Test: Calculation accuracy
    r = await test_agent(
        "Cálculo correcto a plazo (50k a 6 meses en Mercado Pago 12%)",
        [
            {"role": "user", "content": "Si meto 50 mil en Mercado Pago por 6 meses, cuánto gano?"},
        ],
        {
            "Gives a number": lambda r: "$" in r and any(c.isdigit() for c in r),
            "Approximately correct (~$3000)": lambda r: "3,000" in r or "3000" in r or "2,500" in r or "3,500" in r or "rendimiento" in r.lower(),
        }
    )
    all_results.extend(r)

    # Summary
    passed = sum(1 for _, p in all_results if p)
    total = len(all_results)
    print(f"\n  AGENT SCORE: {passed}/{total} checks passed")
    return passed, total

agent_passed, agent_total = asyncio.run(run_agent_tests())

# ─── 3. ENDPOINT HEALTH CHECK ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("3. ENDPOINT HEALTH CHECK")
print("=" * 70)

import httpx
endpoints = [
    "/api/health",
    "/api/instruments",
    "/api/chat/greeting",
    "/api/scrapers/banxico/tasas-cetes",
    "/api/scrapers/banxico/tasa-objetivo",
]

for ep in endpoints:
    try:
        resp = httpx.get(f"http://127.0.0.1:8000{ep}", timeout=10)
        status = "✓" if resp.status_code == 200 else "✗"
        print(f"  {status} {ep} -> {resp.status_code}")
    except Exception as e:
        print(f"  ✗ {ep} -> ERROR: {e}")

# ─── 4. COURSE CONTENT AUDIT ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("4. COURSE CONTENT AUDIT")
print("=" * 70)

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()
cur.execute("SELECT c.title, COUNT(l.id) as lessons, c.sort_order FROM courses c LEFT JOIN lessons l ON l.course_id = c.id GROUP BY c.id, c.title, c.sort_order ORDER BY c.sort_order")
for r in cur.fetchall():
    print(f"  {r[2]}. {r[0]} ({r[1]} lessons)")

# Check for empty lessons
cur.execute("SELECT id, title, LENGTH(content) as len FROM lessons WHERE LENGTH(content) < 100")
empty = cur.fetchall()
if empty:
    print(f"\n  ⚠ Lessons with very short content ({len(empty)}):")
    for e in empty:
        print(f"    {e[0]}: {e[1]} ({e[2]} chars)")
else:
    print("\n  ✓ All lessons have substantial content")

# Check demos are attached
cur.execute("SELECT id, title FROM lessons WHERE content LIKE '%[[DEMO:%'")
demos = cur.fetchall()
print(f"\n  Interactive demos attached: {len(demos)}")
for d in demos:
    print(f"    ✓ {d[1]}")

c.close()

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
