from flask import render_template, g, redirect, url_for
from flask_login import current_user
from app import app


@app.before_request
def before_request():
    g.user = current_user


@app.route('/')
def index():
    return redirect(url_for("list_articles"))


@app.errorhandler(403)
def forbidden_403(exception):
    user = g.user
    return render_template(
        "http_codes/403.html",
        title="403 - Forbidden",
        user=user)
