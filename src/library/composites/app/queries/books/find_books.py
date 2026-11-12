import pydantic

from library.app.queries.books.find_books import FindBooks
from library.composites.infra.db.gateways.find_books import find_books_gateway

find_books = FindBooks(gateway=find_books_gateway)
find_books.run = pydantic.validate_call(find_books.run)  # pyright: ignore[reportAttributeAccessIssue]
