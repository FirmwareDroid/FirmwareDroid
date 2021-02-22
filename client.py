from flask import render_template


def get_client():
    return render_template("index.html")
