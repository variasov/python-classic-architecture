from typing import Any

import falcon

# Импорт модуля реакции подписывает её на общий hub до первого notify.
from library.composites.app.commands.loans.notify_on_loan_issued import (
    notify_on_loan_issued as notify_on_loan_issued,
)
from library.composites.interfaces.web_api.resources.book import book
from library.composites.interfaces.web_api.resources.books import books
from library.composites.interfaces.web_api.resources.catalog_books import catalog_books
from library.composites.interfaces.web_api.resources.copies import copies
from library.composites.interfaces.web_api.resources.loan_extensions import (
    loan_extensions,
)
from library.composites.interfaces.web_api.resources.loans import loans
from library.composites.interfaces.web_api.resources.memberships import memberships
from library.composites.interfaces.web_api.resources.reader_blocks import reader_blocks
from library.composites.interfaces.web_api.resources.readers import readers
from library.composites.interfaces.web_api.resources.returns import returns
from library.composites.interfaces.web_api.settings import api_settings
from library.interfaces.web_api.app import create_app

app: falcon.App[Any, Any] = create_app(
    api_settings,
    books=books,
    copies=copies,
    readers=readers,
    book=book,
    catalog_books=catalog_books,
    memberships=memberships,
    reader_blocks=reader_blocks,
    loans=loans,
    loan_extensions=loan_extensions,
    returns=returns,
)
