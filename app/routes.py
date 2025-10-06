from app import app
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from app.models import Book, Author, Borrowings
from app import db
import requests
import csv
from io import StringIO
from flask import Response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/books", strict_slashes=False)
def books():
    genre = request.args.get("genre")
    author_id = request.args.get("author_id")
    available = request.args.get("available")

    # Pobierz unikalne gatunki
    genres = db.session.query(Book.genre).distinct().filter(Book.genre.isnot(None)).all()
    genre_list = sorted(set(g[0] for g in genres if g[0]))

    authors = Author.query.order_by(Author.name).all()

    query = Book.query

    if available == "true":
        query = query.filter(Book.available.is_(True))
    elif available == "false":
        query = query.filter(Book.available.is_(False))

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
        flash("📘 Książka została dodana!", "success")
        return redirect(url_for("books"))
    
    all_authors = Author.query.all()
    return render_template("new_book.html", authors=all_authors)


@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("❌ Książka została usunięta.", "info")
    return redirect(url_for("books"))


@app.route("/authors", strict_slashes=False)
def authors():
    nationality = request.args.get("nationality")
    main_genre = request.args.get("main_genre")

    query = Author.query

    # Listy do filtrów
    nationalities = db.session.query(Author.nationality).distinct().filter(Author.nationality.isnot(None)).all()
    genres = db.session.query(Author.main_genre).distinct().filter(Author.main_genre.isnot(None)).all()

    nationality_list = sorted(set(n[0] for n in nationalities if n[0]))
    genre_list = sorted(set(g[0] for g in genres if g[0]))

    if nationality:
        query = query.filter(Author.nationality.ilike(f"%{nationality}%"))

    if main_genre:
        query = query.filter(Author.main_genre.ilike(f"%{main_genre}%"))
    
    all_authors = query.all()

    return render_template("authors.html", authors=all_authors, nationality_list=nationality_list, genre_list=genre_list)


@app.route("/authors/new", strict_slashes=False, methods=["GET", "POST"])
def new_author():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        nationality = request.form["nationality"]
        main_genre = request.form.get("main_genre")
        info_url = request.form.get("info_url")
        
        new_author = Author(
            name=name, 
            surname=surname, 
            nationality=nationality,
             main_genre=main_genre,
            info_url=info_url
            )
        db.session.add(new_author)
        db.session.commit()
        flash("👨‍🏫 Autor został dodany!", "success")
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
        author.main_genre = request.form.get("main_genre")
        db.session.commit()
        flash("✏️ Autor został zaktualizowany!", "info")
        return redirect(url_for("authors"))

    return render_template("edit_author.html", author=author)


@app.route("/authors/delete/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)

    # Sprawdź, czy autor ma przypisane książki
    if author.books.count() > 0:
        flash("⚠️ Nie można usunąć autora, który ma przypisane książki.", "error")
        return redirect(url_for("authors"))

    db.session.delete(author)
    db.session.commit()
    flash("🗑️ Autor został usunięty.", "info")
    return redirect(url_for("authors"))


@app.route("/borrowings", strict_slashes=False)
def borrowings():
    status = request.args.get("status")

    query = Borrowings.query

    if status == "returned":
        query = query.filter(Borrowings.return_date.isnot(None))
    elif status == "active":
        query = query.filter(Borrowings.return_date.is_(None))

    all_borrowings = query.all()
    return render_template("borrowings.html", borrowings=all_borrowings)


@app.route("/borrowings/new", strict_slashes=False, methods=["GET", "POST"])
def new_borrowings():
    current_date = datetime.utcnow().strftime("%Y-%m-%d")

    if request.method == "POST":
        book_id = request.form["book_id"]
        borrower_name = request.form["borrower_name"]
        borrower_surname = request.form["borrower_surname"]
        email = request.form.get("email")
        phone = request.form.get("phone")
        borrow_date_str = request.form.get("borrow_date")

        # Walidacja: przynajmniej jedno pole kontaktowe
        if not email and not phone:
            flash("⚠️ Nie udało się wypożyczyć książki. Podaj przynajmniej email lub numer telefonu.", "error")
            return redirect(url_for("borrowings"))
        
        # Konwersja dat
        try:
            borrow_date = datetime.strptime(borrow_date_str, "%Y-%m-%d")
        except ValueError:
            flash("⚠️ Niepoprawny format daty wypożyczenia.", "error")
            return redirect(url_for("new_borrowings"))
        # Walidacja: data nie może być z przyszłości
        if borrow_date > datetime.utcnow():
            flash("⚠️ Data wypożyczenia nie może być w przyszłości.", "error")
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
        flash("📦 Wypożyczenie zostało zapisane!", "success")
        return redirect(url_for("borrowings"))

    all_books = Book.query.filter_by(available=True).all()  # tylko dostępne książki
    return render_template("new_borrowings.html", books=all_books, current_date=current_date)


@app.route("/borrowings/return/<int:borrowing_id>", methods=["POST"])
def return_book(borrowing_id):
    borrowing = Borrowings.query.get_or_404(borrowing_id)
    borrowing.return_date = datetime.utcnow()

    book = Book.query.get(borrowing.book_id)
    if book:
        book.available = True

    db.session.commit()
    flash("✅ Książka została zwrócona.", "success")
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
            flash("⚠️ Niepoprawny format daty wypożyczenia.", "error")
            return redirect(url_for("edit_borrowing", borrowing_id=borrowing.id))

        db.session.commit()
        flash("✏️ Wypożyczenie zostało zaktualizowane!")
        return redirect(url_for("borrowings"))

    return render_template("edit_borrowing.html", borrowing=borrowing)


@app.route("/books/export", strict_slashes=False)
def export_books():
    books = Book.query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Tytuł", "Gatunek", "Dostępna", "Autor"])

    for book in books:
        writer.writerow([
            book.id,
            book.title,
            book.genre,
            "Tak" if book.available else "Nie",
            f"{book.author.name} {book.author.surname}"
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=books.csv"}
    )


@app.route("/authors/export", strict_slashes=False)
def export_authors():
    authors = Author.query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Imię", "Nazwisko", "Narodowość", "Gatunek", "Link"])

    for a in authors:
        writer.writerow([
            a.id,
            a.name,
            a.surname,
            a.nationality or "",
            a.main_genre or "",
            a.info_url or ""
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=authors.csv"}
    )


@app.route("/borrowings/export", strict_slashes=False)
def export_borrowings():
    borrowings = Borrowings.query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Tytuł książki", "Imię", "Nazwisko", "Data wypożyczenia",
        "Data zwrotu", "Email", "Telefon", "Status"
    ])

    for b in borrowings:
        writer.writerow([
            b.id,
            b.book.title,
            b.borrower_name,
            b.borrower_surname,
            b.borrow_date.strftime("%Y-%m-%d"),
            b.return_date.strftime("%Y-%m-%d") if b.return_date else "",
            b.email or "",
            b.phone or "",
            "Zwrócona" if b.return_date else "W trakcie"
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=borrowings.csv"}
    )

