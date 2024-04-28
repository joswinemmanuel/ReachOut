from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for,
)
from pymongo import MongoClient
from datetime import datetime, time, timedelta
from bson.objectid import ObjectId
import traceback
from collections import OrderedDict
from calendar import month_abbr

counselor_bp = Blueprint(
    "counselor",
    __name__,
)


client = MongoClient("mongodb://localhost:27017/")
db = client["db_reachOut"]
appointments_collection = db["appointment"]


@counselor_bp.route("/counselor")
def counselor():
    pending_appointments = get_pending_appointments()
    confirmed_appointments = get_confirmed_appointments()
    completed_appointments = list(appointments_collection.find({"status": "completed"}))
    completed_appointments_count = len(completed_appointments)

    if session.get("counsellor") != True:
        return redirect(url_for("signin"))

    return render_template(
        "counsellor.html",
        pending_appointments=pending_appointments,
        confirmed_appointments=confirmed_appointments,
        completed_appointments=completed_appointments,
        completed_appointments_count=completed_appointments_count,
    )


def get_pending_appointments():
    pending_appointments = appointments_collection.find({"status": "pending"})
    return list(pending_appointments)


@counselor_bp.route("/get_available_slots", methods=["POST"])
def get_available_slots():
    # Get the current date
    today = datetime.now().date()

    # Get the start date (tomorrow)
    start_date = today + timedelta(days=1)

    # Adjust the start date to the next Monday if it's a weekend
    while start_date.weekday() > 4:  # Weekday > 4 means it's Saturday or Sunday
        start_date += timedelta(days=1)

    # Get the end date (7 weekdays from the start date)
    end_date = start_date + timedelta(days=6)

    # Initialize an empty list to store available slots for the next 7 weekdays
    available_slots_week = []

    # Loop through the next 7 weekdays
    current_date = start_date
    while current_date <= end_date:
        # Generate all possible time slots for the current day
        all_slots = []

        # Morning slots
        for start_hour in range(9, 13):
            start_time = datetime.combine(current_date, time(start_hour, 0))
            end_time = datetime.combine(current_date, time(start_hour + 1, 0))
            all_slots.append({
                "start": start_time,
                "end": end_time
            })

        # Afternoon slots
        for start_hour in range(14, 16):
            start_time = datetime.combine(current_date, time(start_hour, 30))
            end_time = datetime.combine(current_date, time(start_hour + 1, 30))
            all_slots.append({
                "start": start_time,
                "end": end_time
            })

        # Get all appointments for the current day
        existing_appointments = list(appointments_collection.find({
            "$or": [
                {
                    "AppDate": {
                        "$gte": datetime.combine(current_date, time(0, 0)),
                        "$lt": datetime.combine(current_date, time(23, 59))
                    }
                },
                {
                    "AppEndDate": {
                        "$gte": datetime.combine(current_date, time(0, 0)),
                        "$lt": datetime.combine(current_date, time(23, 59))
                    }
                }
            ]
        }))

        # Remove existing appointments from the list of all slots
        available_slots = []
        for slot in all_slots:
            slot_start = slot["start"]
            slot_end = slot["end"]
            if not any(appt.get("AppDate") <= slot_start < appt.get("AppEndDate") or
                       appt.get("AppDate") < slot_end <= appt.get("AppEndDate") for appt in existing_appointments):
                available_slots.append({
                    "start": f"{slot_start.strftime('%m/%d/%Y %I:%M %p')}",
                    "end": f"{slot_end.strftime('%m/%d/%Y %I:%M %p')}",
                })

        # Add the available slots for the current day to the list for the week
        available_slots_week.extend(available_slots)

        # Move to the next weekday
        current_date += timedelta(days=1)

    # Sort the available slots in chronological order
    available_slots_week.sort(key=lambda x: datetime.strptime(x["start"], "%m/%d/%Y %I:%M %p"))

    return jsonify(available_slots_week)


@counselor_bp.route("/update_appointment", methods=["POST"])
def update_appointment():
    appointment_id = request.form.get("appointment_id")
    slot_start_datetime_str = request.form.get("slot_start_datetime")
    print(slot_start_datetime_str)
    if slot_start_datetime_str is None:
        return jsonify({"error": "Missing slot_start_datetime"}), 400

    try:
        slot_start_datetime_str = slot_start_datetime_str.replace('Z', '')
        slot_start_datetime = datetime.fromisoformat(slot_start_datetime_str)
        slot_start_datetime += timedelta(hours=5, minutes=30)

        slot_end_datetime = slot_start_datetime + timedelta(hours=1)

        print(
            f"Updating appointment {appointment_id} with start time: {slot_start_datetime} and end time: {slot_end_datetime}"
        )

        # Update the appointment in the database
        result = appointments_collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "AppDate": slot_start_datetime,
                    "AppEndDate": slot_end_datetime,
                    "status": "confirmed",
                }
            },
        )

        print(f"Update result: {result.raw_result}")

        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating appointment: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


def get_confirmed_appointments():
    confirmed_appointments = appointments_collection.find({"status": "confirmed"})
    return list(confirmed_appointments)


@counselor_bp.route("/save_report", methods=["POST"])
def save_report():
    appointment_id = request.form.get("appointment_id")
    private_notes = request.form.get("private_notes")
    student_notes = request.form.get("student_notes")

    # Check if appointment_id is valid
    if not appointment_id or not ObjectId.is_valid(appointment_id):
        print(f"Invalid appointment_id: {appointment_id}")
        return jsonify({"error": "Invalid appointment ID"}), 400

    try:
        # Update the appointment in the database with the notes
        result = appointments_collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "private_notes": private_notes,
                    "student_notes": student_notes,
                    "status": "completed",
                }
            },
        )

        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving report: {e}")
        return jsonify({"error": str(e)}), 500
