"""Add Revolut as an instrument."""
import psycopg2
import uuid

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# Check if Revolut already exists
cur.execute("SELECT id FROM instruments WHERE institution = 'Revolut'")
if cur.fetchone():
    print("Revolut already exists")
else:
    cur.execute("""
        INSERT INTO instruments (id, name, institution, instrument_type, annual_rate, min_investment, max_investment, term, term_days, risk_level, liquidity_tier, tiered_rates, requires_purchase, conditions, last_fetch_status, referral_link, signup_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        str(uuid.uuid4()),
        'Revolut Cuenta',
        'Revolut',
        'cuenta_ahorro',
        9.0,  # ~9% anual (varía, verificar)
        0.01,
        None,
        'liquid',
        None,
        'low',
        'immediate',
        '[{"min_amount": 0, "max_amount": null, "rate": 9.0, "condition": "Requiere 4 compras de $50+ al mes para tasa preferente"}]',
        True,
        'Requiere 4 compras de al menos $50 al mes con la tarjeta Revolut para obtener la tasa preferente.',
        'success',
        '',
        ''
    ))
    c.commit()
    print("Revolut added successfully")

c.close()
