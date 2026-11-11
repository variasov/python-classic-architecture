from library.composites.infra.db.engine import engine
from library.infra.db.repos.books import DbBooksRepo

books_repo = DbBooksRepo(engine)
