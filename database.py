import os
import sqlite3
from cache import cached
from cache_config import TTL_DB_READ, CACHE_CATEGORY_DB_READS
from invalidation import (
    invalidate_on_assessment_save,
    invalidate_on_appliance_change,
    invalidate_on_solar_config_save,
    invalidate_on_challenge_enroll,
    invalidate_on_challenge_progress,
    invalidate_on_challenge_complete,
    invalidate_on_xp_award,
    invalidate_on_badge_unlock,
    invalidate_on_skill_tree_update,
    invalidate_on_journey_save,
    invalidate_on_journey_delete,
    invalidate_on_offset_save,
    invalidate_on_offset_delete,
    invalidate_on_offset_clear,
    invalidate_on_water_assessment_save,
)
import streamlit as st
import bcrypt

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")


def get_db_version(conn):
    """Get the current database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    return cursor.fetchone()[0]


def set_db_version(conn, version):
    """Set the database schema version using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA user_version = {version}")
    conn.commit()


def migrate():
    """
    Apply pending database migrations.
    
    This function is called on application startup to ensure the database
    schema is up to date. It should be called once before any other
    database operations.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Import migrations module to get version info
    import migrations
    
    try:
        conn = sqlite3.connect(DB_NAME)
        current_version = get_db_version(conn)
        
        if current_version >= migrations.CURRENT_VERSION:
            conn.close()
            return True, f"Database is already at version {current_version}"
        
        # Apply migrations sequentially
        migrations_to_apply = range(current_version + 1, migrations.CURRENT_VERSION + 1)
        for version in migrations_to_apply:
            migration_file = f"migrations/migrate_v{version}.py"
            if os.path.exists(migration_file):
                module = __import__(f"migrations.migrate_v{version}", fromlist=['migrate'])
                if hasattr(module, 'migrate'):
                    module.migrate(conn)
                    set_db_version(conn, version)
                    print(f"Applied migration v{version}")
        
        conn.close()
        return True, f"Database migrated to version {migrations.CURRENT_VERSION}"
        
    except Exception as e:
        return False, f"Migration failed: {str(e)}"


def init_db():
    """
    Initialize the database with core tables.
    
    This function should only be called once during application startup,
    BEFORE any other database operations. It will automatically run
    pending migrations if the database exists but is outdated.
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Run migrations first to ensure schema is up to date
        migrate()
        
        # For new databases (version 0), create all tables
        current_version = get_db_version(conn)
        if current_version == 0:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create assessments table with trip_id
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transport TEXT,
                    distance REAL,
                    electricity REAL,
                    diet TEXT,
                    flights INTEGER,
                    footprint REAL,
                    eco_score INTEGER,
                    trip_id TEXT
                )
            """)
            
            # Create unique index on trip_id (NULL-safe)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_assessments_trip_id 
                ON assessments(trip_id) 
                WHERE trip_id IS NOT NULL
            """)
            
            conn.commit()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_drafts (
                user_id INTEGER PRIMARY KEY,
                transport TEXT,
                distance REAL,
                electricity REAL,
                diet TEXT,
                flights INTEGER,
                region TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database init error: {e}")
        return False


def create_user(username, email, password):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_user(username, password):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            return {"id": user[0], "username": user[1]}
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_username(username):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "username": user[1], "email": user[2]}
        return None
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()

def save_assessment(
    user_id,
    transport,
    distance,
    electricity,
    diet,
    flights,
    footprint,
    eco_score,
    trip_id=None
    trip_id=None,
    date=None
):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assessments (

        if date is not None:
            cursor.execute("""
                INSERT INTO assessments (
                    user_id,
                    date,
                    transport,
                    distance,
                    electricity,
                    diet,
                    flights,
                    footprint,
                    eco_score,
                    trip_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                date,
                transport,
                distance,
                electricity,
                diet,
                flights,
                footprint,
                eco_score,
                trip_id
            ))
        elif trip_id is not None:
            cursor.execute("""
                INSERT INTO assessments (
                    user_id,
                    transport,
                    distance,
                    electricity,
                    diet,
                    flights,
                    footprint,
                    eco_score,
                    trip_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                transport,
                distance,
                electricity,
                diet,
                flights,
                footprint,
                eco_score,
                trip_id
            ))
        else:
            cursor.execute("""
                INSERT INTO assessments (
                    user_id,
                    transport,
                    distance,
                    electricity,
                    diet,
                    flights,
                    footprint,
                    eco_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                transport,
                distance,
                electricity,
                diet,
                flights,
                footprint,
                eco_score,
                trip_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            transport,
            distance,
            electricity,
            diet,
            flights,
            footprint,
            eco_score,
            trip_id
        ))
                eco_score
            ))

        conn.commit()
        conn.close()
        invalidate_on_assessment_save()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Database save error: {e}")
        return False


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_assessments(user_id=1):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, date, transport, distance, electricity, diet, flights, footprint, eco_score
            FROM assessments
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
        """, (user_id,))

        data = cursor.fetchall()

        conn.close()
        return data
    except sqlite3.Error as e:
        print(f"Database read error: {e}")
        return []


def get_diet_history(user_id, limit=7):
def save_assessment_draft(user_id, transport, distance, electricity, diet, flights, region):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM assessment_drafts WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE assessment_drafts
                SET transport = ?, distance = ?, electricity = ?, diet = ?, flights = ?, region = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (transport, distance, electricity, diet, flights, region, user_id))
        else:
            cursor.execute("""
                INSERT INTO assessment_drafts (user_id, transport, distance, electricity, diet, flights, region)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, transport, distance, electricity, diet, flights, region))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database draft save error: {e}")
        return False


def get_assessment_draft(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, diet FROM assessments
            ORDER BY date DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.Error as e:
        print(f"get_diet_history error: {e}")
        return []
            SELECT transport, distance, electricity, diet, flights, region
            FROM assessment_drafts
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "transport": row[0],
                "distance": row[1],
                "electricity": row[2],
                "diet": row[3],
                "flights": row[4],
                "region": row[5]
            }
        return None
    except sqlite3.Error as e:
        print(f"Database draft read error: {e}")
        return None


def delete_assessment_draft(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assessment_drafts WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database draft delete error: {e}")
        return False


def init_energy_db():
    """
    Initialize energy-related tables (appliances, solar_configs).
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Run migrations to ensure schema is up to date
        migrate()
        
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                name TEXT,
                category TEXT,
                quantity INTEGER,
                power_rating_watts REAL,
                hours_used_per_day REAL,
                standby_draw_watts REAL,
                usage_schedule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solar_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                roof_space_m2 REAL,
                peak_sun_hours REAL,
                utility_rate_per_kwh REAL,
                panel_efficiency REAL,
                installation_cost_per_kw REAL,
                maintenance_cost_per_year REAL,
                annual_rate_increase REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database energy init error: {e}")
        return False


def add_appliance(user_id, name, category, quantity, power_rating, hours_used, standby_draw):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appliances (user_id, name, category, quantity, power_rating_watts, hours_used_per_day, standby_draw_watts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, category, quantity, power_rating, hours_used, standby_draw))
        conn.commit()
        conn.close()
        invalidate_on_appliance_change()
        return True
    except sqlite3.Error as e:
        print(f"Appliance save error: {e}")
        return False


def delete_appliance(app_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appliances WHERE id = ?", (app_id,))
        conn.commit()
        conn.close()
        invalidate_on_appliance_change()
        return True
    except sqlite3.Error as e:
        return False


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_appliances(user_id=1):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appliances WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error as e:
        return []


def save_solar_config(user_id, roof_space, peak_sun_hours, utility_rate, panel_efficiency, install_cost, maint_cost, rate_inc):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM solar_configs WHERE user_id = ?", (user_id,))
        
        cursor.execute("""
            INSERT INTO solar_configs (
                user_id, roof_space_m2, peak_sun_hours, utility_rate_per_kwh, panel_efficiency, 
                installation_cost_per_kw, maintenance_cost_per_year, annual_rate_increase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, roof_space, peak_sun_hours, utility_rate, panel_efficiency, install_cost, maint_cost, rate_inc))
        conn.commit()
        conn.close()
        invalidate_on_solar_config_save()
        return True
    except sqlite3.Error as e:
        return False


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_solar_config(user_id=1):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM solar_configs WHERE user_id = ? LIMIT 1", (user_id,))
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return None
    except sqlite3.Error as e:
        return None


def init_gamification_db():
    """
    Initialize gamification-related tables.
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Run migrations to ensure schema is up to date
        migrate()
        
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                challenge_id TEXT NOT NULL,
                progress_value REAL DEFAULT 0.0,
                status TEXT DEFAULT 'enrolled',
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                xp_awarded BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                badge_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_awarded BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, badge_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS xp_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                xp_amount INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, source_type, source_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_xp_user ON xp_transactions(user_id)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_tree_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                node_id TEXT NOT NULL,
                status TEXT DEFAULT 'Locked',
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, node_id)
            )
        """)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database gamification init error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def enroll_challenge(user_id, challenge_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM user_challenges WHERE user_id=? AND challenge_id=? AND status != 'expired'", (user_id, challenge_id))
        if cursor.fetchone():
            return False
            
        cursor.execute("""
            INSERT INTO user_challenges (user_id, challenge_id, status)
            VALUES (?, ?, 'enrolled')
        """, (user_id, challenge_id))
        conn.commit()
        invalidate_on_challenge_enroll()
        return True
    except sqlite3.Error as e:
        print(f"enroll_challenge error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def update_challenge_progress(user_id, challenge_id, progress_increment=None, set_progress=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if progress_increment is not None:
            cursor.execute("""
                UPDATE user_challenges 
                SET progress_value = progress_value + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND challenge_id = ? AND status = 'enrolled'
            """, (progress_increment, user_id, challenge_id))
        elif set_progress is not None:
             cursor.execute("""
                UPDATE user_challenges 
                SET progress_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND challenge_id = ? AND status = 'enrolled'
            """, (set_progress, user_id, challenge_id))
            
        conn.commit()
        invalidate_on_challenge_enroll()
        return True
    except sqlite3.Error as e:
        print(f"update_challenge_progress error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def complete_challenge(user_id, challenge_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_challenges 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND challenge_id = ? AND status = 'enrolled'
        """, (user_id, challenge_id))
        
        conn.commit()
        invalidate_on_challenge_enroll()
        return True
    except sqlite3.Error as e:
        print(f"complete_challenge error: {e}")
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_user_challenges(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_challenges WHERE user_id = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error as e:
        return []
    finally:
        if conn:
            conn.close()


def award_xp(user_id, source_type, source_id, xp_amount, description):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO xp_transactions (user_id, source_type, source_id, xp_amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, source_type, source_id, xp_amount, description))
        
        if source_type == 'challenge':
            cursor.execute("UPDATE user_challenges SET xp_awarded = 1 WHERE user_id = ? AND challenge_id = ?", (user_id, source_id))
            invalidate_on_challenge_enroll()
        elif source_type == 'badge':
            cursor.execute("UPDATE unlocked_badges SET xp_awarded = 1 WHERE user_id = ? AND badge_id = ?", (user_id, source_id))
            invalidate_on_badge_unlock()
            
        conn.commit()
        invalidate_on_xp_award()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"award_xp error: {e}")
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_total_xp(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(xp_amount) FROM xp_transactions WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0]
        return total if total else 0
    except sqlite3.Error:
        return 0
    finally:
        if conn:
            conn.close()


def unlock_badge_in_db(user_id, badge_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO unlocked_badges (user_id, badge_id)
            VALUES (?, ?)
        """, (user_id, badge_id))
        
        conn.commit()
        invalidate_on_badge_unlock()
        invalidate_on_xp_award()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"unlock_badge_in_db error: {e}")
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_unlocked_badges(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM unlocked_badges WHERE user_id = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error as e:
        return []
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_skill_tree_progress(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM skill_tree_progress WHERE user_id = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error as e:
        return []
    finally:
        if conn:
            conn.close()


def update_skill_node_status(user_id, node_id, status):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM skill_tree_progress WHERE user_id=? AND node_id=?", (user_id, node_id))
        if cursor.fetchone():
            if status == 'Completed':
                cursor.execute("""
                    UPDATE skill_tree_progress 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND node_id = ?
                """, (status, user_id, node_id))
            else:
                cursor.execute("""
                    UPDATE skill_tree_progress 
                    SET status = ?
                    WHERE user_id = ? AND node_id = ?
                """, (status, user_id, node_id))
        else:
            if status == 'Completed':
                cursor.execute("""
                    INSERT INTO skill_tree_progress (user_id, node_id, status, completed_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, node_id, status))
            else:
                cursor.execute("""
                    INSERT INTO skill_tree_progress (user_id, node_id, status)
                    VALUES (?, ?, ?)
                """, (user_id, node_id, status))
                
        conn.commit()
        invalidate_on_skill_tree_update()
        return True
    except sqlite3.Error as e:
        print(f"update_skill_node_status error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def init_marketplace_db():
    """
    Initialize marketplace-related tables (journey_profiles, offset_transactions).
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Run migrations to ensure schema is up to date
        migrate()
        
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journey_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                name TEXT NOT NULL,
                distance_km REAL NOT NULL,
                transport_mode TEXT NOT NULL,
                passenger_count INTEGER DEFAULT 1,
                trips_per_week INTEGER DEFAULT 1,
                is_commute BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offset_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                offset_tonnes REAL NOT NULL,
                cost_per_tonne REAL NOT NULL,
                total_cost REAL NOT NULL,
                transaction_status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        return True
    except Exception as e:
        print(f'Database marketplace init error: {e}')
        return False
    finally:
        if conn:
            conn.close()


def save_journey_profile(user_id, name, distance_km, transport_mode, passenger_count, trips_per_week, is_commute):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO journey_profiles (user_id, name, distance_km, transport_mode, passenger_count, trips_per_week, is_commute)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, distance_km, transport_mode, passenger_count, trips_per_week, is_commute))
        
        conn.commit()
        invalidate_on_journey_save()
        return True
    except Exception as e:
        print(f'save_journey_profile error: {e}')
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_journey_profiles(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM journey_profiles WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()


def delete_journey_profile(profile_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM journey_profiles WHERE id = ?', (profile_id,))
        conn.commit()
        invalidate_on_journey_save()
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


def save_offset_transaction(user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status='completed'):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offset_transactions (user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status))
        
        conn.commit()
        invalidate_on_offset_save()
        return True
    except Exception as e:
        print(f'save_offset_transaction error: {e}')
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_offset_transactions(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM offset_transactions WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()


def delete_offset_transaction(transaction_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM offset_transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        invalidate_on_offset_save()
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


def clear_offset_transactions(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM offset_transactions WHERE user_id = ?', (user_id,))
        conn.commit()
        invalidate_on_offset_save()
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_total_offsets(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(offset_tonnes) FROM offset_transactions WHERE user_id = ? AND transaction_status != "reversed"', (user_id,))
        total = cursor.fetchone()[0]
        return total if total else 0.0
    except Exception:
        return 0.0
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_total_spend(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(total_cost) FROM offset_transactions WHERE user_id = ? AND transaction_status != "reversed"', (user_id,))
        total = cursor.fetchone()[0]
        return total if total else 0.0
    except Exception:
        return 0.0
    finally:
        if conn:
            conn.close()


def init_water_db():
    """
    Initialize water consumption table.
    
    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # Run migrations to ensure schema is up to date
        migrate()
        
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_consumption (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                shower_mins_per_day REAL,
                laundry_loads_per_week REAL,
                dishwasher_runs_per_week REAL,
                garden_mins_per_week REAL,
                diet TEXT,
                total_liters REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return True
    except Exception as e:
        print(f'Database water init error: {e}')
        return False
    finally:
        if conn:
            conn.close()


def save_water_assessment(user_id, shower, laundry, dishwasher, garden, diet, total_liters):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO water_consumption (user_id, shower_mins_per_day, laundry_loads_per_week, dishwasher_runs_per_week, garden_mins_per_week, diet, total_liters)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, shower, laundry, dishwasher, garden, diet, total_liters))
        
        conn.commit()
        invalidate_on_water_assessment_save()
        return True
    except Exception as e:
        print(f'save_water_assessment error: {e}')
        return False
    finally:
        if conn:
            conn.close()


@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_water_assessments(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM water_consumption WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()
            conn.close()
