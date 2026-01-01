import os
import json
from datetime import datetime, timedelta
from anthropic import Anthropic


class BillParser:
    """Parse natural language bill descriptions using Claude AI."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = Anthropic(api_key=api_key)

    def parse_bill(self, text):
        """
        Parse natural language text into structured bill data.
        """
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        current_year = today.year

        prompt = f"""Parse this bill description into structured data. Today's date is {today_str}.

Bill description: "{text}"

Extract the following fields:
- name: The bill name (e.g., "Electric bill", "Netflix subscription")
- amount: The dollar amount as a number (e.g., 150.00)
- due_date: The due date in YYYY-MM-DD format. If only month/day given, assume year {current_year} or {current_year + 1} if the date has passed. If no date is mentioned and it's a recurring bill, use the 1st of next month.
- frequency: One of "one-time", "weekly", "monthly", "quarterly", "yearly". Default to "monthly" for subscriptions, "one-time" otherwise.
- category: One of "utilities", "subscription", "insurance", "rent", "loan", "medical", "other"

IMPORTANT: Always provide a due_date, never null. If unclear, default to the 1st of next month.

Respond ONLY with valid JSON, no other text. Example:
{{"name": "Electric bill", "amount": 150.00, "due_date": "2026-01-15", "frequency": "one-time", "category": "utilities"}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            result_text = response.content[0].text.strip()
            bill_data = json.loads(result_text)

            required_fields = ["name", "amount"]
            for field in required_fields:
                if field not in bill_data:
                    raise ValueError(f"Missing required field: {field}")

            bill_data["amount"] = float(bill_data["amount"])
            if bill_data["amount"] <= 0:
                raise ValueError("Amount must be greater than 0")

            # Handle missing or null due_date
            if not bill_data.get("due_date"):
                next_month = today.replace(day=1) + timedelta(days=32)
                bill_data["due_date"] = next_month.replace(day=1).strftime("%Y-%m-%d")
            
            # Validate date format
            datetime.strptime(bill_data["due_date"], "%Y-%m-%d")

            if "frequency" not in bill_data:
                bill_data["frequency"] = "one-time"
            if "category" not in bill_data:
                bill_data["category"] = "other"

            return {"success": True, "data": bill_data}

        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Could not parse bill details. Please try again with more detail.",
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"DEBUG: AI Parser error: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": "An error occurred while parsing. Please try again.",
            }
