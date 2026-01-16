from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class HealthResponse(BaseModel):
    status: str = "ok"


class BookOut(BaseModel):
    isbn: str
    title: str
    author: str
    category: str
    publisher: str
    publication_year: int
    total_copies: int
    available_copies: int
    description: str = ""


class BookListItem(BaseModel):
    isbn: str
    title: str
    author: str
    available_copies: int
    total_copies: int


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = ""
    address: Optional[str] = ""


class UserCreateResponse(BaseModel):
    user_id: UUID


class BorrowCreate(BaseModel):
    user_id: UUID
    isbn: str


class BorrowResponse(BaseModel):
    success: bool
