import sqlite3

DB_NAME = "eco_buddy.db"


def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transport TEXT,
                distance REAL,
                electricity REAL,
                diet TEXT,
                flights INTEGER,
                footprint REAL,
                eco_score INTEGER
            )
        """)

        conn.commit()
        conn.close()
        
        # Initialize and seed squads and multiplayer tables
        init_squads_db()
        seed_multiplayer_data()
        
        return True
    except sqlite3.Error as e:
        print(f"Database init error: {e}")
        return False


def save_assessment(
    transport,
    distance,
    electricity,
    diet,
    flights,
    footprint,
    eco_score
):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO assessments (
                transport,
                distance,
                electricity,
                diet,
                flights,
                footprint,
                eco_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transport,
            distance,
            electricity,
            diet,
            flights,
            footprint,
            eco_score
        ))

        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database save error: {e}")
        return False


def get_assessments():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM assessments
            ORDER BY date DESC
        """)

        data = cursor.fetchall()

        conn.close()
        return data
    except sqlite3.Error as e:
        print(f"Database read error: {e}")
        return []

def init_energy_db():
    try:
        conn = sqlite3.connect(DB_NAME)
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

def add_appliance(name, category, quantity, power_rating, hours_used, standby_draw):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appliances (user_id, name, category, quantity, power_rating_watts, hours_used_per_day, standby_draw_watts)
            VALUES (1, ?, ?, ?, ?, ?, ?)
        """, (name, category, quantity, power_rating, hours_used, standby_draw))
        conn.commit()
        conn.close()
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
        return True
    except sqlite3.Error as e:
        return False

def get_appliances():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appliances ORDER BY created_at DESC")
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error as e:
        return []

def save_solar_config(roof_space, peak_sun_hours, utility_rate, panel_efficiency, install_cost, maint_cost, rate_inc):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM solar_configs WHERE user_id = 1")
        
        cursor.execute("""
            INSERT INTO solar_configs (
                roof_space_m2, peak_sun_hours, utility_rate_per_kwh, panel_efficiency, 
                installation_cost_per_kw, maintenance_cost_per_year, annual_rate_increase
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (roof_space, peak_sun_hours, utility_rate, panel_efficiency, install_cost, maint_cost, rate_inc))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        return False

def get_solar_config():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM solar_configs WHERE user_id = 1 LIMIT 1")
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return None
    except sqlite3.Error as e:
        return None

def init_gamification_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
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
        return True
    except sqlite3.Error as e:
        print(f"complete_challenge error: {e}")
        return False
    finally:
        if conn:
            conn.close()

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
        elif source_type == 'badge':
            cursor.execute("UPDATE unlocked_badges SET xp_awarded = 1 WHERE user_id = ? AND badge_id = ?", (user_id, source_id))
            
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"award_xp error: {e}")
        return False
    finally:
        if conn:
            conn.close()

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
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"unlock_badge_in_db error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_unlocked_badges(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM unlocked_badges WHERE user_id = ?", (user_id,))
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return [dict(zip(columns, row)) for row in data]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()

def init_marketplace_db():
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
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
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO journey_profiles (user_id, name, distance_km, transport_mode, passenger_count, trips_per_week, is_commute)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, distance_km, transport_mode, passenger_count, trips_per_week, is_commute))
        
        conn.commit()
        return True
    except Exception as e:
        print(f'save_journey_profile error: {e}')
        return False
    finally:
        if conn:
            conn.close()

def get_journey_profiles(user_id):
    conn = None
    try:
        import sqlite3
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
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM journey_profiles WHERE id = ?', (profile_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def save_offset_transaction(user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status='completed'):
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offset_transactions (user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, project_id, project_name, offset_tonnes, cost_per_tonne, total_cost, transaction_status))
        
        conn.commit()
        return True
    except Exception as e:
        print(f'save_offset_transaction error: {e}')
        return False
    finally:
        if conn:
            conn.close()

def get_offset_transactions(user_id):
    conn = None
    try:
        import sqlite3
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
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM offset_transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def get_total_offsets(user_id):
    conn = None
    try:
        import sqlite3
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

def get_total_spend(user_id):
    conn = None
    try:
        import sqlite3
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
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
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
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO water_consumption (user_id, shower_mins_per_day, laundry_loads_per_week, dishwasher_runs_per_week, garden_mins_per_week, diet, total_liters)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, shower, laundry, dishwasher, garden, diet, total_liters))
        
        conn.commit()
        return True
    except Exception as e:
        print(f'save_water_assessment error: {e}')
        return False
    finally:
        if conn:
            conn.close()

def get_water_assessments(user_id):
    conn = None
    try:
        import sqlite3
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


def init_squads_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS squads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                owner_user_id INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS squad_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                squad_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(squad_id, user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_challenges (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                target_xp INTEGER NOT NULL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                reward_badge_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database squads init error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_or_create_user(username):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"get_or_create_user error: {e}")
        return 1
    finally:
        if conn:
            conn.close()


def get_username(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else f"User {user_id}"
    except sqlite3.Error:
        return f"User {user_id}"
    finally:
        if conn:
            conn.close()


def create_squad(name, description, owner_user_id):
    import uuid
    invite_code = f"SQ-{str(uuid.uuid4())[:6].upper()}"
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if user is already in a squad
        cursor.execute("SELECT squad_id FROM squad_memberships WHERE user_id = ?", (owner_user_id,))
        if cursor.fetchone():
            return None
            
        cursor.execute("""
            INSERT INTO squads (name, description, owner_user_id, invite_code)
            VALUES (?, ?, ?, ?)
        """, (name, description, owner_user_id, invite_code))
        squad_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO squad_memberships (squad_id, user_id)
            VALUES (?, ?)
        """, (squad_id, owner_user_id))
        
        conn.commit()
        return invite_code
    except sqlite3.Error as e:
        print(f"create_squad error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def join_squad_by_code(user_id, invite_code):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if user is already in a squad
        cursor.execute("SELECT squad_id FROM squad_memberships WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return False, "You are already a member of a squad. Leave your current squad first."
            
        cursor.execute("SELECT id FROM squads WHERE invite_code = ?", (invite_code,))
        row = cursor.fetchone()
        if not row:
            return False, "Invalid invite code."
            
        squad_id = row[0]
        cursor.execute("""
            INSERT INTO squad_memberships (squad_id, user_id)
            VALUES (?, ?)
        """, (squad_id, user_id))
        
        conn.commit()
        return True, "Successfully joined the squad!"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        if conn:
            conn.close()


def leave_squad(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT squad_id FROM squad_memberships WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        squad_id = row[0]
        
        # Check if user is owner
        cursor.execute("SELECT owner_user_id FROM squads WHERE id = ?", (squad_id,))
        owner_row = cursor.fetchone()
        is_owner = owner_row and owner_row[0] == user_id
        
        cursor.execute("DELETE FROM squad_memberships WHERE squad_id = ? AND user_id = ?", (squad_id, user_id))
        
        if is_owner:
            # Transfer ownership to another member or delete squad if empty
            cursor.execute("SELECT user_id FROM squad_memberships WHERE squad_id = ? ORDER BY joined_at ASC LIMIT 1", (squad_id,))
            next_member_row = cursor.fetchone()
            if next_member_row:
                cursor.execute("UPDATE squads SET owner_user_id = ? WHERE id = ?", (next_member_row[0], squad_id))
            else:
                cursor.execute("DELETE FROM squads WHERE id = ?", (squad_id,))
                
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        if conn:
            conn.close()


def get_squad_for_user(user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.name, s.invite_code, s.owner_user_id, s.description, s.created_at
            FROM squads s
            JOIN squad_memberships sm ON s.id = sm.squad_id
            WHERE sm.user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()


def get_squad_members(squad_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sm.user_id, u.username, sm.joined_at
            FROM squad_memberships sm
            JOIN users u ON sm.user_id = u.id
            WHERE sm.squad_id = ?
            ORDER BY sm.joined_at ASC
        """, (squad_id,))
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_squad_leaderboard():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.name, s.description, COALESCE(SUM(xp.xp_amount), 0) as total_xp
            FROM squads s
            LEFT JOIN squad_memberships sm ON s.id = sm.squad_id
            LEFT JOIN xp_transactions xp ON sm.user_id = xp.user_id
            GROUP BY s.id
            ORDER BY total_xp DESC
        """)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_active_monthly_challenges():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_challenges WHERE status = 'active'")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def seed_multiplayer_data():
    import datetime
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if users already seeded
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return
            
        # Seed users
        users = ["Alice", "Bob", "Charlie", "Dave", "Eve", "The Professor"]
        user_ids = []
        for u in users:
            cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (u,))
            cursor.execute("SELECT id FROM users WHERE username = ?", (u,))
            user_ids.append(cursor.fetchone()[0])
            
        # Seed XP transactions for users to show on leaderboard
        import random
        sources = [('challenge', 'c1', 50), ('challenge', 'c2', 40), ('badge', 'b1', 20), ('badge', 'b2', 50)]
        for uid in user_ids:
            for src_type, src_id, xp in random.sample(sources, k=3):
                cursor.execute("""
                    INSERT OR IGNORE INTO xp_transactions (user_id, source_type, source_id, xp_amount, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (uid, src_type, src_id, xp, f"Completed {src_id}"))

        # Seed some initial squads
        cursor.execute("""
            INSERT OR IGNORE INTO squads (id, name, invite_code, owner_user_id, description)
            VALUES 
            (1, 'Eco Warriors', 'WAR123', ?, 'Saving the planet one action at a time!'),
            (2, 'Green Team', 'GRN456', ?, 'Reducing footprint collectively.')
        """, (user_ids[0], user_ids[2]))
        
        # Seed memberships
        # Alice (1) is in Eco Warriors (1)
        cursor.execute("INSERT OR IGNORE INTO squad_memberships (squad_id, user_id) VALUES (1, ?)", (user_ids[0],))
        # Bob (2) is in Eco Warriors (1)
        cursor.execute("INSERT OR IGNORE INTO squad_memberships (squad_id, user_id) VALUES (1, ?)", (user_ids[1],))
        # Charlie (3) is in Green Team (2)
        cursor.execute("INSERT OR IGNORE INTO squad_memberships (squad_id, user_id) VALUES (2, ?)", (user_ids[2],))
        # Dave (4) is in Green Team (2)
        cursor.execute("INSERT OR IGNORE INTO squad_memberships (squad_id, user_id) VALUES (2, ?)", (user_ids[3],))
        
        # Seed monthly challenges
        today = datetime.date.today()
        start_of_month = datetime.date(today.year, today.month, 1).strftime('%Y-%m-%d')
        if today.month == 12:
            end_of_month = datetime.date(today.year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_of_month = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
        end_of_month_str = end_of_month.strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT OR REPLACE INTO monthly_challenges (id, title, description, target_xp, start_date, end_date, status, reward_badge_id)
            VALUES 
            ('mc1', 'July Carbon Diet', 'Earn a collective 200 XP as a squad to unlock the Challenge Champion badge.', 200, ?, ?, 'active', 'b3'),
            ('mc2', 'Zero Waste Journey', 'Earn a collective 300 XP as a squad to unlock the Plant-Based Week badge.', 300, ?, ?, 'active', 'b4')
        """, (start_of_month, end_of_month_str, start_of_month, end_of_month_str))

        conn.commit()
    except Exception as e:
        print(f"Error seeding multiplayer data: {e}")
    finally:
        if conn:
            conn.close()
