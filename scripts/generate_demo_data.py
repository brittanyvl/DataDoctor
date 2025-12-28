"""
Generate demo dataset for Data Doctor.

This script creates a 500-row sample dataset with intentional errors
to demonstrate Data Doctor's validation capabilities.
"""

import csv
import random
from datetime import datetime, timedelta
import os

# Seed for reproducibility
random.seed(42)

# Configuration
NUM_ROWS = 500
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "demo_data.csv")

# Sample data pools
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "email.org"]

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

VALID_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

INVALID_STATUSES = ["canceled", "complete", "done", "waiting", "unknown"]  # "canceled" is American spelling, contract uses British "cancelled"

INVALID_STATES = ["XX", "ZZ", "UK", "EU", "00", "ABC"]


def generate_valid_email(first_name, last_name):
    """Generate a valid email address."""
    formats = [
        f"{first_name.lower()}.{last_name.lower()}@{random.choice(EMAIL_DOMAINS)}",
        f"{first_name.lower()}{random.randint(1, 99)}@{random.choice(EMAIL_DOMAINS)}",
        f"{first_name[0].lower()}{last_name.lower()}@{random.choice(EMAIL_DOMAINS)}",
    ]
    return random.choice(formats)


def generate_invalid_email():
    """Generate an invalid email address."""
    invalid_formats = [
        "notanemail",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com",
        "double@@at.com",
        "no.at" + "sign.com",
        "",
    ]
    return random.choice(invalid_formats)


def generate_valid_phone():
    """Generate a valid US phone number."""
    area_code = random.randint(200, 999)
    exchange = random.randint(200, 999)
    subscriber = random.randint(1000, 9999)

    formats = [
        f"({area_code}) {exchange}-{subscriber}",
        f"{area_code}-{exchange}-{subscriber}",
        f"+1 {area_code}-{exchange}-{subscriber}",
        f"{area_code}{exchange}{subscriber}",
    ]
    return random.choice(formats)


def generate_invalid_phone():
    """Generate an invalid phone number."""
    invalid_formats = [
        "123",
        "not-a-phone",
        "123-456",
        "12345678901234",
        "(000) 000-0000",
        "abc-def-ghij",
    ]
    return random.choice(invalid_formats)


def generate_date_pair():
    """Generate order_date and ship_date pair.

    Returns tuple (order_date, ship_date, is_valid).
    Most pairs are valid (ship_date >= order_date), some are invalid.
    """
    # Random order date in 2024
    start_date = datetime(2024, 1, 1)
    order_date = start_date + timedelta(days=random.randint(0, 364))

    # Ship date is usually 1-14 days after order
    ship_offset = random.randint(1, 14)
    ship_date = order_date + timedelta(days=ship_offset)

    return (
        order_date.strftime("%Y-%m-%d"),
        ship_date.strftime("%Y-%m-%d"),
        True
    )


def generate_invalid_date_pair():
    """Generate an invalid date pair where ship_date < order_date."""
    start_date = datetime(2024, 1, 1)
    order_date = start_date + timedelta(days=random.randint(30, 364))

    # Ship date BEFORE order date (invalid)
    ship_offset = random.randint(1, 10)
    ship_date = order_date - timedelta(days=ship_offset)

    return (
        order_date.strftime("%Y-%m-%d"),
        ship_date.strftime("%Y-%m-%d"),
        False
    )


def generate_invalid_date_format():
    """Generate date in wrong format."""
    invalid_formats = [
        "01/15/2024",  # MM/DD/YYYY instead of YYYY-MM-DD
        "15-01-2024",  # DD-MM-YYYY
        "2024/01/15",  # Wrong separator
        "Jan 15, 2024",
        "not-a-date",
    ]
    return random.choice(invalid_formats)


def generate_boolean():
    """Generate boolean value in Y/N format."""
    return random.choice(["Y", "N"])


def generate_inconsistent_boolean():
    """Generate boolean in inconsistent format."""
    formats = ["true", "false", "True", "False", "yes", "no", "1", "0"]
    return random.choice(formats)


def generate_row(row_id, inject_errors=False, error_types=None):
    """Generate a single row of data."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Default values (valid)
    order_id = row_id
    # Add leading/trailing whitespace to ~20% of names for cleaning demo
    customer_name = f"{first_name} {last_name}"
    if random.random() < 0.2:
        whitespace_type = random.choice(["leading", "trailing", "both"])
        if whitespace_type == "leading":
            customer_name = f"  {customer_name}"
        elif whitespace_type == "trailing":
            customer_name = f"{customer_name}  "
        else:
            customer_name = f"  {customer_name}  "
    email = generate_valid_email(first_name, last_name)
    phone = generate_valid_phone()
    quantity = random.randint(1, 100)
    unit_price = round(random.uniform(10.0, 500.0), 2)
    discount_pct = f"{random.randint(0, 30)}%"
    order_date, ship_date, _ = generate_date_pair()
    is_priority = generate_boolean()
    status = random.choice(VALID_STATUSES)
    state_code = random.choice(US_STATES)

    # Inject specific errors
    if inject_errors and error_types:
        for error_type in error_types:
            if error_type == "duplicate_id":
                order_id = random.randint(1, 50)  # Will create duplicates
            elif error_type == "null_name":
                customer_name = ""
            elif error_type == "invalid_email":
                email = generate_invalid_email()
            elif error_type == "invalid_phone":
                phone = generate_invalid_phone()
            elif error_type == "out_of_range_quantity":
                quantity = random.choice([-5, 0, 1500, 2000])
            elif error_type == "negative_price":
                unit_price = round(random.uniform(-100.0, -1.0), 2)
            elif error_type == "invalid_date_order":
                order_date, ship_date, _ = generate_invalid_date_pair()
            elif error_type == "invalid_date_format":
                if random.random() > 0.5:
                    order_date = generate_invalid_date_format()
                else:
                    ship_date = generate_invalid_date_format()
            elif error_type == "inconsistent_boolean":
                is_priority = generate_inconsistent_boolean()
            elif error_type == "invalid_status":
                status = random.choice(INVALID_STATUSES)
            elif error_type == "invalid_state":
                state_code = random.choice(INVALID_STATES)

    return {
        "order_id": order_id,
        "customer_name": customer_name,
        "email": email,
        "phone": phone,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_pct": discount_pct,
        "order_date": order_date,
        "ship_date": ship_date,
        "is_priority": is_priority,
        "status": status,
        "state_code": state_code,
    }


def main():
    """Generate the demo dataset."""
    rows = []

    # Error injection schedule
    # We want ~150 total errors spread across different types
    error_schedule = {
        # (start_row, end_row): [error_types]
        (10, 20): ["duplicate_id"],
        (25, 40): ["null_name"],
        (50, 75): ["invalid_email"],
        (80, 100): ["invalid_phone"],
        (110, 125): ["out_of_range_quantity"],
        (130, 140): ["negative_price"],
        (150, 170): ["invalid_date_order"],
        (180, 190): ["invalid_date_format"],
        (200, 220): ["inconsistent_boolean"],
        (230, 245): ["invalid_status"],
        (250, 260): ["invalid_state"],
        # Second round of errors
        (300, 310): ["invalid_email"],
        (320, 330): ["invalid_phone"],
        (350, 360): ["invalid_date_order"],
        (400, 410): ["invalid_status"],
        (450, 455): ["invalid_state"],
    }

    for i in range(1, NUM_ROWS + 1):
        # Check if this row should have errors
        error_types = None
        for (start, end), errors in error_schedule.items():
            if start <= i <= end:
                error_types = errors
                break

        row = generate_row(i, inject_errors=error_types is not None, error_types=error_types)
        rows.append(row)

    # Write to CSV
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    fieldnames = [
        "order_id", "customer_name", "email", "phone", "quantity",
        "unit_price", "discount_pct", "order_date", "ship_date",
        "is_priority", "status", "state_code"
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows to {OUTPUT_PATH}")

    # Print error summary
    print("\nError Summary:")
    total_errors = 0
    for (start, end), errors in error_schedule.items():
        count = end - start + 1
        total_errors += count
        print(f"  Rows {start}-{end}: {', '.join(errors)} ({count} rows)")
    print(f"\nTotal rows with errors: ~{total_errors}")


if __name__ == "__main__":
    main()
