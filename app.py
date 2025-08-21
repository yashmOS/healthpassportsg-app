import os
import logging
import sqlite3
import json

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers.login import login_required
from helpers.sql import SQLITE

# Configure application
app = Flask(__name__)


# Logging
logging.basicConfig(level = logging.INFO)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# SQLite database
db = SQLITE("healthpassportsg.db", traceback=True)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload a photo"""
    photo_url = None
    if request.method == "POST":
        if "photo" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["photo"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            photo_url = url_for("static", filename="uploads/" + filename)
            flash("File uploaded successfully!")
        else:
            flash("Invalid file type")
    return render_template("upload.html", photo_url=photo_url)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # POST -> perform login 
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username", "error")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", "error")
            return render_template("login.html")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid username and/or password", "error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/view")

    # GET -> login page
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # POST -> register new user
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username", "error")
            return render_template("register.html")

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("must provided password", "error")
            return render_template("register.html")

        # Ensure password match
        if not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
            flash("password does not match", "error")
            return render_template("register.html")

        # Register new user
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       request.form.get("username"),
                       generate_password_hash(request.form.get("password")))

        # Ensure username is unique
        except sqlite3.IntegrityError:
            flash("username already taken", "error")
            return render_template("register.html")

        # Set current session to newly created account
        session["user_id"] = request.form.get("username")
        return redirect("/view")

    # GET -> user registration form
    return render_template("register.html")

@app.route("/view", methods=["GET"])
def view():
    # Dummy data, to fetch from DB and return with a list of dictionaries containing the following fields.
    medical_records = [
        {
            'date': '1 May 2025',
            'hospital_name': 'Raffles Medical',
            'condition': 'Headache',
            'prescription': 'Panadol'
        },
        {
            'date': '29 January 2024',
            'hospital_name': 'Thomson Medical',
            'condition': 'Lower back pain',
            'prescription': 'Panadol'
        },
        {
            'date': '8 May 2023',
            'hospital_name': 'Square Hospital',
            'condition': 'Malaria',
            'prescription': None
        }
    ]
    return render_template('view.html', records=medical_records)

@app.route("/record", methods=["GET"])
def record():
    # Load JSON file
    with open("Result.json", "r") as f:
        data = json.load(f)
    return render_template("record.html", record=data)