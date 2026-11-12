import falcon

from library.app.commands.books.add_copy import AddCopy


class CopiesResource:
    def __init__(self, add_copy: AddCopy) -> None:
        self._add_copy = add_copy

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._add_copy.run(req.media, req.context.account)
        resp.status = falcon.HTTP_201
