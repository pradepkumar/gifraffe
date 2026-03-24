from pydantic import BaseModel, field_validator
from typing import Optional

class GenerateRequest(BaseModel):
    url: str
    start: float
    end: float

class JobResponse(BaseModel):
    status: str
    step: Optional[str]
    gif_url: Optional[str]
    error: Optional[str]

class SubmitRequest(BaseModel):
    job_id: str
    title: str
    tags: str
    submitter_name: str
    description: Optional[str] = None
    submitter_email: Optional[str] = None

class GifSummary(BaseModel):
    id: str
    title: str
    description: Optional[str]
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
    description: Optional[str]
    tags: list[str]
    submitter_name: str
    submitter_email: Optional[str]
    gif_url: str
    source_url: str
    source_start: float
    source_end: float
    created_at: str
