"""Task 4: Add referral_link and signup_link columns to instruments."""
import psycopg2

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# Add columns if they don't exist
cur.execute("""
    ALTER TABLE instruments ADD COLUMN IF NOT EXISTS referral_link TEXT DEFAULT '';
    ALTER TABLE instruments ADD COLUMN IF NOT EXISTS signup_link TEXT DEFAULT '';
""")
c.commit()

# Verify
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'instruments' AND column_name IN ('referral_link', 'signup_link')")
cols = [r[0] for r in cur.fetchall()]
print(f"Columns added: {cols}")
c.close()
