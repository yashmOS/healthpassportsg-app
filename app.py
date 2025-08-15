import os
import logging
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

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


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")


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
        return redirect("/")

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

        return redirect("/")

    # GET -> user registration form
    return render_template("register.html")