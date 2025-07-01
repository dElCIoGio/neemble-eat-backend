from fastapi import APIRouter

from app.services import diagnostics as diag_service

router = APIRouter()


@router.get("/sessions/duplicates")
async def get_duplicate_sessions():
    """List tables with more than one active session."""
    return await diag_service.duplicate_active_sessions()


@router.get("/sessions/current-mismatch")
async def get_current_session_mismatches():
    """Find tables whose currentSessionId does not match an active session."""
    return await diag_service.mismatched_current_sessions()


@router.get("/sessions/orphans")
async def get_orphan_sessions():
    """Return sessions not linked to any table."""
    return await diag_service.orphan_sessions()


@router.get("/run-all")
async def run_all_diagnostics():
    """Execute all diagnostic checks and return their results."""
    return await diag_service.run_all()
