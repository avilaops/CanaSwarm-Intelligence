"""Simple in-memory storage for field recommendations and decisions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .models import FieldRecommendations, FieldDecision


class InMemoryStorage:
    """In-memory storage with optional JSON persistence."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize storage.
        
        Args:
            data_dir: Directory for JSON persistence
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # In-memory storage
        self.recommendations: Dict[str, FieldRecommendations] = {}
        self.decisions: Dict[str, FieldDecision] = {}
        
        # Load existing data if available
        self._load_from_disk()
    
    def store_recommendations(self, recommendations: FieldRecommendations) -> None:
        """
        Store field recommendations from Precision Platform.
        
        Args:
            recommendations: Field recommendations to store
        """
        field_id = self._normalize_field_id(recommendations.field_id)
        self.recommendations[field_id] = recommendations
        
        # Persist to disk
        self._save_to_disk(field_id, "recommendations", recommendations.model_dump())
    
    def get_recommendations(self, field_id: str) -> Optional[FieldRecommendations]:
        """
        Retrieve field recommendations.
        
        Args:
            field_id: Field identifier
            
        Returns:
            FieldRecommendations if found, None otherwise
        """
        field_id = self._normalize_field_id(field_id)
        return self.recommendations.get(field_id)
    
    def store_decision(self, decision: FieldDecision) -> None:
        """
        Store field decision from Intelligence Platform.
        
        Args:
            decision: Field decision to store
        """
        field_id = self._normalize_field_id(decision.field_id)
        self.decisions[field_id] = decision
        
        # Persist to disk
        self._save_to_disk(field_id, "decisions", decision.model_dump())
    
    def get_decision(self, field_id: str) -> Optional[FieldDecision]:
        """
        Retrieve field decision.
        
        Args:
            field_id: Field identifier
            
        Returns:
            FieldDecision if found, None otherwise
        """
        field_id = self._normalize_field_id(field_id)
        return self.decisions.get(field_id)
    
    def list_fields(self) -> Dict[str, dict]:
        """
        List all stored fields with summary info.
        
        Returns:
            Dictionary mapping field_id to summary info
        """
        fields = {}
        for field_id, rec in self.recommendations.items():
            fields[field_id] = {
                "field_id": rec.field_id,
                "crop": rec.crop,
                "area_ha": rec.total_area_ha,
                "season": rec.season,
                "analysis_date": rec.analysis_date,
                "has_decision": field_id in self.decisions,
            }
        return fields
    
    def _normalize_field_id(self, field_id: str) -> str:
        """Normalize field ID (extract short form if needed)."""
        return field_id.split("-")[0] if "-" in field_id else field_id
    
    def _save_to_disk(self, field_id: str, data_type: str, data: dict) -> None:
        """Save data to JSON file."""
        file_path = self.data_dir / f"{field_id}_{data_type}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_from_disk(self) -> None:
        """Load existing data from JSON files."""
        if not self.data_dir.exists():
            return
        
        # Load recommendations
        for file_path in self.data_dir.glob("*_recommendations.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rec = FieldRecommendations(**data)
                    field_id = self._normalize_field_id(rec.field_id)
                    self.recommendations[field_id] = rec
            except Exception:
                pass  # Skip corrupted files
        
        # Load decisions
        for file_path in self.data_dir.glob("*_decisions.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    dec = FieldDecision(**data)
                    field_id = self._normalize_field_id(dec.field_id)
                    self.decisions[field_id] = dec
            except Exception:
                pass  # Skip corrupted files
