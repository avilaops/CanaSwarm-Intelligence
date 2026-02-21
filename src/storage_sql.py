"""SQLite-based persistent storage for field recommendations and decisions."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import FieldRecommendations, FieldDecision


class SQLiteStorage:
    """SQLite-based persistent storage with full SQL capabilities."""
    
    def __init__(self, db_path: str = "data/intelligence.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Initialize schema
        self._create_schema()
    
    def _create_schema(self) -> None:
        """Create database schema if not exists."""
        cursor = self.conn.cursor()
        
        # Recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id TEXT NOT NULL,
                crop TEXT NOT NULL,
                season TEXT NOT NULL,
                total_area_ha REAL NOT NULL,
                analysis_date TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(field_id, season)
            )
        """)
        
        # Create index on field_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_field_id 
            ON recommendations(field_id)
        """)
        
        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                decision_status TEXT NOT NULL,
                total_actions INTEGER NOT NULL,
                high_priority_count INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(field_id, decision_date)
            )
        """)
        
        # Create index on field_id and decision_date
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_field_id 
            ON decisions(field_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_date 
            ON decisions(decision_date DESC)
        """)
        
        # History table for time-series analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id TEXT NOT NULL,
                decision_id INTEGER NOT NULL,
                snapshot_date TEXT NOT NULL,
                data_json TEXT NOT NULL,
                FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_field_date 
            ON decision_history(field_id, snapshot_date DESC)
        """)
        
        self.conn.commit()
    
    def store_recommendations(self, recommendations: FieldRecommendations) -> None:
        """
        Store field recommendations from Precision Platform.
        
        Args:
            recommendations: Field recommendations to store
        """
        cursor = self.conn.cursor()
        field_id = self._normalize_field_id(recommendations.field_id)
        data_json = json.dumps(recommendations.model_dump(), ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO recommendations 
            (field_id, crop, season, total_area_ha, analysis_date, data_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(field_id, season) DO UPDATE SET
                crop = excluded.crop,
                total_area_ha = excluded.total_area_ha,
                analysis_date = excluded.analysis_date,
                data_json = excluded.data_json,
                updated_at = CURRENT_TIMESTAMP
        """, (
            field_id,
            recommendations.crop,
            recommendations.season,
            recommendations.total_area_ha,
            recommendations.analysis_date,
            data_json
        ))
        
        self.conn.commit()
    
    def get_recommendations(self, field_id: str) -> Optional[FieldRecommendations]:
        """
        Retrieve latest field recommendations.
        
        Args:
            field_id: Field identifier
            
        Returns:
            FieldRecommendations if found, None otherwise
        """
        cursor = self.conn.cursor()
        field_id = self._normalize_field_id(field_id)
        
        cursor.execute("""
            SELECT data_json FROM recommendations 
            WHERE field_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (field_id,))
        
        row = cursor.fetchone()
        if row:
            data = json.loads(row["data_json"])
            return FieldRecommendations(**data)
        return None
    
    def store_decision(self, decision: FieldDecision) -> None:
        """
        Store field decision from Intelligence Platform.
        
        Args:
            decision: Field decision to store
        """
        cursor = self.conn.cursor()
        field_id = self._normalize_field_id(decision.field_id)
        data_json = json.dumps(decision.model_dump(), ensure_ascii=False)
        
        # Count high priority actions
        high_priority_count = sum(
            1 for zone in decision.zones
            if zone.action.priority in ["high", "critical"]
        )
        
        cursor.execute("""
            INSERT INTO decisions 
            (field_id, decision_date, decision_status, total_actions, 
             high_priority_count, data_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(field_id, decision_date) DO UPDATE SET
                decision_status = excluded.decision_status,
                total_actions = excluded.total_actions,
                high_priority_count = excluded.high_priority_count,
                data_json = excluded.data_json,
                updated_at = CURRENT_TIMESTAMP
        """, (
            field_id,
            decision.decision_date,
            decision.priority.level,
            len(decision.zones),
            high_priority_count,
            data_json
        ))
        
        decision_id = cursor.lastrowid
        
        # Store in history for time-series analysis
        cursor.execute("""
            INSERT INTO decision_history (field_id, decision_id, snapshot_date, data_json)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        """, (field_id, decision_id, data_json))
        
        self.conn.commit()
    
    def get_decision(self, field_id: str) -> Optional[FieldDecision]:
        """
        Retrieve latest field decision.
        
        Args:
            field_id: Field identifier
            
        Returns:
            FieldDecision if found, None otherwise
        """
        cursor = self.conn.cursor()
        field_id = self._normalize_field_id(field_id)
        
        cursor.execute("""
            SELECT data_json FROM decisions 
            WHERE field_id = ?
            ORDER BY decision_date DESC
            LIMIT 1
        """, (field_id,))
        
        row = cursor.fetchone()
        if row:
            data = json.loads(row["data_json"])
            return FieldDecision(**data)
        return None
    
    def get_decision_history(
        self, 
        field_id: str, 
        limit: int = 10
    ) -> List[FieldDecision]:
        """
        Retrieve decision history for a field.
        
        Args:
            field_id: Field identifier
            limit: Maximum number of historical decisions to return
            
        Returns:
            List of historical decisions, newest first
        """
        cursor = self.conn.cursor()
        field_id = self._normalize_field_id(field_id)
        
        cursor.execute("""
            SELECT data_json FROM decision_history 
            WHERE field_id = ?
            ORDER BY snapshot_date DESC
            LIMIT ?
        """, (field_id, limit))
        
        decisions = []
        for row in cursor.fetchall():
            data = json.loads(row["data_json"])
            decisions.append(FieldDecision(**data))
        
        return decisions
    
    def list_fields(self) -> Dict[str, dict]:
        """
        List all stored fields with summary info.
        
        Returns:
            Dictionary mapping field_id to summary info
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.field_id,
                r.crop,
                r.total_area_ha as area_ha,
                r.season,
                r.analysis_date,
                CASE WHEN d.field_id IS NOT NULL THEN 1 ELSE 0 END as has_decision,
                d.decision_date as last_decision_date,
                d.high_priority_count
            FROM recommendations r
            LEFT JOIN (
                SELECT field_id, MAX(decision_date) as decision_date, high_priority_count
                FROM decisions
                GROUP BY field_id
            ) d ON r.field_id = d.field_id
            ORDER BY r.updated_at DESC
        """)
        
        fields = {}
        for row in cursor.fetchall():
            fields[row["field_id"]] = {
                "field_id": row["field_id"],
                "crop": row["crop"],
                "area_ha": row["area_ha"],
                "season": row["season"],
                "analysis_date": row["analysis_date"],
                "has_decision": bool(row["has_decision"]),
                "last_decision_date": row["last_decision_date"],
                "high_priority_actions": row["high_priority_count"] or 0,
            }
        
        return fields
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM recommendations")
        recommendations_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM decisions")
        decisions_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM decision_history")
        history_count = cursor.fetchone()["count"]
        
        cursor.execute("""
            SELECT SUM(total_area_ha) as total_area 
            FROM recommendations
        """)
        total_area = cursor.fetchone()["total_area"] or 0.0
        
        cursor.execute("""
            SELECT SUM(high_priority_count) as high_priority 
            FROM decisions
        """)
        high_priority_actions = cursor.fetchone()["high_priority"] or 0
        
        return {
            "db_path": str(self.db_path),
            "total_fields": recommendations_count,
            "total_decisions": decisions_count,
            "historical_snapshots": history_count,
            "total_area_ha": round(total_area, 2),
            "high_priority_actions": high_priority_actions,
        }
    
    def _normalize_field_id(self, field_id: str) -> str:
        """Normalize field ID (extract short form if needed)."""
        return field_id.split("-")[0] if "-" in field_id else field_id
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
