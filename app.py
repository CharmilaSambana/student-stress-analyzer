from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
from flask import Flask, render_template, request,session,redirect
import csv
from werkzeug.security import generate_password_hash,check_password_hash
import os
from datetime import datetime
import io



app = Flask(__name__)
app.secret_key="secret123"

if not os.path.exists("users.csv"):
    with open("users.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password"])

# ---------------- CREATE CSV ONCE ----------------
if not os.path.exists("history.csv"):
    with open("history.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Score", "Stress Level", "Risk %"])


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

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


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
        risk_percentage=session['risk'],
        features=session['features'],
        color=session['color'],
        reasons=session['reasons'],
        suggestions=session['suggestions'],
        explanation=session['explanation'],
        user=session['user']
    )

# ---------------- HOME PAGE ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template("index.html",user=session['user'])


# ---------------- PREDICT ----------------
@app.route('/predict', methods=['POST'])
def predict():
    
    if 'user' not in session:
        return redirect('/login')

    # -------- INPUTS (MATCH YOUR HTML) --------
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

    # -------- SIMPLE SCORE LOGIC (NO ML PROBLEM) --------
    score = sum([
        sleep, study, exam, workload,
        concentration, screen, physical,
        sleep_quality, emotional, routine,
        breaks, support
    ])

    # limit score to 32
    if score > 32:
        score = 32

    score_text = f"{score}/32"

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

# ---------------- KEY FACTORS ----------------

    if sleep >= 2:
       reasons.append("Poor sleep pattern affecting mental health")
       suggestions.append("Maintain 7-8 hours sleep daily")

    if study >= 2:
       reasons.append("High study pressure increases stress")
       suggestions.append("Use Pomodoro technique for study balance")

    if exam >= 2:
       reasons.append("Exam stress is high")
       suggestions.append("Practice relaxation before exams")

    if workload >= 2:
       reasons.append("Heavy academic workload")
       suggestions.append("Break tasks into small tasks")

    if concentration >= 2:
       reasons.append("Low concentration level")
       suggestions.append("Reduce distractions while studying")

    if screen >= 2:
       reasons.append("High screen time usage")
       suggestions.append("Limit mobile usage before sleep")

    if physical >= 2:
       reasons.append("Low physical activity")
       suggestions.append("Do daily exercise or walking")

    if sleep_quality >= 1:
       reasons.append("Poor sleep quality")
       suggestions.append("Avoid screens before bedtime")

    if emotional >= 2:
       reasons.append("High anxiety level")
       suggestions.append("Try meditation or breathing exercises")

    if routine >= 2:
       reasons.append("No proper daily routine")
       suggestions.append("Follow a fixed daily schedule")

    if breaks >= 2:
       reasons.append("Not taking enough breaks")
       suggestions.append("Take short breaks while studying")

    if support >= 2:
       reasons.append("Low emotional support system")
       suggestions.append("Talk to friends or family regularly")

    if len(reasons) == 0:
       reasons.append("No major stress factors detected")
       suggestions.append("Maintain your current healthy routine")
    
    health_message = ""

    if result == "High":
        health_message = "⚠️ Your stress level is critically high. Immediate attention is recommended to prevent serious mental health impact."

    elif result == "Moderate":
        health_message = "⚡ Your stress level is moderate. It is advisable to manage stress before it increases."

    else:
        health_message = "✅ Your mental health is stable. Keep maintaining your current lifestyle."

    alert = None

    if result == "High":
        alert = "🚨 High Stress Alert: Please take immediate action and consider talking to someone."
    
    factor_score = []

    for r in reasons:
        if "sleep" in r:
            factor_score.append(("Sleep Issue", 3))
        elif "study" in r:
            factor_score.append(("Study Pressure", 2))
        elif "screen" in r:
            factor_score.append(("Screen Time", 1))
    factor_score.sort(key=lambda x: x[1], reverse=True)
                      
    features = [
    sleep, study, exam, workload,
    concentration, screen, physical,
    sleep_quality, emotional, routine,
    breaks, support
    ]
    dates = []
    scores = []

    with open("history.csv", "r") as file:
      reader = csv.reader(file)
      next(reader)

      for row in reader:
        dates.append(row[0])
        scores.append(int(row[1].split('/')[0]))
    # -------- RISK % --------
    risk_percentage = round((score / 32) * 100, 2)

    session['result'] = result
    session['score'] = score
    session['risk'] = risk_percentage
    session['features'] = features
    session['color'] = color
    session['reasons'] = reasons
    session['suggestions'] = suggestions
    session['health_message'] = health_message
    session['alert'] = alert

    # -------- SAVE TO CSV --------
    filename = f"history_{session['user']}.csv"

    with open(filename, "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            f"{score}/32",
            result,
            risk_percentage
        ])

    if score<=10:
        color="green"
    elif score<=20:
        color="orange"
    else:
        color="red"

    
    # -------- SHOW RESULT --------
    return render_template(
        "result.html",
        result=result,
        score=score,
        color=color,
        reasons=reasons,
        suggestions=suggestions,
        health_message=health_message,
        alert=alert,
        risk_percentage=risk_percentage,
        factor_score=factor_score,
        features=features,
        dates=dates,
        scores=scores,
        user=session['user'])
    


# ---------------- HISTORY PAGE ----------------
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    import os

    data = []
    dates = []
    scores = []

    filename = f"history_{session['user']}.csv"

    # ✅ Create file if not exists (first time user)
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            pass

    with open(filename, "r") as file:
        reader = csv.reader(file)

        next(reader, None)  # skip header if exists

        for row in reader:

            if len(row) < 2:
                continue

            try:
                # if stored like "32/32"
                score_value = int(row[1].split('/')[0])
            except:
                try:
                    # if stored like "32"
                    score_value = int(row[1])
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
        user=session['user']   # ✅ for welcome message
    )



# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
