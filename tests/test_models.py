import pytest
from app import app, db
from app.models import Author, Book, Borrowings
from datetime import datetime

@pytest.fixture
def test_app():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()

def test_create_author(test_app):
    author = Author(name="Maria", surname="Konopnicka", nationality="Polska")
    db.session.add(author)
    db.session.commit()

    assert author.id is not None
    assert str(author) == "Maria Konopnicka"

def test_create_book_with_author(test_app):
    author = Author(name="Adam", surname="Mickiewicz", nationality="Polska")
    db.session.add(author)
    db.session.commit()

    book = Book(title="Dziady", genre="Dramat", author_id=author.id)
    db.session.add(book)
    db.session.commit()

    assert book.id is not None
    assert book.available is True
    assert book.author.name == "Adam"
    assert str(book) == "Dziady (Dramat)"

def test_create_borrowing(test_app):
    author = Author(name="Henryk", surname="Sienkiewicz", nationality="Polska")
    db.session.add(author)
    db.session.commit()

    book = Book(title="Potop", genre="Historyczna", author_id=author.id)
    db.session.add(book)
    db.session.commit()

    borrowing = Borrowings(
        book_id=book.id,
        borrower_name="Jan",
        borrower_surname="Kowalski",
        email="jan@example.com",
        phone="123456789"
    )
    db.session.add(borrowing)
    db.session.commit()

    assert borrowing.id is not None
    assert borrowing.return_date is None
    assert borrowing.book.title == "Potop"
    assert str(borrowing) == "Jan Kowalski borrowed 'Potop'"