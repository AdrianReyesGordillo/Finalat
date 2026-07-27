"""Task 5: Populate tiered_rates, Task 7: Rename trading course, Task 9: Alembic note."""
import psycopg2
import json

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# ═══ TASK 5: Populate tiered_rates ═══════════════════════════════════════════
print("=== TASK 5: Populating tiered_rates ===")

tiered_data = {
    "Nu Cuenta": json.dumps([
        {"min_amount": 0, "max_amount": 25000, "rate": 13.0, "condition": "Requiere 1 compra/mes con tarjeta Nu"},
        {"min_amount": 25000.01, "max_amount": None, "rate": 6.5, "condition": "Excedente sin requisito"}
    ]),
    "Nu Cajitas": json.dumps([
        {"min_amount": 0, "max_amount": None, "rate": 6.5, "condition": "Sin requisito de compra"}
    ]),
    "Didi Cuenta": json.dumps([
        {"min_amount": 0, "max_amount": 10000, "rate": 15.0, "condition": "Sin requisito"},
        {"min_amount": 10000.01, "max_amount": None, "rate": 7.5, "condition": "Excedente"}
    ]),
    "Ualá Cuenta Plus": json.dumps([
        {"min_amount": 0, "max_amount": 30000, "rate": 12.0, "condition": "Requiere consumo mínimo $3,000/mes"},
        {"min_amount": 30000.01, "max_amount": None, "rate": 0, "condition": "Sin rendimiento sobre excedente"}
    ]),
    "Ualá Cuenta Plus Alta": json.dumps([
        {"min_amount": 0, "max_amount": 30000, "rate": 15.0, "condition": "Requiere consumo mínimo $6,000/mes"},
        {"min_amount": 30000.01, "max_amount": None, "rate": 0, "condition": "Sin rendimiento sobre excedente"}
    ]),
    "Ualá Cuenta": json.dumps([
        {"min_amount": 0, "max_amount": 30000, "rate": 6.75, "condition": "Tasa base sin requisito"},
    ]),
}

for name, tiers in tiered_data.items():
    cur.execute("UPDATE instruments SET tiered_rates = %s WHERE name = %s", (tiers, name))
    print(f"  {name}: tiered_rates updated")

c.commit()
print(f"  Done: {len(tiered_data)} instruments updated")

# ═══ TASK 7: Rename Trading course ═══════════════════════════════════════════
print("\n=== TASK 7: Renaming Trading course ===")

cur.execute(
    "UPDATE courses SET title = %s, description = %s WHERE id = 'fundamentos-trading'",
    (
        "Introducción al Análisis de Acciones",
        "Entiende cómo funcionan los mercados bursátiles, lee gráficas y conoce los conceptos básicos del análisis técnico. Curso educativo — Finalat no recomienda ni asesora la compra de acciones."
    )
)
print("  Course renamed: 'Introducción al Análisis de Acciones'")
print("  Description updated with educational disclaimer")

# Add disclaimer to first lesson content
cur.execute("SELECT id, content FROM lessons WHERE course_id = 'fundamentos-trading' AND sort_order = 1")
row = cur.fetchone()
if row:
    disclaimer = '<div class="lesson-guide"><h3>Aviso importante</h3><p>Este curso es <strong>exclusivamente educativo</strong>. Finalat no recomienda, asesora ni promueve la compra de acciones, ETFs ni instrumentos de renta variable. El contenido busca que entiendas cómo funciona el mercado para tomar decisiones informadas por tu cuenta.</p></div>'
    if 'Aviso importante' not in row[1]:
        cur.execute("UPDATE lessons SET content = %s WHERE id = %s", (disclaimer + row[1], row[0]))
        print(f"  Disclaimer added to lesson: {row[0]}")

c.commit()

# ═══ TASK 9: Verify tables exist (account_metadata + user_preferences) ═══════
print("\n=== TASK 9: Verifying DB tables ===")

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name IN ('account_metadata', 'user_preferences')
    ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]
print(f"  Tables found: {tables}")
if 'account_metadata' in tables:
    cur.execute("SELECT COUNT(*) FROM account_metadata")
    print(f"  account_metadata rows: {cur.fetchone()[0]}")
if 'user_preferences' in tables:
    cur.execute("SELECT COUNT(*) FROM user_preferences")
    print(f"  user_preferences rows: {cur.fetchone()[0]}")

# Note: These tables were created manually. For Alembic tracking, stamp them.
print("  Note: Tables created via direct SQL. Add to next Alembic migration for tracking.")

c.close()
print("\nAll tasks complete!")
