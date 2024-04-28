from flask import Blueprint, request, jsonify, session, redirect, url_for
from datetime import timedelta, datetime
import datetime
from model import model
import traceback
from pymongo import MongoClient

recommend_bp = Blueprint("recommend", __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["db_reachOut"]
collection = db["journal"]
appointments_collection = db["appointment"]
mood_collection = db["mood"]


@recommend_bp.route("/recommendation", methods=["POST"])
def recommendation():
    try:
        form_data = request.get_json()
        userAge = session.get("age")
        userGender = 1 if session.get("gender") == "male" else 2

        # Extract the feature values from the form data
        Q1_Stress = form_data.get("stress")
        Q2_Anxiety = form_data.get("anxiety")
        Q3_Depression = form_data.get("depression")
        Q4_Sleep = form_data.get("sleep")
        Q5_Social = form_data.get("social")

        # Store the form data values in the session

        # Create a feature vector
        feature_vector = [
            [
                userAge,
                userGender,
                Q1_Stress,
                Q2_Anxiety,
                Q3_Depression,
                Q4_Sleep,
                Q5_Social,
            ]
        ]

        # Make a prediction using the trained model
        prediction = model.predict(feature_vector)[0]

        if prediction == "Counseling":
            recommendation = [
                ["fas fa-comments", "Seek counseling:"],
                ["fas fa-search", "1. Look up counseling services nearby."],
                ["fas fa-phone", "2. Call to schedule an appointment."],
                ["fas fa-pencil-alt", "3. Prepare by jotting down your thoughts."]
            ]
        elif prediction == "Exercise":
            recommendation = [
                ["fas fa-running", "Incorporate exercise:"],
                ["fas fa-smile", "1. Choose an activity you enjoy."],
                ["fas fa-calendar-alt", "2. Set a schedule."],
                ["fas fa-bullseye", "3. Start with small goals."]
            ]
        elif prediction == "Therapy":
            recommendation = [
                ["fas fa-user-md", "Explore therapy:"],
                ["fas fa-search", "1. Research therapy options."],
                ["fas fa-user-friends", "2. Find a therapist."],
                ["fas fa-calendar-check", "3. Schedule a consultation."]
            ]
        elif prediction == "Mindfulness":
            recommendation = [
                ["fas fa-eye", "Practice mindfulness:"],
                ["fas fa-leaf", "1. Start with deep breathing."],
                ["fas fa-mobile-alt", "2. Use mindfulness apps."],
                ["fas fa-clock", "3. Set aside time daily."]
            ]
        elif prediction == "Support Group":
            recommendation = [
                ["fas fa-users", "Join a support group:"],
                ["fas fa-search", "1. Search for groups online."],
                ["fas fa-door-open", "2. Attend a meeting."],
                ["fas fa-comments", "3. Share your experiences."]
            ]
        elif prediction == "Stress Management":
            recommendation = [
                ["fas fa-brain", "Manage stress:"],
                ["fas fa-lightbulb", "1. Identify stressors."],
                ["fas fa-spa", "2. Use relaxation techniques."],
                ["fas fa-list-ol", "3. Prioritize tasks."]
            ]
        elif prediction == "Physical Activity":
            recommendation = [
                ["fas fa-walking", "Engage in physical activity:"],
                ["fas fa-shoe-prints", "1. Take short walks."],
                ["fas fa-music", "2. Dance to music."],
                ["fas fa-football-ball", "3. Play a sport."]
            ]
        elif prediction == "Psychotherapy":
            recommendation = [
                ["fas fa-user-md", "Consider psychotherapy:"],
                ["fas fa-search", "1. Find a psychotherapist."],
                ["fas fa-calendar-plus", "2. Schedule an appointment."],
                ["fas fa-comments", "3. Discuss your concerns."]
            ]
        elif prediction == "Yoga":
            recommendation = [
                ["fas fa-yoga", "Incorporate yoga:"],
                ["fas fa-video", "1. Watch beginner videos."],
                ["fas fa-male", "2. Start with basic poses."],
                ["fas fa-sync-alt", "3. Practice regularly."]
            ]
        elif prediction == "Social Support":
            recommendation = [
                ["fas fa-user-friends", "Seek social support:"],
                ["fas fa-comments", "1. Reach out to friends."],
                ["fas fa-users", "2. Join social clubs."],
                ["fas fa-calendar-alt", "3. Attend community events."]
            ]
        elif prediction == "Meditation":
            recommendation = [
                ["fas fa-om", "Practice meditation:"],
                ["fas fa-home", "1. Find a quiet space."],
                ["fas fa-lung", "2. Focus on your breath."],
                ["fas fa-hourglass-start", "3. Start with short sessions."]
            ]
        elif prediction == "Life Coach":
            recommendation = [
                ["fas fa-user-tie", "Work with a life coach:"],
                ["fas fa-search", "1. Research coaches."],
                ["fas fa-calendar-alt", "2. Schedule a consultation."],
                ["fas fa-bullseye", "3. Set goals together."]
            ]
        elif prediction == "Group Therapy":
            recommendation = [
                ["fas fa-users", "Explore group therapy:"],
                ["fas fa-search", "1. Find local groups."],
                ["fas fa-door-open", "2. Attend a session."],
                ["fas fa-comments", "3. Participate actively."]
            ]
        elif prediction == "Time Management":
            recommendation = [
                ["fas fa-clock", "Manage your time:"],
                ["fas fa-list-ol", "1. Make to-do lists."],
                ["fas fa-calendar-alt", "2. Set deadlines."],
                ["fas fa-tachometer-alt", "3. Prioritize tasks."]
            ]
        elif prediction == "CBT (Cognitive Behavioral Therapy)":
            recommendation = [
                ["fas fa-brain", "Try CBT:"],
                ["fas fa-book-reader", "1. Learn about CBT techniques."],
                ["fas fa-arrows-alt", "2. Apply them to your daily life."],
                ["fas fa-user-friends", "3. Seek guidance if needed."]
            ]
        elif prediction == "Self-Care":
            recommendation = [
                ["fas fa-heart", "Prioritize self-care:"],
                ["fas fa-calendar-alt", "1. Schedule 'me' time."],
                ["fas fa-smile", "2. Do activities you enjoy."],
                ["fas fa-hand-holding-heart", "3. Practice self-compassion."]
            ]
        else:
            recommendation = [["fas fa-exclamation-circle", "The recommendation is not recognized."]]


        user_id = session.get("uid")
        mood_data = {
            "user_id": user_id,
            "stress": Q1_Stress,
            "anxiety": Q2_Anxiety,
            "depression": Q3_Depression,
            "sleep": Q4_Sleep,
            "social": Q5_Social,
            "recommendation": recommendation,
            "mood_date": datetime.date.today().isoformat(),
        }
        mood_collection.insert_one(mood_data)

        # Redirect to the /user route
        return redirect(url_for("user"))

    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500