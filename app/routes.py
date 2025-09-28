from app import app
from flask import render_template, redirect, url_for, flash, request
from app.models import Book, Author, Borrowings
from app import db
import requests

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/books", strict_slashes=False, methods=["GET", "POST"])
def books():
    if request.method == "POST":
        title = request.form["title"]
        genre = request.form["genre"]
        author_id = request.form["author_id"]
        new_book = Book(title=title, genre=genre, author_id=author_id)
        db.session.add(new_book)
        db.session.commit()
        flash("📘 Książka została dodana!")
        return redirect(url_for("books"))
    
    all_books = Book.query.all()
    all_authors = Author.query.all()
    return render_template("books.html", books=all_books, authors=all_authors)

@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("❌ Książka została usunięta.")
    return redirect(url_for("books"))

@app.route("/authors", strict_slashes=False)
def authors():
    all_authors = Author.query.all()
    return render_template("authors.html", authors=all_authors)

@app.route("/borrowings", strict_slashes=False)
def borrowings():
    all_borrowings = Borrowings.query.all()
    return render_template("borrowings.html", borrowings=all_borrowings)