from flask import Flask, render_template, request, jsonify
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_db_connection
from datetime import date, datetime, timedelta
import os

# ------------------------------
# GEMINI AI IMPORT
# ------------------------------
import google.generativeai as genai
app = Flask(__name__)
# ------------------------------
# GEMINI CONFIG
# ------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not set in environment!")
genai.configure(api_key=GEMINI_API_KEY)
# ------------------------------
# EMAIL CONFIGURATION (SOS)
# ------------------------------
EMAIL_ADDRESS = "sharwaridake@gmail.com"        # Replace with your email
EMAIL_PASSWORD = "ctfy cysp xcmf tmvl"          # Gmail App password recommended

def send_med_email(to_email, med_name, med_time):
    msg = MIMEText(
        f"⏰ Time to take your medicine: {med_name}\nScheduled at: {med_time}"
    )
    msg["Subject"] = "Medication Reminder 💊"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

# -------------------------------------------------
# HOME & PAGES
# -------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/templates/header")
def header_templates():
    return render_template("header.html")

@app.route("/progress")   
def progress():
    return render_template("progress.html")

@app.route("/medication-page")
def medication_page():
    return render_template("medication.html")

@app.route("/water-tracker")
def water_page():
    return render_template("water.html")

@app.route("/sos")
def sos_page():
    return render_template("sos.html")

@app.route("/tips")
def tips_page():
    return render_template("tips.html")

@app.route('/exercise')
def exercise():
    return render_template('exercise.html')

@app.route('/memory')
def memory():
    return render_template('memory.html')

@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # ---------- GET ----------
        if request.method == "GET":
            user_id = request.args.get("user_id")
            if not user_id:
                return jsonify({"error": "User ID missing"}), 400

            user_id = int(user_id)   # 🔥 FIX 1

            cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
            profile = cursor.fetchone()
            if not profile:
                return jsonify({"error": "Profile not found"}), 404

            return jsonify(profile)

        # ---------- POST ----------
        data = request.json or {}
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID missing"}), 400

        user_id = int(user_id)   # 🔥 FIX 2

        cursor.execute("SELECT id FROM user_profile WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()

        if row:
            cursor.execute("""
                UPDATE user_profile SET
                    name=%s, age=%s, gender=%s, contact=%s,
                    weight=%s, height=%s, conditions=%s, allergies=%s,
                    sleep_hours=%s, water_goal=%s,
                    exercise_frequency=%s, diet=%s, activities=%s, goals=%s
                WHERE user_id=%s
            """, (
                data.get("name"), data.get("age"), data.get("gender"),
                data.get("contact"), data.get("weight"), data.get("height"),
                data.get("conditions"), data.get("allergies"),
                data.get("sleep_hours"), data.get("water_goal"),
                data.get("exercise_frequency"), data.get("diet"),
                data.get("activities"), data.get("goals"),
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profile
                (user_id, name, age, gender, contact, weight, height,
                 conditions, allergies, sleep_hours, water_goal,
                 exercise_frequency, diet, activities, goals)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id,
                data.get("name"), data.get("age"), data.get("gender"),
                data.get("contact"), data.get("weight"), data.get("height"),
                data.get("conditions"), data.get("allergies"),
                data.get("sleep_hours"), data.get("water_goal"),
                data.get("exercise_frequency"), data.get("diet"),
                data.get("activities"), data.get("goals")
            ))

        conn.commit()

        cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
        return jsonify(cursor.fetchone())

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==========================
# Progress Data API (Dummy Charts)
# ==========================
@app.route("/api/progress-data")
def progress_data():
    user_id = request.args.get("user_id")  # keep for frontend

    return jsonify({
        "water": 6,
        "exercise": 3,
        "games": 4,
        "medication": 2,
        "streaks": {
            "Health Check-in": 5,
            "Medication": 2,
            "Water": 6,
            "Exercise": 3,
            "Memory Game": 4,
            "Health Tips": 7
        }
    })

# ----------------------------
# MEMORY GAME ROUTES
# ----------------------------

# Add a new game session
@app.route("/memory_game/session", methods=["POST"])
def add_session():
    data = request.json
    user_id = data.get("user_id")
    game_mode = data.get("game_mode")
    difficulty = data.get("difficulty")
    moves = data.get("moves")
    time_taken = data.get("time_taken")
    stars = data.get("stars", 0)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # -------------------------
        # Insert session
        # -------------------------
        cursor.execute(
            """
            INSERT INTO memory_game_sessions
            (user_id, game_mode, difficulty, moves, time_taken, stars)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (user_id, game_mode, difficulty, moves, time_taken, stars)
        )

        # -------------------------
        # Update best scores
        # -------------------------
        cursor.execute(
            "SELECT best_moves, best_time FROM memory_game_best_scores WHERE user_id=%s AND game_mode=%s AND difficulty=%s",
            (user_id, game_mode, difficulty)
        )
        result = cursor.fetchone()
        if result:
            best_moves, best_time = result["best_moves"], result["best_time"]
            new_best_moves = moves if (best_moves is None or moves < best_moves) else best_moves
            new_best_time = time_taken if (best_time is None or time_taken < best_time) else best_time
            cursor.execute(
                """
                UPDATE memory_game_best_scores
                SET best_moves=%s, best_time=%s, updated_at=NOW()
                WHERE user_id=%s AND game_mode=%s AND difficulty=%s
                """,
                (new_best_moves, new_best_time, user_id, game_mode, difficulty)
            )
        else:
            cursor.execute(
                """
                INSERT INTO memory_game_best_scores
                (user_id, game_mode, difficulty, best_moves, best_time)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (user_id, game_mode, difficulty, moves, time_taken)
            )

        # -------------------------
        # Update streaks
        # -------------------------
        today = date.today()
        cursor.execute(
            "SELECT current_streak, last_played, longest_streak FROM memory_game_streaks WHERE user_id=%s",
            (user_id,)
        )
        streak = cursor.fetchone()
        if streak:
            current_streak, last_played, longest_streak = streak["current_streak"], streak["last_played"], streak["longest_streak"]
            if last_played == today:
                pass  # already played today
            elif last_played == today - timedelta(days=1):
                current_streak += 1
            else:
                current_streak = 1  # reset streak
            longest_streak = max(longest_streak, current_streak)
            cursor.execute(
                """
                UPDATE memory_game_streaks
                SET current_streak=%s, last_played=%s, longest_streak=%s
                WHERE user_id=%s
                """,
                (current_streak, today, longest_streak, user_id)
            )
        else:
            current_streak = 1
            cursor.execute(
                """
                INSERT INTO memory_game_streaks
                (user_id, current_streak, last_played, longest_streak)
                VALUES (%s,%s,%s,%s)
                """,
                (user_id, 1, today, 1)
            )

        conn.commit()

        # Fetch updated values to return to frontend
        cursor.execute(
            "SELECT best_moves FROM memory_game_best_scores WHERE user_id=%s AND game_mode=%s AND difficulty=%s",
            (user_id, game_mode, difficulty)
        )
        best_moves = cursor.fetchone()["best_moves"]

        cursor.execute(
            "SELECT current_streak FROM memory_game_streaks WHERE user_id=%s",
            (user_id,)
        )
        current_streak = cursor.fetchone()["current_streak"]

        return jsonify({
            "message": "Session recorded, scores and streaks updated",
            "best_moves": best_moves,
            "current_streak": current_streak
        }), 201

    finally:
        cursor.close()
        conn.close()


# Get best scores
@app.route("/memory_game/best_scores/<int:user_id>", methods=["GET"])
def get_best_scores(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memory_game_best_scores WHERE user_id=%s", (user_id,))
    scores = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(scores)


# Get current streak
@app.route("/memory_game/streak/<int:user_id>", methods=["GET"])
def get_streak(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memory_game_streaks WHERE user_id=%s", (user_id,))
    streak = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(streak if streak else {"message": "No streak found"})


# ------------------------------
# ROUTE TO LOG EXERCISE ACTIVITY
# ------------------------------
@app.route("/log_exercise", methods=["POST"])
def log_exercise():
    data = request.get_json()
    user_id = data.get("user_id")
    level = data.get("level")
    exercise_name = data.get("exercise_name")
    category = data.get("category")
    
    if not all([user_id, level, exercise_name, category]):
        return jsonify({"status": "error", "message": "Missing data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO user_exercise_activity (user_id, level, exercise_name, category, completed_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, level, exercise_name, category, datetime.now())
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"status": "success", "message": "Exercise logged successfully"})

# -------------------------------------------------
# DAILY HEALTH AI TIPS (GEMINI)
# -------------------------------------------------
@app.route("/api/daily-tips", methods=["POST"])
def daily_tips():
    try:
        data = request.get_json()

        prompt = f"""
        User daily health summary:
        Mood: {data.get("mood")}
        Feeling tired: {data.get("tired")}
        Body pain: {data.get("pain")}
        Dizziness: {data.get("dizzy")}
        Sleep quality: {data.get("slept")}

        Give 5 short, friendly daily health tips.
        """

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        tips = [
            line.strip("-•123. ")
            for line in response.text.split("\n")
            if line.strip()
        ]

        return jsonify({"tips": tips})

    except Exception as e:
        print("GEMINI ERROR:", e)
        return jsonify({"tips": ["Take rest, drink water, and stay calm today."]})

# -------------------------------------------------
# DAILY HEALTH CHECK-IN
# -------------------------------------------------
@app.route("/daily-health", methods=["GET", "POST"])
def daily_health():
    if request.method == "POST":
        data = request.get_json()
        required = ["user_id", "mood", "tired", "pain", "dizzy", "slept"]

        if not all(data.get(k) is not None for k in required):
            return jsonify({"error": "Missing daily health data"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO daily_health (user_id, mood, tired, pain, dizzy, slept)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                data["user_id"], data["mood"], data["tired"],
                data["pain"], data["dizzy"], data["slept"]
            ))
            conn.commit()
            return jsonify({"message": "Daily health saved"}), 201
        finally:
            cursor.close()
            conn.close()

    return render_template("daily-health.html")

# -------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(force=True)
    print("SIGNUP DATA RECEIVED:", data)


    if data.get("captcha", "").lower() != data.get("captchaActual", "").lower():
        return jsonify({"error": "Invalid CAPTCHA"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM users WHERE username=%s OR email=%s",
            (data["username"], data["email"])
        )
        if cursor.fetchone():
            return jsonify({"error": "User already exists"}), 409

        cursor.execute("""
            INSERT INTO users (username, email, password, age, gender)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            data["username"],
            data["email"],
            generate_password_hash(data["password"]),
            int(data["age"]),
            data["gender"]
        ))
        conn.commit()
        return jsonify({"message": "Signup successful"}), 201
    finally:
        cursor.close()
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (data["username"],)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user["password"], data["password"]):
            return jsonify({
                "message": "Login successful",
                "user": {"id": user["id"],
                    "username": user["username"],
                    "age": user["age"],
                    "gender": user["gender"]}
            })

        return jsonify({"error": "Invalid credentials"}), 401
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------
# MEDICATION API
# -------------------------------------------------

@app.route("/api/medication", methods=["GET", "POST", "DELETE"])
def medication_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # -------------------------
        # ADD MEDICATION (SAVE)
        # -------------------------
        if request.method == "POST":
            data = request.get_json()

            cursor.execute("""
    INSERT INTO medications
    (user_id, reminder_email, name, dosage, time, frequency, duration, start_date)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""", (
    data["user_id"],
    data["reminder_email"],
    data["name"],
    data["dosage"],
    data["time"],
    data["frequency"],
    data["duration"],
    data["start_date"]
))

            conn.commit()
            return jsonify({"message": "Medication added"}), 201

        # -------------------------
        # FETCH MEDICATIONS
        # -------------------------
        if request.method == "GET":
            cursor.execute(
                "SELECT * FROM medications WHERE user_id=%s",
                (request.args.get("user_id"),)
            )
            return jsonify(cursor.fetchall())

        # -------------------------
        # DELETE MEDICATION
        # -------------------------
        if request.method == "DELETE":
            cursor.execute(
                "DELETE FROM medications WHERE id=%s",
                (request.args.get("id"),)
            )
            conn.commit()
            return jsonify({"message": "Deleted"})

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------
# UPDATE MEDICATION DURATION (TAKEN BUTTON)
# -------------------------------------------------
@app.route("/api/medication/update-duration", methods=["POST"])
def update_medication_duration():
    data = request.get_json()
    med_id = data["id"]
    new_duration = data["duration"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Reduce duration
        cursor.execute("""
            UPDATE medications
            SET duration=%s
            WHERE id=%s
        """, (new_duration, med_id))

        # Log TAKEN for today
        cursor.execute("""
            INSERT IGNORE INTO medication_logs
            (user_id, medication_id, status, log_date)
            SELECT user_id, id, 'taken', CURDATE()
            FROM medications WHERE id=%s
        """, (med_id,))

        conn.commit()
        return jsonify({"message": "Dose logged & duration updated"})
    finally:
        cursor.close()
        conn.close()
# -------------------------------------------------
# Missed Medication Logs 
# -------------------------------------------------
@app.route("/api/medication/log-missed", methods=["POST"])
def log_missed_medication():
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT IGNORE INTO medication_logs
            (user_id, medication_id, status, log_date)
            VALUES (%s,%s,'missed',CURDATE())
        """, (data["user_id"], data["medication_id"]))

        conn.commit()
        return jsonify({"message": "Missed logged"})
    finally:
        cursor.close()
        conn.close()

# -------------------------
# WATER STATUS (FRESH)
# -------------------------
@app.route("/api/water/status", methods=["GET"])
def get_water_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID missing"}), 400

    today = date.today()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Ensure a row exists for today
        cursor.execute(
            "SELECT goal_ml FROM water_intake WHERE user_id=%s AND intake_date=%s",
            (user_id, today)
        )
        row = cursor.fetchone()

        if not row:
            # Create a fresh row with 0 intake
            cursor.execute(
                "INSERT INTO water_intake (user_id, intake_date, total_intake_ml, goal_ml, goal_completed) "
                "VALUES (%s,%s,0,2000,0)",
                (user_id, today)
            )
            conn.commit()
            goal = 2000
        else:
            goal = row["goal_ml"]

        # Always return fresh status (0 intake, empty logs)
        return jsonify({
            "currentIntake": 0,
            "goal": goal,
            "logs": []
        })

    finally:
        cursor.close()
        conn.close()


# -------------------------
# ADD WATER
# -------------------------
@app.route("/api/water/add", methods=["POST"])
def add_water():
    data = request.get_json()
    user_id = data.get("user_id")
    amount = int(data.get("amount_ml", 0))
    today = date.today()

    if not user_id or amount <= 0:
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Ensure today's row exists
        cursor.execute(
            "SELECT total_intake_ml, goal_ml FROM water_intake WHERE user_id=%s AND intake_date=%s",
            (user_id, today)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO water_intake (user_id, intake_date, total_intake_ml, goal_ml, goal_completed) "
                "VALUES (%s,%s,0,2000,0)",
                (user_id, today)
            )
            total, goal = 0, 2000
        else:
            total, goal = row["total_intake_ml"], row["goal_ml"]

        # Add water
        total += amount
        goal_completed = 1 if total >= goal else 0

        cursor.execute(
            "UPDATE water_intake SET total_intake_ml=%s, goal_completed=%s WHERE user_id=%s AND intake_date=%s",
            (total, goal_completed, user_id, today)
        )

        # Log water normally
        cursor.execute(
            "INSERT INTO water_logs (user_id, intake_date, intake_time, amount_ml) VALUES (%s,%s,CURTIME(),%s)",
            (user_id, today, amount)
        )

        # Update hydration streak if goal reached
        if total >= goal:
            cursor.execute(
                "SELECT current_streak, last_completed_date FROM hydration_streak WHERE user_id=%s",
                (user_id,)
            )
            streak_row = cursor.fetchone()
            if streak_row:
                last_date, current_streak = streak_row["last_completed_date"], streak_row["current_streak"]
                if isinstance(last_date, str):
                    last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
                if last_date != today:
                    current_streak = current_streak + 1 if last_date == today - timedelta(days=1) else 1
                    cursor.execute(
                        "UPDATE hydration_streak SET current_streak=%s, last_completed_date=%s WHERE user_id=%s",
                        (current_streak, today, user_id)
                    )
            else:
                cursor.execute(
                    "INSERT INTO hydration_streak (user_id, current_streak, last_completed_date) VALUES (%s,1,%s)",
                    (user_id, today)
                )

        conn.commit()
        return jsonify({"message": "Water added", "total": total})
    finally:
        cursor.close()
        conn.close()


# -------------------------
# SET GOAL
# -------------------------
@app.route("/api/water/set-goal", methods=["POST"])
def set_goal():
    data = request.get_json()
    user_id = data.get("user_id")
    goal = int(data.get("goal_ml", 2000))
    today = date.today()

    if not user_id:
        return jsonify({"error": "User ID missing"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO water_intake (user_id,intake_date,total_intake_ml,goal_ml,goal_completed)
               VALUES (%s,%s,0,%s,0)
               ON DUPLICATE KEY UPDATE goal_ml=%s, total_intake_ml=0""",
            (user_id, today, goal, goal)
        )
        conn.commit()
        return jsonify({"message": "Goal updated", "goal": goal})
    finally:
        cursor.close()
        conn.close()

# ------------------------------
# SOS
# ------------------------------
# ------------------------------
# SAVE CONTACTS
# ------------------------------
@app.route("/api/sos/save-contacts", methods=["POST"])
def save_sos_contacts():
    data = request.get_json()
    user_id = data.get("user_id")
    contact1_name = data.get("contact1_name")
    contact1_email = data.get("contact1_email")
    contact2_name = data.get("contact2_name")
    contact2_email = data.get("contact2_email")

    if not user_id or not contact1_name or not contact1_email or not contact2_name or not contact2_email:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO emergency_contacts
            (user_id, contact1_name, contact1_email, contact2_name, contact2_email, created_at)
            VALUES (%s,%s,%s,%s,%s,NOW())
            ON DUPLICATE KEY UPDATE
                contact1_name=VALUES(contact1_name),
                contact1_email=VALUES(contact1_email),
                contact2_name=VALUES(contact2_name),
                contact2_email=VALUES(contact2_email),
                created_at=NOW()
        """, (
            user_id, contact1_name, contact1_email, contact2_name, contact2_email
        ))
        conn.commit()
        return jsonify({"status": "success", "message": "Contacts saved successfully"})
    except Exception as e:
        print("DB ERROR:", str(e))
        return jsonify({"status": "error", "message": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()


# ------------------------------
# GET CONTACTS
# ------------------------------
@app.route("/api/sos/get-contacts", methods=["GET"])
def get_sos_contacts():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "user_id missing"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM emergency_contacts WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()
        return jsonify({"status": "success", "contacts": row})
    finally:
        cursor.close()
        conn.close()


# ------------------------------
# SEND SOS EMAIL
# ------------------------------
@app.route("/send-sos", methods=["POST"])
def send_sos():
    try:
        data = request.get_json()
        contact_email = data.get("contact_email")  # comma-separated emails
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not contact_email:
            return jsonify({"status": "error", "message": "No contact email provided"}), 400

        subject = "🚨 Emergency SOS Alert 🚨"
        body = "Emergency alert! Please respond immediately."

        if latitude and longitude:
            body += f"\n\nUser Location: https://www.google.com/maps?q={latitude},{longitude}"

        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = contact_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"🚨 SOS email sent to {contact_email} 🚨")
        return jsonify({"status": "success", "message": f"SOS email sent to {contact_email}"})
    except Exception as e:
        print("SEND SOS ERROR:", str(e))
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# ------------------------------
# medication email related 
# ------------------------------
def medication_scheduler():
    while True:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now_time = datetime.now().strftime("%H:%M")
        today = datetime.now().date()

        cursor.execute("""
            SELECT * FROM medications
            WHERE time=%s AND duration>0 AND start_date<=%s
        """, (now_time, today))

        meds = cursor.fetchall()

        for med in meds:
            send_med_email(
                med["reminder_email"],
                med["name"],
                med["time"]
            )

        cursor.close()
        conn.close()
        time.sleep(60)
    
# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=medication_scheduler)
    t.daemon = True
    t.start()

    app.run(debug=True)

