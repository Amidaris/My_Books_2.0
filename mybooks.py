from app import app, db
from app.models import Author, Book, Borrowings
from app import routes

@app.shell_context_processor
def make_shell_context():
   return {
       "db": db,
       "Author": Author,
       "Book": Book,
       "Borrowings": Borrowings
   }