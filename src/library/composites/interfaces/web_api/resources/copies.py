from library.composites.app.commands.books.add_copy import add_copy
from library.interfaces.web_api.resources.copies import CopiesResource

copies = CopiesResource(add_copy=add_copy)
