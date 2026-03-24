from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    url: str
    start: float
    end: float

class JobResponse(BaseModel):
    status: str
    step: Optional[str] = None
    gif_url: Optional[str] = None
    error: Optional[str] = None

class SubmitRequest(BaseModel):
    job_id: str
    title: str
    tags: list[str]
    submitter_name: str
    description: Optional[str] = None
    submitter_email: Optional[str] = None

class GifSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tags: list[str]
    gif_url: str
    created_at: str

class GifDetail(GifSummary):
    submitter_name: str
    source_url: str
    source_start: float
    source_end: float

class GifListResponse(BaseModel):
    results: list[GifSummary]
    total: int
    offset: int

class AdminLoginRequest(BaseModel):
    password: str

class AdminGifItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tags: list[str]
    submitter_name: str
    submitter_email: Optional[str] = None
    gif_url: str
    source_url: str
    source_start: float
    source_end: float
    created_at: str

class ApproveRequest(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    description: str | None = None
