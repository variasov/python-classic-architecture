from library.composites.app.commands.add_copy import add_copy
from library.interfaces.api.resources.books import CopiesResource

copies_resource = CopiesResource(add_copy=add_copy)
