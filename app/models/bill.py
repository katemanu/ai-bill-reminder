from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Bill(db.Model):
    """Model for storing bill information."""

    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Bill details
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    frequency = db.Column(db.String(20), default="one-time")
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)

    # Status tracking
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Bill {self.name} ${self.amount}>"

    def to_dict(self):
        """Convert bill to dictionary for JSON response."""
        return {
            "id": self.id,
            "name": self.name,
            "amount": float(self.amount),
            "due_date": self.due_date.isoformat(),
            "frequency": self.frequency,
            "category": self.category,
            "notes": self.notes,
            "is_paid": self.is_paid,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def is_overdue(self):
        """Check if bill is overdue."""
        if self.is_paid:
            return False
        return date.today() > self.due_date
