from app import db
from datetime import datetime

class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(100))

    books = db.relationship("Book", backref="author", lazy="dynamic")

    def __str__(self):
        return f"{self.name} {self.surname}"

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100))
    available = db.Column(db.Boolean, default=True)

    borrowings = db.relationship("Borrowings", backref="book", lazy="dynamic")

    def __str__(self):
        return f"{self.title} ({self.genre})"

class Borrowings(db.Model):
    __tablename__ = "borrowings"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_surname = db.Column(db.String(100), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    def __str__(self):
        return f"{self.borrower_name} {self.borrower_surname} borrowed '{self.book.title}'"
