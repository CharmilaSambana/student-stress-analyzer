from flask import Flask, render_template, request, session, redirect
import csv
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- CREATE USERS CSV ----------------
if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password"])

# ---------------- REGISTER ----------------
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


# ---------------- LOGIN ----------------
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


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template("index.html", user=session['user'])


# ---------------- RESULT PAGE ----------------
@app.route('/result')
def result_page():
    if 'user' not in session:
        return redirect('/login')

    if 'result' not in session:
        return redirect('/')

    return render_template(
        "result.html",
        result=session['result'],
        score=session['score'],
        risk=session['risk'],
        color=session['color'],
        reasons=session['reasons'],
        suggestions=session['suggestions'],
        explanation=session['explanation'],
        user=session['user']
    )


# ---------------- PREDICT ----------------
@app.route('/predict', methods=['POST'])
def predict():

    if 'user' not in session:
        return redirect('/login')

    # ✅ SAFE INPUT HANDLING (prevents 400 error)
    sleep = int(request.form.get('sleep', 0))
    study = int(request.form.get('study', 0))
    exam = int(request.form.get('exam', 0))
    workload = int(request.form.get('workload', 0))
    concentration = int(request.form.get('concentration', 0))
    screen = int(request.form.get('screen', 0))
    physical = int(request.form.get('physical', 0))
    sleep_quality = int(request.form.get('sleep_quality', 0))
    emotional = int(request.form.get('emotional', 0))
    routine = int(request.form.get('routine', 0))
    breaks = int(request.form.get('breaks', 0))
    support = int(request.form.get('support', 0))

    # -------- SCORE --------
    score = sum([
        sleep, study, exam, workload,
        concentration, screen, physical,
        sleep_quality, emotional, routine,
        breaks, support
    ])

    if score > 32:
        score = 32

    # -------- STRESS LEVEL --------
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

    # -------- FACTORS --------
    if sleep >= 2:
        reasons.append("Poor sleep pattern affecting mental health")
        suggestions.append("Maintain 7-8 hours sleep daily")

    if study >= 2:
        reasons.append("High study pressure")
        suggestions.append("Use Pomodoro technique")

    if exam >= 2:
        reasons.append("Exam stress is high")
        suggestions.append("Practice relaxation")

    if screen >= 2:
        reasons.append("High screen time")
        suggestions.append("Limit mobile usage")

    if emotional >= 2:
        reasons.append("High anxiety")
        suggestions.append("Try meditation")

    if len(reasons) == 0:
        reasons.append("No major stress factors")
        suggestions.append("Maintain your routine")

    # -------- EXPLANATION --------
    if result == "High":
        explanation = "Your stress is high due to " + ", ".join(reasons[:2])
    elif result == "Moderate":
        explanation = "Your stress is moderate due to " + ", ".join(reasons[:2])
    else:
        explanation = "You are maintaining a healthy balance"

    # -------- RISK --------
    risk = round((score / 32) * 100, 2)

    # -------- SAVE HISTORY --------
    filename = f"history_{session['user']}.csv"

    if not os.path.exists(filename):
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Score", "Stress Level", "Risk %"])

    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            score,
            result,
            risk
        ])

    # -------- STORE SESSION --------
    session['result'] = result
    session['score'] = score
    session['risk'] = risk
    session['color'] = color
    session['reasons'] = reasons
    session['suggestions'] = suggestions
    session['explanation'] = explanation
    session['features'] = features
    
    
    return render_template(
    "result.html",
    result=session['result'],
    score=session['score'],
    risk=session['risk'],
    color=session['color'],
    reasons=session['reasons'],
    suggestions=session['suggestions'],
    explanation=session['explanation'],
    features=session['features'],   # 🔥 ADD THIS
    user=session['user']
       )


# ---------------- HISTORY ----------------
@app.route('/history')
def history():

    if 'user' not in session:
        return redirect('/login')

    filename = f"history_{session['user']}.csv"

    data = []
    dates = []
    scores = []

    if os.path.exists(filename):
        with open(filename, "r") as file:
            reader = csv.reader(file)
            next(reader, None)

            for row in reader:
                data.append(row)
                dates.append(row[0])
                scores.append(int(row[1]))

    return render_template(
        "history.html",
        data=data,
        dates=dates,
        scores=scores,
        user=session['user']
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
