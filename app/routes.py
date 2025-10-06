from app import app
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from app.models import Book, Author, Borrowings
from app import db
import requests


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/books", strict_slashes=False)
def books():
    genre = request.args.get("genre")
    author_id = request.args.get("author_id")

    # Pobierz unikalne gatunki
    genres = db.session.query(Book.genre).distinct().filter(Book.genre.isnot(None)).all()
    genre_list = sorted(set(g[0] for g in genres if g[0]))

    authors = Author.query.order_by(Author.name).all()

    query = Book.query

    if genre:
        query = query.filter(Book.genre.ilike(f"%{genre}%"))

    if author_id:
        query = query.filter(Book.author_id == int(author_id))

    books = query.all()
    return render_template("books.html", books=books, genre_list=genre_list, authors=authors)


@app.route("/books/new", strict_slashes=False, methods=["GET", "POST"])
def new_book():
    if request.method == "POST":
        title = request.form["title"]
        genre = request.form["genre"]
        author_id = request.form["author_id"]
        new_book = Book(title=title, genre=genre, author_id=author_id)
        db.session.add(new_book)
        db.session.commit()
        flash("📘 Książka została dodana!")
        return redirect(url_for("books"))
    
    all_authors = Author.query.all()
    return render_template("new_book.html", authors=all_authors)


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


@app.route("/authors/new", strict_slashes=False, methods=["GET", "POST"])
def new_author():
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
    return render_template("new_author.html")


@app.route("/authors/edit/<int:author_id>", methods=["GET", "POST"])
def edit_author(author_id):
    author = Author.query.get_or_404(author_id)

    if request.method == "POST":
        author.name = request.form["name"]
        author.surname = request.form["surname"]
        author.nationality = request.form["nationality"]
        author.info_url = request.form.get("info_url")
        db.session.commit()
        flash("✏️ Autor został zaktualizowany!")
        return redirect(url_for("authors"))

    return render_template("edit_author.html", author=author)


@app.route("/authors/delete/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)

    # Sprawdź, czy autor ma przypisane książki
    if author.books.count() > 0:
        flash("⚠️ Nie można usunąć autora, który ma przypisane książki.")
        return redirect(url_for("authors"))

    db.session.delete(author)
    db.session.commit()
    flash("🗑️ Autor został usunięty.")
    return redirect(url_for("authors"))


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


@app.route("/borrowings/edit/<int:borrowing_id>", methods=["GET", "POST"])
def edit_borrowing(borrowing_id):
    borrowing = Borrowings.query.get_or_404(borrowing_id)

    if request.method == "POST":
        borrowing.borrower_name = request.form["borrower_name"]
        borrowing.borrower_surname = request.form["borrower_surname"]
        borrowing.email = request.form.get("email")
        borrowing.phone = request.form.get("phone")

        borrow_date_str = request.form.get("borrow_date")
        try:
            borrowing.borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d")
        except ValueError:
            flash("⚠️ Niepoprawny format daty wypożyczenia.")
            return redirect(url_for("edit_borrowing", borrowing_id=borrowing.id))

        db.session.commit()
        flash("✏️ Wypożyczenie zostało zaktualizowane!")
        return redirect(url_for("borrowings"))

    return render_template("edit_borrowing.html", borrowing=borrowing)

