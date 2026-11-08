from library.composites.app.queries.get_book import get_book
from library.interfaces.api.resources.book import BookResource

book_resource = BookResource(get_book=get_book)
