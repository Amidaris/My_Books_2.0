from app import app
from flask import render_template
from app.models import Book, Author, Borrowings
import requests

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/books", strict_slashes=False)
def books():
    all_books = Book.query.all()
    return render_template("books.html", books=all_books)

@app.route("/authors", strict_slashes=False)
def authors():
    all_authors = Author.query.all()
    return render_template("authors.html", authors=all_authors)

@app.route("/borrowings", strict_slashes=False)
def borrowings():
    all_borrowings = Borrowings.query.all()
    return render_template("borrowings.html", borrowings=all_borrowings)