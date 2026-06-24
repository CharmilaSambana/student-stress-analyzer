from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
from flask import Flask, render_template, request, session, redirect
import csv
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = "secret123"

# -------- CREATE USERS FILE --------
if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password"])

# -------- CREATE HISTORY FILE --------
if not os.path.exists("history.csv"):
    with open("history.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Score", "Stress Level", "Risk %"])

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return "Passwords do not match"

        hashed_password = generate_password_hash(password)

        with open('users.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, hashed_password])

        return redirect('/login')

    return render_template('register.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with open('users.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row[0] == username and check_password_hash(row[1], password):
                    session['user'] = username
                    return redirect('/')

        return "Invalid Credentials"

    return render_template('login.html')

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# -------- HOME --------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template("index.html", user=session['user'])

# -------- RESULT PAGE --------
@app.route('/result')
def result_page():
    if 'user' not in session:
        return redirect('/login')

    if 'result' not in session:
        return redirect('/')

    return render_template(
    "result.html",
    result=session.get('result'),
    score=session.get('score', 0),
    risk_percentage=session.get('risk', 0),
    features=session.get('features', []),
    color=session.get('color', 'black'),
    reasons=session.get('reasons', []),
    suggestions=session.get('suggestions', []),
    explanation=session.get('explanation', ''),
    user=session.get('user')
     )
    
# -------- PREDICT --------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect('/login')

    sleep = int(request.form['sleep'])
    study = int(request.form['study'])
    exam = int(request.form['exam'])
    workload = int(request.form['workload'])
    concentration = int(request.form['concentration'])
    screen = int(request.form['screen'])
    physical = int(request.form['physical'])
    sleep_quality = int(request.form['sleep_quality'])
    emotional = int(request.form['emotional'])
    routine = int(request.form['routine'])
    breaks = int(request.form['breaks'])
    support = int(request.form['support'])

    score = sum([
        sleep, study, exam, workload,
        concentration, screen, physical,
        sleep_quality, emotional, routine,
        breaks, support
    ])

    if score > 32:
        score = 32

    if score <= 10:
        result = "Low"
        color = "green"
    elif score <= 20:
        result = "Moderate"
        color = "orange"
    else:
        result = "High"
        color = "red"

    reasons = []
    suggestions = []

# 😴 Sleep
    if sleep >= 2:
        reasons.append("Poor sleep duration affecting brain recovery")
        suggestions.append("Maintain consistent 7–8 hours sleep schedule")

# 📚 Study Pressure
    if study >= 2:
        reasons.append("High study pressure causing mental fatigue")
        suggestions.append("Use Pomodoro technique (25 min focus + 5 min break)")

# 📝 Exams
    if exam >= 2:
        reasons.append("Exam anxiety increasing stress levels")
        suggestions.append("Practice mock tests & breathing exercises")

# 📦 Workload
    if workload >= 2:
        reasons.append("Heavy workload causing burnout risk")
        suggestions.append("Break tasks into smaller manageable goals")

# 🎯 Concentration
    if concentration >= 2:
        reasons.append("Low concentration affecting productivity")
        suggestions.append("Avoid distractions & use focus apps")

# 📱 Screen Time
    if screen >= 2:
        reasons.append("Excess screen time causing mental strain")
        suggestions.append("Limit screen usage & follow 20-20-20 rule")

# 🏃 Physical Activity
    if physical >= 2:
        reasons.append("Lack of physical activity reducing energy levels")
        suggestions.append("Do at least 30 mins exercise daily")

# 🛌 Sleep Quality
    if sleep_quality >= 2:
        reasons.append("Poor sleep quality affecting mood & focus")
        suggestions.append("Avoid mobile before sleep")

# 😔 Emotional Health
    if emotional >= 2:
        reasons.append("Emotional imbalance increasing stress")
        suggestions.append("Talk to friends/family or journal feelings")

# 🔄 Routine
    if routine >= 2:
        reasons.append("Irregular daily routine causing instability")
        suggestions.append("Maintain a fixed daily schedule")

# ☕ Breaks
    if breaks >= 2:
        reasons.append("Lack of breaks leading to burnout")
        suggestions.append("Take short breaks between tasks")

# 🤝 Support
    if support >= 2:
        reasons.append("Lack of support system increasing pressure")
        suggestions.append("Seek help from mentors or friends")

# ✅ Default case
    if len(reasons) == 0:
        reasons.append("You are maintaining a healthy lifestyle")
        suggestions.append("Keep up your good habits!")

# 🧠 SMART AI INSIGHT (DYNAMIC)
    if score <= 10:
        explanation = "You are currently managing stress well. Keep maintaining a balanced lifestyle."
    elif score <= 20:
        explanation = "You are experiencing moderate stress. Improving routine, sleep, and focus can help reduce it."
    else:
        explanation = "You are under high stress. Immediate lifestyle changes and support are strongly recommended."

    risk_percentage = round((score / 32) * 100, 2)

    session['result'] = result
    session['score'] = score
    session['risk'] = risk_percentage
    session['features'] = [
    sleep, study, exam, workload,
    concentration, screen, physical,
    sleep_quality, emotional, routine,
    breaks, support
    ]
    session['color'] = color
    session['reasons'] = reasons
    session['suggestions'] = suggestions
    session['explanation'] = explanation

    return render_template(
        "result.html",
        result=result,
        score=score,
        color=color,
        reasons=reasons,
        suggestions=suggestions,
        explanation=explanation,
        risk_percentage=risk_percentage,
        features=session['features'],
        user=session['user']
    )

# -------- HISTORY --------
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    data = []
    dates = []
    scores = []

    filename = f"history_{session['user']}.csv"

    if not os.path.exists(filename):
        with open(filename, "w"):
            pass

    with open(filename, "r") as file:
        reader = csv.reader(file)
        next(reader, None)

        for row in reader:
            if len(row) < 2:
                continue

            try:
                score_value = int(row[1].split('/')[0])
            except:
                continue

            data.append(row)
            dates.append(row[0])
            scores.append(score_value)

    return render_template(
        "history.html",
        data=data,
        dates=dates,
        scores=scores,
        user=session['user']
    )

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
