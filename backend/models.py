from pydantic import BaseModel, field_validator
from typing import Optional

CATEGORIES = ["Tamil", "English", "Other"]

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
    category: str

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v

class GifSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    tags: list[str]
    gif_url: str
    created_at: str
    category: str

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
    category: str

class ApproveRequest(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    description: str | None = None
    category: str | None = None
