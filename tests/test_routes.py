import pytest
from app import app, db
from app.models import Author, Book, Borrowings
from datetime import datetime

@pytest.fixture
def client(test_app):
    with app.test_client() as client:
        yield client
        
@pytest.fixture   
def test_app():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200

def test_books_page(client):
    response = client.get("/books")
    assert response.status_code == 200

def test_authors_page(client):
    response = client.get("/authors")
    assert response.status_code == 200

def test_borrowings_page(client):
    response = client.get("/borrowings")
    assert response.status_code == 200

def test_add_author(client):
    response = client.post("/authors/new", data={
        "name": "Jan",
        "surname": "Kowalski",
        "nationality": "Polska"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_add_book(client):
    # najpierw dodaj autora
    db.session.add(Author(name="Adam", surname="Mickiewicz", nationality="Polska"))
    db.session.commit()
    author = Author.query.first()

    response = client.post("/books/new", data={
        "title": "Pan Tadeusz",
        "genre": "Epos",
        "author_id": author.id
    }, follow_redirects=True)
    assert response.status_code == 200