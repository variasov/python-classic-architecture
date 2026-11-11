from library.composites.app.commands.add_copy import add_copy
from library.interfaces.api.resources.copies import CopiesResource

copies = CopiesResource(add_copy=add_copy)
