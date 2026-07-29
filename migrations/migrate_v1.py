"""
Migration v1: Initial schema with all core tables.

This migration creates all the basic tables for the EcoBuddy AI application.
It's designed to be idempotent - tables are created with IF NOT EXISTS
to allow re-running without errors.
"""

import sqlite3


def migrate(conn):
    """
    Apply migration v1: Create initial schema.
    
    Creates tables:
    - assessments: Carbon footprint assessments
    - users: User authentication
    - appliances: Home appliance energy tracking
    - solar_configs: Solar panel configuration
    - user_challenges: Gamification challenges
    - unlocked_badges: Achievement badges
    - xp_transactions: XP history
    - skill_tree_progress: Skill tree progress
    - journey_profiles: Route planning profiles
    - offset_transactions: Carbon offset transactions
    - water_consumption: Water usage tracking
    """
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
    
    # Create assessments table
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
            eco_score INTEGER
        )
    """)
    
    # Create appliances table
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
    
    # Create solar_configs table
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
    
    # Create user_challenges table
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
    
    # Create unlocked_badges table
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
    
    # Create xp_transactions table
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
    
    # Create skill_tree_progress table
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
    
    # Create journey_profiles table
    cursor.execute("""
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
    """)
    
    # Create offset_transactions table
    cursor.execute("""
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
    """)
    
    # Create water_consumption table
    cursor.execute("""
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
    """)
    
    conn.commit()
