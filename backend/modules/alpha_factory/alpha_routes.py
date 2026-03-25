"""
PHASE 13.1 - Alpha Factory Routes
==================================
API endpoints for Alpha Node Registry.

Endpoints:
- GET  /api/alpha-factory/health
- GET  /api/alpha-factory/nodes
- GET  /api/alpha-factory/nodes/{node_id}
- POST /api/alpha-factory/nodes
- PUT  /api/alpha-factory/nodes/{node_id}
- GET  /api/alpha-factory/nodes/types
- GET  /api/alpha-factory/nodes/search
- GET  /api/alpha-factory/nodes/{node_id}/relationships
- GET  /api/alpha-factory/nodes/{node_id}/dependents
- GET  /api/alpha-factory/stats
"""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .alpha_node_registry import get_alpha_registry, AlphaNodeRegistry
from .alpha_types import NodeType, NodeStatus, AlphaNode
from .alpha_repository import AlphaFactoryRepository

router = APIRouter(prefix="/api/alpha-factory", tags=["Alpha Factory"])


# ===== Pydantic Models =====

class NodeCreateRequest(BaseModel):
    node_id: str
    node_type: str = "alpha"
    source_module: str
    inputs: List[str] = []
    outputs: List[str] = []
    compute_function: Optional[str] = None
    compute_params: dict = {}
    description: str = ""
    tags: List[str] = []
    category: Optional[str] = None
    regime_dependency: List[str] = []
    value_type: str = "float"
    confidence_range: List[float] = [0.0, 1.0]
    supports: List[str] = []
    contradicts: List[str] = []
    amplifies: List[str] = []
    conditional_on: List[str] = []


class NodeUpdateRequest(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    regime_dependency: Optional[List[str]] = None
    supports: Optional[List[str]] = None
    contradicts: Optional[List[str]] = None
    amplifies: Optional[List[str]] = None
    conditional_on: Optional[List[str]] = None
    status: Optional[str] = None


# ===== Singleton instances =====

_registry: Optional[AlphaNodeRegistry] = None
_repository: Optional[AlphaFactoryRepository] = None


def get_registry() -> AlphaNodeRegistry:
    global _registry
    if _registry is None:
        _registry = get_alpha_registry()
    return _registry


def get_repository() -> AlphaFactoryRepository:
    global _repository
    if _repository is None:
        _repository = AlphaFactoryRepository()
    return _repository


# ===== Health & Stats =====

@router.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "module": "alpha_factory",
        "version": "phase13.1_alpha_node_registry",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stats")
async def get_stats():
    """Get Alpha Factory statistics."""
    registry = get_registry()
    repo = get_repository()
    
    registry_stats = registry.get_stats()
    repo_stats = repo.get_stats()
    
    return {
        "registry": registry_stats,
        "repository": repo_stats,
        "computed_at": datetime.now(timezone.utc).isoformat()
    }


# ===== Node CRUD =====

@router.get("/nodes")
async def list_nodes(
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    status: str = Query("active", description="Filter by status"),
    limit: int = Query(100, ge=1, le=500)
):
    """List all alpha nodes."""
    registry = get_registry()
    
    nt = NodeType(node_type) if node_type else None
    ns = NodeStatus(status) if status else NodeStatus.ACTIVE
    tags = [tag] if tag else None
    
    nodes = registry.list_nodes(
        node_type=nt,
        tags=tags,
        status=ns,
        limit=limit
    )
    
    return {
        "count": len(nodes),
        "nodes": [n.to_dict() for n in nodes],
        "filters": {
            "node_type": node_type,
            "tag": tag,
            "status": status
        }
    }


@router.get("/nodes/types")
async def get_node_types():
    """Get available node types."""
    registry = get_registry()
    breakdown = registry.get_type_breakdown()
    
    return {
        "types": [t.value for t in NodeType],
        "counts": breakdown,
        "total": sum(breakdown.values())
    }


@router.get("/nodes/search")
async def search_nodes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200)
):
    """Search nodes by query."""
    registry = get_registry()
    results = registry.search_nodes(q, limit=limit)
    
    return {
        "query": q,
        "count": len(results),
        "nodes": [n.to_dict() for n in results]
    }


@router.get("/nodes/tags")
async def get_all_tags():
    """Get all unique tags across nodes."""
    registry = get_registry()
    nodes = registry.list_nodes(limit=500)
    
    tags = set()
    for node in nodes:
        tags.update(node.tags)
    
    return {
        "tags": sorted(list(tags)),
        "count": len(tags)
    }


@router.get("/nodes/categories")
async def get_all_categories():
    """Get all unique categories across nodes."""
    registry = get_registry()
    nodes = registry.list_nodes(limit=500)
    
    categories = {}
    for node in nodes:
        cat = node.category or "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": categories,
        "count": len(categories)
    }


@router.get("/nodes/by-type/{node_type}")
async def get_nodes_by_type(node_type: str):
    """Get all nodes of a specific type."""
    try:
        nt = NodeType(node_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid node_type: {node_type}")
    
    registry = get_registry()
    nodes = registry.get_nodes_by_type(nt)
    
    return {
        "node_type": node_type,
        "count": len(nodes),
        "nodes": [n.to_dict() for n in nodes]
    }


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """Get a specific node."""
    registry = get_registry()
    node = registry.get_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    return {
        "node": node.to_dict(),
        "relationships": registry.get_node_relationships(node_id),
        "dependents": registry.get_dependent_nodes(node_id)
    }


@router.post("/nodes")
async def create_node(request: NodeCreateRequest):
    """Create a new alpha node."""
    registry = get_registry()
    
    # Check if exists
    existing = registry.get_node(request.node_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Node '{request.node_id}' already exists")
    
    # Create node
    try:
        node_type = NodeType(request.node_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid node_type: {request.node_type}")
    
    node = AlphaNode(
        node_id=request.node_id,
        node_type=node_type,
        source_module=request.source_module,
        inputs=request.inputs,
        outputs=request.outputs,
        compute_function=request.compute_function,
        compute_params=request.compute_params,
        description=request.description,
        tags=request.tags,
        category=request.category,
        regime_dependency=request.regime_dependency,
        value_type=request.value_type,
        confidence_range=request.confidence_range,
        supports=request.supports,
        contradicts=request.contradicts,
        amplifies=request.amplifies,
        conditional_on=request.conditional_on,
        created_at=datetime.now(timezone.utc)
    )
    
    success = registry.register_node(node)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register node")
    
    return {
        "created": True,
        "node_id": node.node_id,
        "node": node.to_dict()
    }


@router.put("/nodes/{node_id}")
async def update_node(node_id: str, request: NodeUpdateRequest):
    """Update an existing node."""
    registry = get_registry()
    
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    # Build updates
    updates = {}
    if request.description is not None:
        updates["description"] = request.description
    if request.tags is not None:
        updates["tags"] = request.tags
    if request.regime_dependency is not None:
        updates["regime_dependency"] = request.regime_dependency
    if request.supports is not None:
        updates["supports"] = request.supports
    if request.contradicts is not None:
        updates["contradicts"] = request.contradicts
    if request.amplifies is not None:
        updates["amplifies"] = request.amplifies
    if request.conditional_on is not None:
        updates["conditional_on"] = request.conditional_on
    if request.status is not None:
        updates["status"] = request.status
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    success = registry.update_node(node_id, updates)
    
    return {
        "updated": success,
        "node_id": node_id,
        "updates": updates
    }


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    """Delete (deprecate) a node."""
    registry = get_registry()
    
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    success = registry.delete_node(node_id)
    
    return {
        "deleted": success,
        "node_id": node_id,
        "status": "deprecated"
    }


# ===== Relationships (Alpha Graph support) =====

@router.get("/nodes/{node_id}/relationships")
async def get_node_relationships(node_id: str):
    """Get all relationships for a node."""
    registry = get_registry()
    
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    return {
        "node_id": node_id,
        "relationships": registry.get_node_relationships(node_id),
        "computed_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/nodes/{node_id}/dependents")
async def get_node_dependents(node_id: str):
    """Get nodes that depend on this node (DAG support)."""
    registry = get_registry()
    
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    return {
        "node_id": node_id,
        "inputs": registry.get_node_inputs(node_id),
        "outputs": registry.get_node_outputs(node_id),
        "dependent_nodes": registry.get_dependent_nodes(node_id),
        "computed_at": datetime.now(timezone.utc).isoformat()
    }


# ===== Performance =====

@router.get("/nodes/{node_id}/performance")
async def get_node_performance(
    node_id: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Get performance history for a node."""
    registry = get_registry()
    
    node = registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    performance = registry.get_node_performance(node_id, limit=limit)
    
    return {
        "node_id": node_id,
        "performance_history": performance,
        "count": len(performance)
    }
