"""Create account_metadata table in RDS for persisting colors and config."""
import psycopg2

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS account_metadata (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(128) NOT NULL,
        table_name VARCHAR(50) NOT NULL,
        record_id VARCHAR(36) NOT NULL,
        meta_key VARCHAR(50) NOT NULL,
        meta_value TEXT NOT NULL,
        UNIQUE(user_id, table_name, record_id, meta_key)
    );
    CREATE INDEX IF NOT EXISTS idx_acct_meta_user ON account_metadata(user_id, table_name);
""")

# Also create user_preferences table for panel toggles
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(128) NOT NULL,
        key VARCHAR(100) NOT NULL,
        value TEXT NOT NULL,
        UNIQUE(user_id, key)
    );
    CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_preferences(user_id);
""")

c.commit()
print("Tables created: account_metadata, user_preferences")
c.close()
