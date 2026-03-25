"""
PHASE 13.1 - Alpha Factory Repository
======================================
MongoDB persistence for Alpha Factory data.
"""

from typing import List, Dict
from datetime import datetime, timezone, timedelta

from core.database import MongoRepository, get_database

try:
    from pymongo import DESCENDING
    MONGO_OK = True
except ImportError:
    MONGO_OK = False


class AlphaFactoryRepository(MongoRepository):
    """Repository for Alpha Factory data."""
    
    def __init__(self):
        super().__init__()
        self._init_collections()
    
    def _init_collections(self):
        """Initialize collection indexes."""
        if not self.connected:
            return
        
        try:
            db = self.db
            if db is None:
                return
            
            # Alpha nodes
            db.alpha_nodes.create_index([("node_id", 1)], unique=True)
            db.alpha_nodes.create_index([("node_type", 1)])
            db.alpha_nodes.create_index([("status", 1)])
            
            # Features (for Feature Library)
            db.alpha_features.create_index([("feature_id", 1)], unique=True)
            db.alpha_features.create_index([("category", 1)])
            
            # Factors (for Factor Generator)
            db.alpha_factors.create_index([("factor_id", 1)], unique=True)
            db.alpha_factors.create_index([("status", 1)])
            
            # Factor performance
            db.factor_performance.create_index([("factor_id", 1), ("timestamp", -1)])
            
            # Graph relations
            db.alpha_graph_relations.create_index([("source_node", 1)])
            db.alpha_graph_relations.create_index([("target_node", 1)])
            db.alpha_graph_relations.create_index([("relation_type", 1)])
            
            # DAG computations
            db.alpha_dag_runs.create_index([("run_id", 1)])
            db.alpha_dag_runs.create_index([("timestamp", -1)])
            
            print("[AlphaFactoryRepo] Indexes created")
            
        except Exception as e:
            print(f"[AlphaFactoryRepo] Index error: {e}")
    
    def get_stats(self) -> Dict:
        """Get repository statistics."""
        if not self.connected:
            return {"connected": False}
        
        try:
            db = self.db
            if db is None:
                return {"connected": False}
            
            return {
                "connected": True,
                "collections": {
                    "alpha_nodes": db.alpha_nodes.count_documents({}),
                    "alpha_features": db.alpha_features.count_documents({}),
                    "alpha_factors": db.alpha_factors.count_documents({}),
                    "factor_performance": db.factor_performance.count_documents({}),
                    "alpha_graph_relations": db.alpha_graph_relations.count_documents({}),
                    "alpha_dag_runs": db.alpha_dag_runs.count_documents({})
                }
            }
        except Exception as e:
            return {"connected": True, "error": str(e)}
