from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import joblib
import pandas as pd

app = Flask(__name__)
app.secret_key = "wine_secret_key_change_in_production"

# ── DB config ─────────────────────────────────────────────────────────────────
DB = dict(host="localhost", user="root", password="Mitansh@636782", db="wine_db")

def get_db():
    return pymysql.connect(**DB, cursorclass=pymysql.cursors.DictCursor)

# ── Load model once at startup ────────────────────────────────────────────────
model = joblib.load("rf_wine_model.pkl")

FEATURES = [
    "fixed acidity", "volatile acidity", "citric acid",
    "residual sugar", "chlorides", "free sulfur dioxide",
    "total sulfur dioxide", "density", "pH", "sulphates", "alcohol"
]

def quality_label(score):
    """Convert numeric quality score to a human-readable label."""
    if score < 5:
        return "Poor"
    elif score < 6:
        return "Average"
    elif score < 7:
        return "Good"
    else:
        return "Excellent"

# ── Home ──────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")

# ── Register ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    flash("An account with this email already exists.", "danger")
                    return render_template("register.html")
                hashed = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, email, hashed)
                )
                conn.commit()
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                session.clear()
                session["user_id"]   = user["id"]
                session["user_name"] = name
                flash(f"Welcome, {name}! Your account has been created.", "success")
                return redirect(url_for("dashboard"))
        finally:
            conn.close()

    return render_template("register.html")

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([email, password]):
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if not user or not check_password_hash(user["password_hash"], password):
                    flash("Invalid email or password.", "danger")
                    return render_template("login.html")
                session.clear()
                session["user_id"]   = user["id"]
                session["user_name"] = user["name"]
                flash(f"Welcome back, {user['name']}!", "success")
                return redirect(url_for("dashboard"))
        finally:
            conn.close()

    return render_template("login.html")

# ── Logout ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM predictions WHERE user_id = %s",
                (session["user_id"],)
            )
            total = cur.fetchone()["total"]

            cur.execute(
                """SELECT predicted_quality, quality_label, alcohol, created_at
                   FROM predictions WHERE user_id = %s
                   ORDER BY created_at DESC LIMIT 1""",
                (session["user_id"],)
            )
            latest = cur.fetchone()
    finally:
        conn.close()

    return render_template("dashboard.html", total=total, latest=latest)

# ── Predict ───────────────────────────────────────────────────────────────────
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user_id" not in session:
        flash("Please log in to make predictions.", "warning")
        return redirect(url_for("login"))

    result = None

    if request.method == "POST":
        raw = {f: request.form.get(f, "").strip() for f in FEATURES}

        # ── Validate all fields present ───────────────────────────────────────
        if not all(raw.values()):
            flash("All fields are required.", "danger")
            return render_template("predict.html", result=None)

        # ── Type conversion ───────────────────────────────────────────────────
        try:
            values = {f: float(raw[f]) for f in FEATURES}
        except ValueError:
            flash("All inputs must be valid numbers.", "danger")
            return render_template("predict.html", result=None)

        # ── Range validation ──────────────────────────────────────────────────
        ranges = {
            "fixed acidity":        (4.6,  15.9),
            "volatile acidity":     (0.12,  1.58),
            "citric acid":          (0.0,   1.0),
            "residual sugar":       (1.2,  15.5),
            "chlorides":            (0.012, 0.611),
            "free sulfur dioxide":  (1.0,  72.0),
            "total sulfur dioxide": (6.0, 289.0),
            "density":              (0.990, 1.004),
            "pH":                   (2.74,  4.01),
            "sulphates":            (0.33,  2.0),
            "alcohol":              (8.4,  14.9),
        }
        for feat, (lo, hi) in ranges.items():
            if not (lo <= values[feat] <= hi):
                flash(f"{feat.title()} must be between {lo} and {hi}.", "danger")
                return render_template("predict.html", result=None)

        # ── Predict ───────────────────────────────────────────────────────────
        try:
            df_input = pd.DataFrame([values], columns=FEATURES)
            raw_score    = model.predict(df_input)[0]
            pred_score   = round(float(raw_score), 2)
            pred_label   = quality_label(pred_score)
        except Exception as e:
            flash(f"Prediction error: {str(e)}", "danger")
            return render_template("predict.html", result=None)

        # ── Save to DB ────────────────────────────────────────────────────────
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO predictions
                       (user_id, fixed_acidity, volatile_acidity, citric_acid,
                        residual_sugar, chlorides, free_sulfur_dioxide,
                        total_sulfur_dioxide, density, pH, sulphates, alcohol,
                        predicted_quality, quality_label)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        session["user_id"],
                        values["fixed acidity"],   values["volatile acidity"],
                        values["citric acid"],     values["residual sugar"],
                        values["chlorides"],       values["free sulfur dioxide"],
                        values["total sulfur dioxide"], values["density"],
                        values["pH"],              values["sulphates"],
                        values["alcohol"],         pred_score, pred_label
                    )
                )
                conn.commit()
        finally:
            conn.close()

        result = {"score": pred_score, "label": pred_label, "inputs": values}

    return render_template("predict.html", result=result)

# ── History ───────────────────────────────────────────────────────────────────
@app.route("/history")
def history():
    if "user_id" not in session:
        flash("Please log in to view your history.", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM predictions WHERE user_id = %s
                   ORDER BY created_at DESC""",
                (session["user_id"],)
            )
            records = cur.fetchall()
    finally:
        conn.close()

    return render_template("history.html", records=records)

# ── Contact ───────────────────────────────────────────────────────────────────
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()

        if not all([name, email, message]):
            flash("All fields are required.", "danger")
            return render_template("contact.html")

        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
                    (name, email, message)
                )
                conn.commit()
        finally:
            conn.close()

        flash("Your message has been sent. We'll be in touch!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

# ── About ─────────────────────────────────────────────────────────────────────
@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
