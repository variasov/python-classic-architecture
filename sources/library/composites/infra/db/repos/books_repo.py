from library.composites.infra.db.engine import engine
from library.infra.db.repos.books_repo import DbBooksRepo

books_repo = DbBooksRepo(engine=engine)
