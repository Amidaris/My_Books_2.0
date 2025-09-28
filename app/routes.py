from app import app
from flask import render_template
from app.models import Book
import requests

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/books")
def books():
    all_books = Book.query.all()
    return render_template("books.html", books=all_books)