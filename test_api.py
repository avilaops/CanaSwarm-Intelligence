"""Test Intelligence API imports and data structures"""
from src.api import app, storage
from src.models import FieldRecommendations, FieldDecision

print("✓ Intelligence API imports successful")
print(f"✓ Storage initialized: {storage.data_dir}")
print(f"✓ Stored fields: {len(storage.list_fields())}")
print("\nReady to start API server:")
print("  uvicorn src.api:app --host 0.0.0.0 --port 6000")
