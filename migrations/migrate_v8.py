"""Migration v8: add time capsule and carbon credit marketplace simulation tables."""

import sqlite3


def migrate(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # --- Eco Time Capsule ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_capsules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            promise_text TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            unlock_date TEXT NOT NULL,
            is_unlocked INTEGER DEFAULT 0,
            unlocked_at TIMESTAMP,
            progress_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_time_capsules_user
        ON time_capsules(user_id, unlock_date DESC)
    """)

    # --- Carbon Credit Marketplace Simulation ---
    cursor.execute("PRAGMA table_info(carbon_credits)")
    if not cursor.fetchall():
        cursor.execute("""
            CREATE TABLE carbon_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                serial_no TEXT UNIQUE NOT NULL,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                vintage_year INTEGER NOT NULL,
                quantity REAL NOT NULL DEFAULT 1.0,
                status TEXT NOT NULL DEFAULT 'issued'
                    CHECK(status IN ('issued','listed','traded','retired')),
                source TEXT NOT NULL DEFAULT 'offset_purchase'
                    CHECK(source IN ('offset_purchase','challenge_reward','assessment_bonus','trade')),
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retired_at TIMESTAMP,
                retired_for TEXT,
                UNIQUE(serial_no)
            )
        """)

        cursor.execute("""
            CREATE INDEX idx_credits_user
            ON carbon_credits(user_id, status)
        """)

    cursor.execute("PRAGMA table_info(credit_trades)")
    if not cursor.fetchall():
        cursor.execute("""
            CREATE TABLE credit_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                price_per_tonne REAL NOT NULL,
                total_value REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed'
                    CHECK(status IN ('completed','cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(credit_id) REFERENCES carbon_credits(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX idx_trades_seller
            ON credit_trades(seller_id)
        """)
        cursor.execute("""
            CREATE INDEX idx_trades_buyer
            ON credit_trades(buyer_id)
        """)

    cursor.execute("PRAGMA table_info(market_state)")
    if not cursor.fetchall():
        cursor.execute("""
            CREATE TABLE market_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price_per_tonne REAL NOT NULL DEFAULT 25.0,
                volatility REAL NOT NULL DEFAULT 0.05,
                total_supply REAL NOT NULL DEFAULT 10000.0,
                total_demand REAL NOT NULL DEFAULT 5000.0,
                trading_volume REAL NOT NULL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO market_state (price_per_tonne, volatility, total_supply, total_demand)
            VALUES (25.0, 0.05, 10000.0, 5000.0)
        """)

    cursor.execute("PRAGMA table_info(user_eco_balance)")
    if not cursor.fetchall():
        cursor.execute("""
            CREATE TABLE user_eco_balance (
                user_id INTEGER PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 1000.0,
                lifetime_earned REAL NOT NULL DEFAULT 1000.0,
                lifetime_spent REAL NOT NULL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO user_eco_balance (user_id, balance, lifetime_earned)
            VALUES (1, 1000.0, 1000.0)
        """)

    conn.commit()
