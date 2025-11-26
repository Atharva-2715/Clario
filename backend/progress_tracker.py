# backend/progress_tracker.py

# In-memory database for student progress (simulating a DB/JSON file)
STUDENT_PROFILES = {
    "default_student": {
        "topics": {
            # Initialize with low accuracy/unknown strength for new topics
            "AI": {"accuracy": 0, "strength": "unknown"},
            "Probability": {"accuracy": 0, "strength": "unknown"},
            "Physics - Mechanics": {"accuracy": 0, "strength": "unknown"},
        },
        "last_interaction": None
    }
}

def get_student_profile(student_id: str = "default_student"):
    """
    Fetches the progress profile for a student.
    Initializes a new profile if the ID doesn't exist.
    """
    if student_id not in STUDENT_PROFILES:
        # Create a deep copy of the default profile for a new student
        STUDENT_PROFILES[student_id] = {
            "topics": {
                "AI": {"accuracy": 0, "strength": "unknown"},
                "Probability": {"accuracy": 0, "strength": "unknown"},
                "Physics - Mechanics": {"accuracy": 0, "strength": "unknown"},
            },
            "last_interaction": None
        }
        
    return STUDENT_PROFILES[student_id]

def update_student_profile(student_id: str, topic: str, correct_count: int, total_count: int):
    """
    Updates a student's topic strength based on quiz results.
    """
    profile = get_student_profile(student_id)
    
    # Ensure the topic exists in the profile
    if topic not in profile["topics"]:
        profile["topics"][topic] = {"accuracy": 0, "strength": "unknown"}
    
    current_topic = profile["topics"][topic]
    
    # Calculate performance from the latest quiz
    latest_performance = correct_count / total_count
    
    # Simple weighted average update (weighs new score equally with current average)
    if current_topic["strength"] == "unknown":
        new_accuracy = latest_performance * 100
    else:
        # 70% weight to current average, 30% to new performance
        new_accuracy = (current_topic["accuracy"] * 0.7) + (latest_performance * 100 * 0.3)
        
    new_accuracy = round(min(new_accuracy, 100)) # Cap at 100
    
    if new_accuracy >= 80:
        strength = "strong"
    elif new_accuracy >= 50:
        strength = "average"
    else:
        strength = "weak"

    profile["topics"][topic] = {
        "accuracy": new_accuracy,
        "strength": strength
    }
    profile["last_interaction"] = f"quiz_completed_on_{topic}"
    
    # Update the global store (for in-memory tracking)
    STUDENT_PROFILES[student_id] = profile
    return profile