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

    try:
        # 🔹 Get input values from form
        sleep_hours = float(request.form['sleep_hours'])
        study_hours = float(request.form['study_hours'])
        social_support = float(request.form['social_support'])

        # Add all your other inputs here if present
        input_data = [sleep_hours, study_hours, social_support]

        # 🔹 ML Prediction
        prediction = model.predict([input_data])[0]

        # 🔹 Convert to Stress Level
        if prediction == 0:
            result = "Low"
        elif prediction == 1:
            result = "Moderate"
        else:
            result = "High"

        # 🔹 Risk Percentage (simple logic or use probability if available)
        if result == "Low":
            risk = "20%"
        elif result == "Moderate":
            risk = "50%"
        else:
            risk = "85%"

        # 🔹 Reasons (AI explanation)
        reasons = []

        if sleep_hours < 6:
            reasons.append("Low sleep duration")
        if study_hours > 8:
            reasons.append("High academic workload")
        if social_support < 3:
            reasons.append("Low social interaction")

        if not reasons:
            reasons.append("Balanced lifestyle factors")

        # 🔹 Suggestions (Healthcare Action)
        if result == "Low":
            suggestions = [
                "Maintain your healthy routine",
                "Keep a consistent sleep schedule",
                "Stay physically active"
            ]

        elif result == "Moderate":
            suggestions = [
                "Take regular breaks during study",
                "Practice breathing or meditation",
                "Improve sleep quality",
                "Talk with friends or family"
            ]

        else:
            suggestions = [
                "Take immediate rest",
                "Talk to a trusted person or mentor",
                "Try relaxation techniques like meditation",
                "Reduce workload temporarily",
                "Seek professional help if needed"
            ]

        # 🔴 NEW: Health Message (Healthcare tone)
        if result == "High":
            health_message = "⚠️ Your stress level is critically high. Immediate attention is recommended to prevent serious mental health impact."

        elif result == "Moderate":
            health_message = "⚡ Your stress level is moderate. It is advisable to manage stress before it increases."

        else:
            health_message = "✅ Your mental health is stable. Keep maintaining your current lifestyle."

        # 🔴 NEW: Alert system
        alert = None
        if result == "High":
            alert = "🚨 High Stress Alert: Please take immediate action and consider talking to someone."

        # 🔹 Smart Explanation
        if result == "High":
            explanation = "Based on your inputs, factors like " + ", ".join(reasons[:2]) + " are significantly contributing to high stress."

        elif result == "Moderate":
            explanation = "Your stress is influenced by " + ", ".join(reasons[:2]) + ". Early management is recommended."

        else:
            explanation = "Your responses indicate a balanced lifestyle with minimal stress risk."

        # 🔹 Save to CSV (history)
        import csv
        from datetime import datetime

        with open("history.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                prediction,
                result,
                risk
            ])

        # 🔹 Store in session
        session['result'] = result
        session['risk'] = risk
        session['reasons'] = reasons
        session['suggestions'] = suggestions
        session['explanation'] = explanation
        session['health_message'] = health_message
        session['alert'] = alert

        # 🔹 Send to frontend
        return render_template(
            "result.html",
            result=result,
            risk=risk,
            reasons=reasons,
            suggestions=suggestions,
            explanation=explanation,
            health_message=health_message,
            alert=alert
        )

    except Exception as e:
        return f"Error: {str(e)}"


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
