"""
Idea API Routes
================
REST API endpoints for Idea System.

Endpoints:
- POST /api/ta/ideas — Create new idea
- GET /api/ta/ideas — List ideas
- GET /api/ta/ideas/{idea_id} — Get idea details
- POST /api/ta/ideas/{idea_id}/update — Update idea (new version)
- POST /api/ta/ideas/{idea_id}/validate — Validate idea
- GET /api/ta/ideas/{idea_id}/timeline — Get idea timeline
- DELETE /api/ta/ideas/{idea_id} — Delete idea
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from modules.ta_engine.ideas.idea_service import get_idea_service

router = APIRouter(prefix="/api/ta/ideas", tags=["ta-ideas"])


class CreateIdeaRequest(BaseModel):
    asset: str
    timeframe: str = "1d"
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = ""


class ValidateIdeaRequest(BaseModel):
    current_price: Optional[float] = None


# ═══════════════════════════════════════════════════════════════
# CREATE IDEA
# ═══════════════════════════════════════════════════════════════

@router.post("")
async def create_idea(request: CreateIdeaRequest):
    """
    Create a new trading idea.
    
    Runs setup analysis and saves the result as an idea.
    """
    service = get_idea_service()
    
    idea = service.create_idea(
        asset=request.asset,
        timeframe=request.timeframe,
        user_id=request.user_id,
        tags=request.tags,
        notes=request.notes or "",
    )
    
    return {
        "ok": True,
        "message": "Idea created successfully",
        "idea": idea.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════
# LIST IDEAS
# ═══════════════════════════════════════════════════════════════

@router.get("")
async def list_ideas(
    user_id: Optional[str] = None,
    asset: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """
    List saved ideas with optional filters.
    """
    service = get_idea_service()
    
    ideas = service.list_ideas(
        user_id=user_id,
        asset=asset,
        status=status,
        limit=limit,
    )
    
    return {
        "ok": True,
        "ideas": [idea.to_summary_dict() for idea in ideas],
        "count": len(ideas),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# GET IDEA
# ═══════════════════════════════════════════════════════════════

@router.get("/{idea_id}")
async def get_idea(idea_id: str):
    """
    Get full idea details including all versions and validations.
    """
    service = get_idea_service()
    
    idea = service.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "ok": True,
        "idea": idea.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════
# UPDATE IDEA (NEW VERSION)
# ═══════════════════════════════════════════════════════════════

@router.post("/{idea_id}/update")
async def update_idea(idea_id: str):
    """
    Update idea with fresh analysis, creating a new version.
    """
    service = get_idea_service()
    
    idea = service.update_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "ok": True,
        "message": f"Idea updated to version {idea.current_version}",
        "idea": idea.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════
# VALIDATE IDEA
# ═══════════════════════════════════════════════════════════════

@router.post("/{idea_id}/validate")
async def validate_idea(idea_id: str, request: Optional[ValidateIdeaRequest] = None):
    """
    Validate an idea by checking if the prediction was correct.
    """
    service = get_idea_service()
    
    current_price = request.current_price if request else None
    idea = service.validate_idea(idea_id, current_price)
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    latest_validation = idea.validations[-1] if idea.validations else None
    
    return {
        "ok": True,
        "message": "Idea validated",
        "validation_result": latest_validation.result.value if latest_validation else None,
        "idea": idea.to_dict(),
    }


# ═══════════════════════════════════════════════════════════════
# GET TIMELINE
# ═══════════════════════════════════════════════════════════════

@router.get("/{idea_id}/timeline")
async def get_idea_timeline(idea_id: str):
    """
    Get timeline view of idea evolution.
    
    Shows all versions and validations in chronological order.
    """
    service = get_idea_service()
    
    timeline = service.get_idea_timeline(idea_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "ok": True,
        **timeline,
    }


# ═══════════════════════════════════════════════════════════════
# DELETE IDEA
# ═══════════════════════════════════════════════════════════════

@router.delete("/{idea_id}")
async def delete_idea(idea_id: str):
    """
    Delete an idea.
    """
    service = get_idea_service()
    
    success = service.delete_idea(idea_id)
    if not success:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "ok": True,
        "message": "Idea deleted",
    }


# ═══════════════════════════════════════════════════════════════
# ARCHIVE IDEA
# ═══════════════════════════════════════════════════════════════

@router.post("/{idea_id}/archive")
async def archive_idea(idea_id: str):
    """
    Archive an idea (soft delete).
    """
    service = get_idea_service()
    
    idea = service.archive_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "ok": True,
        "message": "Idea archived",
        "idea": idea.to_summary_dict(),
    }
