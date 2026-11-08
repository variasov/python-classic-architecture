from library.composites.app.commands.create_book import create_book
from library.composites.app.queries.find_books import find_books
from library.interfaces.api.resources.books import BooksResource

books_resource = BooksResource(
    find_books=find_books,
    create_book=create_book,
)
