from library.composites.infra.db.engine import engine
from library.infra.db.repos.books import BooksRepository

books_repo = BooksRepository(db=engine)
