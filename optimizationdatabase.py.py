"""
Smart Household Resource Optimization Engine - Database Operations
Database handlers for optimization data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from optimization.models import (
    HouseholdResource, OptimizationPlan, OptimizationTarget,
    OptimizationProgress, ResourceType, ResourceCategory
)

logger = logging.getLogger(__name__)


class OptimizationDatabase:
    """
    Database handler for optimization operations.
    """
    
    def __init__(self, db_path: str = 'ecobuddy.db'):
        """Initialize the database handler."""
        self.db_path = db_path
        self._initialize_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def _initialize_tables(self) -> None:
        """Create optimization tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Resources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_resources (
                    id TEXT PRIMARY KEY,
                    household_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    unit TEXT,
                    current_usage REAL,
                    baseline_usage REAL,
                    cost_per_unit REAL,
                    efficiency_score REAL,
                    efficiency_grade TEXT,
                    optimization_potential REAL,
                    estimated_savings REAL,
                    consumption_pattern TEXT,
                    last_updated TEXT,
                    notes TEXT,
                    tags TEXT
                )
            ''')
            
            # Optimization plans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_plans (
                    id TEXT PRIMARY KEY,
                    household_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    overall_progress REAL,
                    completed_actions INTEGER,
                    total_actions INTEGER,
                    estimated_savings REAL,
                    achieved_savings REAL,
                    created_at TEXT,
                    updated_at TEXT,
                    start_date TEXT,
                    target_completion_date TEXT,
                    actual_completion_date TEXT,
                    notes TEXT
                )
            ''')
            
            # Optimization targets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_targets (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    target_value REAL,
                    current_value REAL,
                    unit TEXT,
                    deadline TEXT,
                    achieved INTEGER,
                    achieved_date TEXT,
                    FOREIGN KEY (plan_id) REFERENCES optimization_plans (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_resources_household ON optimization_resources(household_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_resources_type ON optimization_resources(resource_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_plans_household ON optimization_plans(household_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_plans_status ON optimization_plans(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_targets_plan ON optimization_targets(plan_id)')
            
            conn.commit()
            logger.info("Optimization tables initialized successfully")
    
    def save_resource(self, resource: HouseholdResource) -> str:
        """Save a resource to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO optimization_resources (
                    id, household_id, resource_type, category, name, description,
                    unit, current_usage, baseline_usage, cost_per_unit,
                    efficiency_score, efficiency_grade, optimization_potential,
                    estimated_savings, consumption_pattern, last_updated,
                    notes, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resource.id, resource.household_id, resource.resource_type.value,
                resource.category.value, resource.name, resource.description,
                resource.unit, resource.current_usage, resource.baseline_usage,
                resource.cost_per_unit, resource.efficiency_score,
                resource.efficiency_grade.value, resource.optimization_potential,
                resource.estimated_savings, resource.consumption_pattern.value,
                resource.last_updated.isoformat(), resource.notes,
                json.dumps(resource.tags)
            ))
            
            conn.commit()
            return resource.id
    
    def save_plan(self, plan: OptimizationPlan) -> str:
        """Save an optimization plan to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO optimization_plans (
                    id, household_id, name, description, status,
                    overall_progress, completed_actions, total_actions,
                    estimated_savings, achieved_savings, created_at,
                    updated_at, start_date, target_completion_date,
                    actual_completion_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.id, plan.household_id, plan.name, plan.description,
                plan.status.value, plan.overall_progress, plan.completed_actions,
                plan.total_actions, plan.estimated_savings, plan.achieved_savings,
                plan.created_at.isoformat(), plan.updated_at.isoformat(),
                plan.start_date.isoformat() if plan.start_date else None,
                plan.target_completion_date.isoformat() if plan.target_completion_date else None,
                plan.actual_completion_date.isoformat() if plan.actual_completion_date else None,
                plan.notes
            ))
            
            # Save targets
            cursor.execute('DELETE FROM optimization_targets WHERE plan_id = ?', (plan.id,))
            for target in plan.targets:
                cursor.execute('''
                    INSERT INTO optimization_targets (
                        id, plan_id, category, target_value, current_value,
                        unit, deadline, achieved, achieved_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    target.id, plan.id, target.category.value,
                    target.target_value, target.current_value,
                    target.unit, target.deadline.isoformat() if target.deadline else None,
                    1 if target.achieved else 0,
                    target.achieved_date.isoformat() if target.achieved_date else None
                ))
            
            conn.commit()
            return plan.id