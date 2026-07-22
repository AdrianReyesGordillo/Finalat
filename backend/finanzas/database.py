"""Database module for Financial Dashboard.

Supports PostgreSQL (via DATABASE_URL env var) for production and SQLite as fallback
for local development. All user-facing tables include a `user_id` column (Firebase UID)
to ensure data isolation between users.

When DATABASE_URL is set and points to a PostgreSQL database, all data is stored
persistently in PostgreSQL. Otherwise, a local SQLite file is used.
"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgres")

# Fix Render/Supabase "postgres://" → "postgresql://"
if USE_POSTGRES and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Add sslmode for cloud PostgreSQL if not present
if USE_POSTGRES and "sslmode" not in DATABASE_URL:
    if "?" in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
    else:
        DATABASE_URL += "?sslmode=require"

# SQLite fallback path
SQLITE_PATH = Path(__file__).parent.parent.parent / "data" / "financial.db"


class _PgCursorWrapper:
    """Wraps a psycopg2 cursor to provide sqlite3-compatible interface."""

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        # Convert ? placeholders to %s for PostgreSQL
        sql = sql.replace("?", "%s")

        # For INSERT statements, add RETURNING id to get lastrowid
        is_insert = sql.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " RETURNING id"

        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        self.rowcount = self._cursor.rowcount

        # Get lastrowid from RETURNING clause
        if is_insert:
            try:
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                self.lastrowid = None
        else:
            self.lastrowid = None

        return self

    def executescript(self, sql):
        """Execute multiple statements."""
        self._cursor.execute(sql)
        return self

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._cursor.description:
            cols = [desc[0] for desc in self._cursor.description]
            return [_DictRow(dict(zip(cols, row))) for row in rows]
        return rows

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._cursor.description:
            cols = [desc[0] for desc in self._cursor.description]
            return _DictRow(dict(zip(cols, row)))
        return row


class _DictRow(dict):
    """A dict that also supports index-based access like sqlite3.Row."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


class _PgConnectionWrapper:
    """Wraps a psycopg2 connection to provide sqlite3-compatible interface."""

    def __init__(self, conn):
        self._conn = conn
        self._cursor = None

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        wrapper = _PgCursorWrapper(cur)
        wrapper.execute(sql, params)
        return wrapper

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(sql)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_connection():
    """Get a database connection (PostgreSQL or SQLite)."""
    if USE_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return _PgConnectionWrapper(conn)
    else:
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema.

    All user-facing tables include user_id (Firebase UID) for per-user isolation.
    Uses dialect-appropriate DDL for PostgreSQL vs SQLite.
    """
    if USE_POSTGRES:
        _init_db_postgres()
    else:
        _init_db_sqlite()


def _init_db_postgres():
    """Create tables using PostgreSQL DDL."""
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ahorro (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                color TEXT DEFAULT '#1da1f2',
                balance TEXT DEFAULT '0',
                annual_rate DOUBLE PRECISION DEFAULT 0,
                rate_cap DOUBLE PRECISION DEFAULT 0,
                excess_rate DOUBLE PRECISION DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS prestamos (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                borrower TEXT NOT NULL,
                principal DOUBLE PRECISION DEFAULT 0,
                rate DOUBLE PRECISION DEFAULT 0,
                term TEXT DEFAULT '',
                status TEXT DEFAULT 'activo'
            );

            CREATE TABLE IF NOT EXISTS afore (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                balance TEXT DEFAULT '0',
                annual_return DOUBLE PRECISION DEFAULT 0,
                bimonthly_contribution TEXT DEFAULT '0',
                voluntary_contribution TEXT DEFAULT '0',
                UNIQUE(user_id)
            );

            CREATE TABLE IF NOT EXISTS creditos (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                color TEXT DEFAULT '#1da1f2',
                credit_limit TEXT DEFAULT '0',
                debt TEXT DEFAULT '0',
                available TEXT DEFAULT '0',
                cutoff_date TEXT DEFAULT '',
                payment_date TEXT DEFAULT '',
                minimum_payment TEXT DEFAULT '0',
                full_payment TEXT DEFAULT '0'
            );

            CREATE TABLE IF NOT EXISTS gastos_ingresos (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                fecha TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                categoria TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                monto TEXT DEFAULT '0'
            );

            CREATE TABLE IF NOT EXISTS deudas (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                nombre TEXT NOT NULL,
                deuda_total TEXT DEFAULT '0',
                pago_periodo TEXT DEFAULT '0',
                temporalidad TEXT DEFAULT 'mensual',
                dia_pago_1 INTEGER DEFAULT 1,
                dia_pago_2 INTEGER DEFAULT 0,
                pagos_restantes TEXT DEFAULT '0',
                fecha_inicio_1 TEXT DEFAULT '',
                fecha_inicio_2 TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS gbm_nacional (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                ticker TEXT NOT NULL,
                section TEXT DEFAULT '',
                shares DOUBLE PRECISION DEFAULT 0,
                avg_cost DOUBLE PRECISION DEFAULT 0,
                market_price DOUBLE PRECISION DEFAULT 0,
                market_value DOUBLE PRECISION DEFAULT 0,
                gain_loss DOUBLE PRECISION DEFAULT 0,
                return_pct DOUBLE PRECISION DEFAULT 0,
                var_day_pct DOUBLE PRECISION DEFAULT 0,
                portfolio_pct DOUBLE PRECISION DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS gbm_usa (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                ticker TEXT NOT NULL,
                section TEXT DEFAULT '',
                shares DOUBLE PRECISION DEFAULT 0,
                avg_cost DOUBLE PRECISION DEFAULT 0,
                market_price DOUBLE PRECISION DEFAULT 0,
                market_value DOUBLE PRECISION DEFAULT 0,
                gain_loss DOUBLE PRECISION DEFAULT 0,
                return_pct DOUBLE PRECISION DEFAULT 0,
                var_day_pct DOUBLE PRECISION DEFAULT 0,
                cost_value DOUBLE PRECISION DEFAULT 0,
                portfolio_pct DOUBLE PRECISION DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS update_tracker (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                section TEXT NOT NULL,
                last_update TEXT NOT NULL,
                UNIQUE(user_id, section)
            );

            CREATE TABLE IF NOT EXISTS aportaciones (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                status TEXT DEFAULT 'pendiente',
                person TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS aportaciones_config (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                amount TEXT DEFAULT '0',
                person TEXT DEFAULT '',
                color TEXT DEFAULT '#1da1f2',
                frequency TEXT DEFAULT 'semanal'
            );

            CREATE TABLE IF NOT EXISTS patrimonio_neto (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                month TEXT NOT NULL,
                value TEXT DEFAULT '0',
                UNIQUE(user_id, month)
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '',
                UNIQUE(user_id, key)
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                family_group_id INTEGER,
                started_at TEXT NOT NULL DEFAULT '',
                expires_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT '',
                UNIQUE(user_id)
            );

            CREATE TABLE IF NOT EXISTS family_groups (
                id SERIAL PRIMARY KEY,
                owner_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT 'Mi familia',
                invite_code TEXT NOT NULL DEFAULT '',
                max_members INTEGER NOT NULL DEFAULT 4,
                created_at TEXT NOT NULL DEFAULT '',
                UNIQUE(owner_id),
                UNIQUE(invite_code)
            );

            CREATE TABLE IF NOT EXISTS gi_categories (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                icon TEXT DEFAULT 'pi-tag',
                sort_order INTEGER DEFAULT 0,
                UNIQUE(user_id, name)
            );
        """)
        # Create indexes
        _create_indexes_pg(cur)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_indexes_pg(cur):
    """Create indexes for PostgreSQL."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_ahorro_user ON ahorro(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_prestamos_user ON prestamos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_afore_user ON afore(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_creditos_user ON creditos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gastos_ingresos_user ON gastos_ingresos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_deudas_user ON deudas(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gbm_nacional_user ON gbm_nacional(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gbm_usa_user ON gbm_usa(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_update_tracker_user ON update_tracker(user_id, section)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_user ON aportaciones(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_dates ON aportaciones(user_id, week_start, week_end)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_config_user ON aportaciones_config(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_patrimonio_neto_user ON patrimonio_neto(user_id, month)",
        # Prevent duplicate aportaciones records
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_aportaciones_unique ON aportaciones(user_id, category, COALESCE(person, ''), week_start)",
        "CREATE INDEX IF NOT EXISTS idx_gi_categories_user ON gi_categories(user_id)",
    ]
    for sql in indexes:
        cur.execute(sql)


def _migrate_pg_real_to_double():
    """Migrate REAL columns to DOUBLE PRECISION in PostgreSQL for monetary precision.

    REAL in PostgreSQL is 4-byte single-precision float (~7 digits precision),
    which causes rounding errors for decimal monetary values (e.g., 10.56 → 10.60).
    DOUBLE PRECISION is 8-byte (~15 digits precision) and preserves values correctly.

    Safe to call multiple times — ALTER TYPE is idempotent if already DOUBLE PRECISION.
    """
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()
        # Columns to migrate: table_name, column_name
        columns_to_migrate = [
            ("ahorro", "balance"),
            ("ahorro", "annual_rate"),
            ("ahorro", "rate_cap"),
            ("ahorro", "excess_rate"),
            ("prestamos", "principal"),
            ("prestamos", "rate"),
            ("afore", "balance"),
            ("afore", "annual_return"),
            ("afore", "bimonthly_contribution"),
            ("afore", "voluntary_contribution"),
            ("creditos", "credit_limit"),
            ("creditos", "debt"),
            ("creditos", "available"),
            ("creditos", "minimum_payment"),
            ("creditos", "full_payment"),
            ("gastos_ingresos", "monto"),
            ("deudas", "deuda_total"),
            ("deudas", "pago_periodo"),
            ("gbm_nacional", "shares"),
            ("gbm_nacional", "avg_cost"),
            ("gbm_nacional", "market_price"),
            ("gbm_nacional", "market_value"),
            ("gbm_nacional", "gain_loss"),
            ("gbm_nacional", "return_pct"),
            ("gbm_nacional", "var_day_pct"),
            ("gbm_nacional", "portfolio_pct"),
            ("gbm_usa", "shares"),
            ("gbm_usa", "avg_cost"),
            ("gbm_usa", "market_price"),
            ("gbm_usa", "market_value"),
            ("gbm_usa", "gain_loss"),
            ("gbm_usa", "return_pct"),
            ("gbm_usa", "var_day_pct"),
            ("gbm_usa", "cost_value"),
            ("gbm_usa", "portfolio_pct"),
            ("aportaciones_config", "amount"),
            ("patrimonio_neto", "value"),
        ]
        for table, column in columns_to_migrate:
            cur.execute(f"""
                ALTER TABLE {table}
                ALTER COLUMN {column} TYPE DOUBLE PRECISION
            """)
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def _init_db_sqlite():
    """Create tables using SQLite DDL (original implementation)."""
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ahorro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                color TEXT DEFAULT '#1da1f2',
                balance TEXT DEFAULT '0',
                annual_rate REAL DEFAULT 0,
                rate_cap REAL DEFAULT 0,
                excess_rate REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                borrower TEXT NOT NULL,
                principal REAL DEFAULT 0,
                rate REAL DEFAULT 0,
                term TEXT DEFAULT '',
                status TEXT DEFAULT 'activo'
            );

            CREATE TABLE IF NOT EXISTS afore (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                balance TEXT DEFAULT '0',
                annual_return REAL DEFAULT 0,
                bimonthly_contribution TEXT DEFAULT '0',
                voluntary_contribution TEXT DEFAULT '0',
                UNIQUE(user_id)
            );

            CREATE TABLE IF NOT EXISTS creditos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                color TEXT DEFAULT '#1da1f2',
                credit_limit TEXT DEFAULT '0',
                debt TEXT DEFAULT '0',
                available TEXT DEFAULT '0',
                cutoff_date TEXT DEFAULT '',
                payment_date TEXT DEFAULT '',
                minimum_payment TEXT DEFAULT '0',
                full_payment TEXT DEFAULT '0'
            );

            CREATE TABLE IF NOT EXISTS gastos_ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                fecha TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                categoria TEXT DEFAULT '',
                tipo TEXT DEFAULT '',
                monto TEXT DEFAULT '0'
            );

            CREATE TABLE IF NOT EXISTS deudas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                nombre TEXT NOT NULL,
                deuda_total TEXT DEFAULT '0',
                pago_periodo TEXT DEFAULT '0',
                temporalidad TEXT DEFAULT 'mensual',
                dia_pago_1 INTEGER DEFAULT 1,
                dia_pago_2 INTEGER DEFAULT 0,
                pagos_restantes TEXT DEFAULT '0',
                fecha_inicio_1 TEXT DEFAULT '',
                fecha_inicio_2 TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS gbm_nacional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                ticker TEXT NOT NULL,
                section TEXT DEFAULT '',
                shares REAL DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                market_price REAL DEFAULT 0,
                market_value REAL DEFAULT 0,
                gain_loss REAL DEFAULT 0,
                return_pct REAL DEFAULT 0,
                var_day_pct REAL DEFAULT 0,
                portfolio_pct REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS gbm_usa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                ticker TEXT NOT NULL,
                section TEXT DEFAULT '',
                shares REAL DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                market_price REAL DEFAULT 0,
                market_value REAL DEFAULT 0,
                gain_loss REAL DEFAULT 0,
                return_pct REAL DEFAULT 0,
                var_day_pct REAL DEFAULT 0,
                cost_value REAL DEFAULT 0,
                portfolio_pct REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS update_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                section TEXT NOT NULL,
                last_update TEXT NOT NULL,
                UNIQUE(user_id, section)
            );

            CREATE TABLE IF NOT EXISTS aportaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                status TEXT DEFAULT 'pendiente',
                person TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS aportaciones_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                amount TEXT DEFAULT '0',
                person TEXT DEFAULT '',
                color TEXT DEFAULT '#1da1f2',
                frequency TEXT DEFAULT 'semanal'
            );

            CREATE TABLE IF NOT EXISTS patrimonio_neto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                month TEXT NOT NULL,
                value TEXT DEFAULT '0',
                UNIQUE(user_id, month)
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '',
                UNIQUE(user_id, key)
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                family_group_id INTEGER,
                started_at TEXT NOT NULL DEFAULT '',
                expires_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT '',
                UNIQUE(user_id)
            );

            CREATE TABLE IF NOT EXISTS family_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT 'Mi familia',
                invite_code TEXT NOT NULL DEFAULT '',
                max_members INTEGER NOT NULL DEFAULT 4,
                created_at TEXT NOT NULL DEFAULT '',
                UNIQUE(owner_id),
                UNIQUE(invite_code)
            );

            CREATE TABLE IF NOT EXISTS gi_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                name TEXT NOT NULL,
                icon TEXT DEFAULT 'pi-tag',
                sort_order INTEGER DEFAULT 0,
                UNIQUE(user_id, name)
            );
        """)


def _create_indexes(conn):
    """Create indexes on user_id columns for performance."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_ahorro_user ON ahorro(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_prestamos_user ON prestamos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_afore_user ON afore(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_creditos_user ON creditos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gastos_ingresos_user ON gastos_ingresos(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_deudas_user ON deudas(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gbm_nacional_user ON gbm_nacional(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_gbm_usa_user ON gbm_usa(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_update_tracker_user ON update_tracker(user_id, section)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_user ON aportaciones(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_dates ON aportaciones(user_id, week_start, week_end)",
        "CREATE INDEX IF NOT EXISTS idx_aportaciones_config_user ON aportaciones_config(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_patrimonio_neto_user ON patrimonio_neto(user_id, month)",
        "CREATE INDEX IF NOT EXISTS idx_gi_categories_user ON gi_categories(user_id)",
    ]
    for sql in indexes:
        conn.execute(sql)


def migrate_db():
    """Run migrations to add user_id columns to existing tables.

    Safe to call multiple times — uses IF NOT EXISTS / checks before altering.
    For PostgreSQL, the schema is created fresh via init_db so migrations are skipped
    except for column type migrations.
    """
    if USE_POSTGRES:
        # Migrate REAL columns to DOUBLE PRECISION for monetary precision
        _migrate_pg_real_to_double()
        return

    tables_needing_user_id = [
        "ahorro", "prestamos", "creditos", "gastos_ingresos",
        "deudas", "gbm_nacional", "gbm_usa", "aportaciones",
        "aportaciones_config", "patrimonio_neto",
    ]

    with get_db() as conn:
        for table in tables_needing_user_id:
            # Check if user_id column exists
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")

        # update_tracker: change primary key scheme (section -> user_id + section)
        cursor = conn.execute("PRAGMA table_info(update_tracker)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            # Recreate with new schema
            conn.executescript("""
                ALTER TABLE update_tracker RENAME TO update_tracker_old;
                CREATE TABLE update_tracker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT '',
                    section TEXT NOT NULL,
                    last_update TEXT NOT NULL,
                    UNIQUE(user_id, section)
                );
                INSERT INTO update_tracker (user_id, section, last_update)
                    SELECT '', section, last_update FROM update_tracker_old;
                DROP TABLE update_tracker_old;
            """)

        # afore: change from id=1 to user_id unique
        cursor = conn.execute("PRAGMA table_info(afore)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            conn.executescript("""
                ALTER TABLE afore RENAME TO afore_old;
                CREATE TABLE afore (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    balance REAL DEFAULT 0,
                    annual_return REAL DEFAULT 0,
                    bimonthly_contribution REAL DEFAULT 0,
                    voluntary_contribution REAL DEFAULT 0,
                    UNIQUE(user_id)
                );
                INSERT INTO afore (user_id, balance, annual_return, bimonthly_contribution, voluntary_contribution)
                    SELECT '', balance, annual_return, bimonthly_contribution, voluntary_contribution FROM afore_old;
                DROP TABLE afore_old;
            """)

        # patrimonio_neto: add UNIQUE(user_id, month)
        cursor = conn.execute("PRAGMA table_info(patrimonio_neto)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" in columns:
            pass

        # aportaciones_config: add frequency column
        cursor = conn.execute("PRAGMA table_info(aportaciones_config)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "frequency" not in columns:
            conn.execute("ALTER TABLE aportaciones_config ADD COLUMN frequency TEXT DEFAULT 'semanal'")

        # Indexes
        _create_indexes(conn)
