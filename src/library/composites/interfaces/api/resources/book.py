from library.composites.app.queries.books.get_book import get_book
from library.interfaces.api.resources.book import BookResource

book = BookResource(get_book=get_book)
