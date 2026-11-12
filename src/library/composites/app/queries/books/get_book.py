import pydantic

from library.app.queries.books.get_book import GetBook
from library.composites.infra.db.gateways.get_book import get_book_gateway

get_book = GetBook(gateway=get_book_gateway)
get_book.run = pydantic.validate_call(get_book.run)  # pyright: ignore[reportAttributeAccessIssue]
