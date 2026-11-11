from library.composites.app.commands.create_book import create_book
from library.composites.app.queries.books.find_books import find_books
from library.interfaces.api.resources.books import BooksResource

books = BooksResource(create_book=create_book, find_books=find_books)
