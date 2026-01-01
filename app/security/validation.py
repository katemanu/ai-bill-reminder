import re
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class UserRegistration(BaseModel):
    """Validate user registration input."""

    email: EmailStr
    password: str
    name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a number")
        return v

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Name must be less than 100 characters")
        if re.search(r"[<>\"';]", v):
            raise ValueError("Name contains invalid characters")
        return v


class UserLogin(BaseModel):
    """Validate user login input."""

    email: EmailStr
    password: str


class BillCreate(BaseModel):
    """Validate bill creation input."""

    name: str
    amount: float
    due_date: str
    frequency: Optional[str] = "one-time"
    category: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Bill name must be 1-100 characters")
        if re.search(r"[<>\"';]", v):
            raise ValueError("Bill name contains invalid characters")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 999999.99:
            raise ValueError("Amount is too large")
        return round(v, 2)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        try:
            parsed = datetime.strptime(v, "%Y-%m-%d").date()
            return v
        except ValueError:
            raise ValueError("Due date must be in YYYY-MM-DD format")

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        allowed = ["one-time", "weekly", "monthly", "quarterly", "yearly"]
        if v not in allowed:
            raise ValueError(f"Frequency must be one of: {', '.join(allowed)}")
        return v


class BillNaturalLanguage(BaseModel):
    """Validate natural language bill input."""

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Please provide more detail about the bill")
        if len(v) > 500:
            raise ValueError("Input is too long (max 500 characters)")
        return v
