"""
ERP AI Assistant — Pydantic Models
Request/response models for all API endpoints.
"""
from pydantic import BaseModel
from typing import Optional


# ─── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = ""
    text: str = ""
    user_id: str = "user_001"
    company_id: str = ""
    company_code: str = ""
    companyfn: str = ""
    masterfn: str = ""
    lang: str = "auto"
    topic: Optional[str] = None
    session_id: str = ""
    stream: bool = True


class ChatHistoryRequest(BaseModel):
    user_id: str
    company_id: str = ""
    limit: int = 50
    before_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatHistoryDeleteRequest(BaseModel):
    user_id: str
    company_id: str = ""


# ─── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    entry_version_id: int
    user_id: str
    company_id: str = ""
    rating: str  # 'up' | 'down'
    query_text: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None


class FeedbackBulkRequest(BaseModel):
    user_id: str
    company_id: str = ""
    ratings: list  # list of {entry_version_id, rating, query_text?, reason?, comment?}


# ─── Admin ─────────────────────────────────────────────────────────────────────

class AdminFlagAction(BaseModel):
    admin_user_id: str = "admin"
    entry_version_id: Optional[int] = None
    reason: Optional[str] = None



class AdminSchedulerAction(BaseModel):
    admin_user_id: str = "admin"


class AdminSchedulerConfig(BaseModel):
    admin_user_id: str = "admin"
    interval: str = "daily"
    time: str = "02:00"
    day: str = "monday"


class AdminResolveFlag(BaseModel):
    admin_user_id: str = "admin"
    resolution_note: Optional[str] = None


class AdminFlagEntry(BaseModel):
    admin_user_id: str = "admin"
    flag_reason: str = ""


class AdminFlagResolve(BaseModel):
    admin_user_id: str = "admin"
    entry_version_id: int
    resolution_note: Optional[str] = None


class AdminSCMPredict(BaseModel):
    model_name: str
    features: dict


class ScmTrainingRunRequest(BaseModel):
    admin_user_id: str = "admin"
    masterfn: str = ""
    companyfn: str = ""
    model: str = "all"
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class AIAlertCreate(BaseModel):
    masterfn: str
    companyfn: str
    alert_type: str
    severity: str = "medium"
    title: str
    reason_code: Optional[str] = None
    risk_score: Optional[float] = None
    source_id: Optional[str] = None
    evidence: dict = {}
    rule_version: Optional[str] = None


class AIAlertReview(BaseModel):
    masterfn: str
    companyfn: str
    status: str
    reviewer: str
    note: Optional[str] = None


class AIRecommendationAction(BaseModel):
    masterfn: str
    companyfn: str
    recommendation_id: str
    action: str
    actor: str
    note: Optional[str] = None
    adjusted_qty: Optional[float] = None


