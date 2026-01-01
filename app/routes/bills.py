from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from pydantic import ValidationError
from app.models import db, Bill
from app.security import limiter, BillCreate, BillNaturalLanguage
from app.services import BillParser

bills_bp = Blueprint("bills", __name__, url_prefix="/api/bills")


@bills_bp.route("", methods=["GET"])
@jwt_required()
def get_bills():
    """Get all bills for current user."""
    bills = Bill.query.filter_by(user_id=current_user.id).order_by(Bill.due_date).all()
    return jsonify({
        "bills": [bill.to_dict() for bill in bills],
        "count": len(bills),
    }), 200


@bills_bp.route("/<int:bill_id>", methods=["GET"])
@jwt_required()
def get_bill(bill_id):
    """Get a specific bill."""
    bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404
    return jsonify({"bill": bill.to_dict()}), 200


@bills_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("30 per hour")
def create_bill():
    """Create a new bill manually."""
    try:
        data = BillCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    bill = Bill(
        user_id=current_user.id,
        name=data.name,
        amount=data.amount,
        due_date=datetime.strptime(data.due_date, "%Y-%m-%d").date(),
        frequency=data.frequency,
        category=data.category,
        notes=data.notes,
    )

    db.session.add(bill)
    db.session.commit()

    return jsonify({"message": "Bill created", "bill": bill.to_dict()}), 201


@bills_bp.route("/parse", methods=["POST"])
@jwt_required()
@limiter.limit("20 per hour")
def parse_bill():
    """Parse natural language bill description using AI."""
    try:
        data = BillNaturalLanguage(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    parser = BillParser()
    result = parser.parse_bill(data.text)

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    bill_data = result["data"]
    bill = Bill(
        user_id=current_user.id,
        name=bill_data["name"],
        amount=bill_data["amount"],
        due_date=datetime.strptime(bill_data["due_date"], "%Y-%m-%d").date(),
        frequency=bill_data.get("frequency", "one-time"),
        category=bill_data.get("category"),
    )

    db.session.add(bill)
    db.session.commit()

    return jsonify({
        "message": "Bill parsed and created",
        "bill": bill.to_dict(),
        "parsed_from": data.text,
    }), 201


@bills_bp.route("/<int:bill_id>", methods=["PUT"])
@jwt_required()
def update_bill(bill_id):
    """Update an existing bill."""
    bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    data = request.get_json()

    if "name" in data:
        bill.name = data["name"]
    if "amount" in data:
        bill.amount = data["amount"]
    if "due_date" in data:
        bill.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
    if "frequency" in data:
        bill.frequency = data["frequency"]
    if "category" in data:
        bill.category = data["category"]
    if "notes" in data:
        bill.notes = data["notes"]

    db.session.commit()

    return jsonify({"message": "Bill updated", "bill": bill.to_dict()}), 200


@bills_bp.route("/<int:bill_id>", methods=["DELETE"])
@jwt_required()
def delete_bill(bill_id):
    """Delete a bill."""
    bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    db.session.delete(bill)
    db.session.commit()

    return jsonify({"message": "Bill deleted"}), 200


@bills_bp.route("/<int:bill_id>/pay", methods=["POST"])
@jwt_required()
def mark_bill_paid(bill_id):
    """Mark a bill as paid."""
    bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    bill.is_paid = True
    bill.paid_date = datetime.now().date()
    db.session.commit()

    return jsonify({"message": "Bill marked as paid", "bill": bill.to_dict()}), 200


@bills_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_summary():
    """Get bill summary for dashboard."""
    bills = Bill.query.filter_by(user_id=current_user.id).all()

    total_bills = len(bills)
    unpaid_bills = [b for b in bills if not b.is_paid]
    overdue_bills = [b for b in unpaid_bills if b.is_overdue]

    total_due = sum(float(b.amount) for b in unpaid_bills)
    total_overdue = sum(float(b.amount) for b in overdue_bills)

    return jsonify({
        "total_bills": total_bills,
        "unpaid_count": len(unpaid_bills),
        "overdue_count": len(overdue_bills),
        "total_due": round(total_due, 2),
        "total_overdue": round(total_overdue, 2),
    }), 200
