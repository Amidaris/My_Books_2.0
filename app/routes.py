from app import app
from datetime import datetime
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


@app.route("/authors", strict_slashes=False, methods=["GET", "POST"])
def authors():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        nationality = request.form["nationality"]
        new_author = Author(name=name, surname=surname, nationality=nationality)
        db.session.add(new_author)
        db.session.commit()
        flash("👨‍🏫 Autor został dodany!")
        return redirect(url_for("authors"))
    
    all_authors = Author.query.all()
    return render_template("authors.html", authors=all_authors)

@app.route("/borrowings", strict_slashes=False)
def borrowings():
    all_borrowings = Borrowings.query.all()
    return render_template("borrowings.html", borrowings=all_borrowings)

@app.route("/borrowings/new", strict_slashes=False, methods=["GET", "POST"])
def new_borrowings():
    if request.method == "POST":
        book_id = request.form["book_id"]
        borrower_name = request.form["borrower_name"]
        borrower_surname = request.form["borrower_surname"]
        email = request.form.get("email")
        phone = request.form.get("phone")
        borrow_date_str = request.form.get("borrow_date")

        # Walidacja: przynajmniej jedno pole kontaktowe
        if not email and not phone:
            flash("⚠️ Podaj przynajmniej email lub numer telefonu.")
            return redirect(url_for("borrowings"))
        
        # Konwersja dat
        try:
            borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d")
        except ValueError:
            flash("⚠️ Niepoprawny format daty wypożyczenia.")
            return redirect(url_for("new_borrowings"))

        # Utwórz wypożyczenie
        new_borrowing = Borrowings(
            book_id=book_id,
            borrower_name=borrower_name,
            borrower_surname=borrower_surname,
            borrow_date=borrow_date,
            email=email if email else None,
            phone=phone if phone else None
        )
        db.session.add(new_borrowing)

        # Zaktualizuj dostępność książki
        book = Book.query.get(book_id)
        if book:
            book.available = False

        db.session.commit()
        flash("📦 Wypożyczenie zostało zapisane!")
        return redirect(url_for("borrowings"))

    all_books = Book.query.filter_by(available=True).all()  # tylko dostępne książki
    return render_template("new_borrowings.html", books=all_books)


@app.route("/borrowings/return/<int:borrowing_id>", methods=["POST"])
def return_book(borrowing_id):
    borrowing = Borrowings.query.get_or_404(borrowing_id)
    borrowing.return_date = datetime.utcnow()

    book = Book.query.get(borrowing.book_id)
    if book:
        book.available = True

    db.session.commit()
    flash("✅ Książka została zwrócona.")
    return redirect(url_for("borrowings"))
