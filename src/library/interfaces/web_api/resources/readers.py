import falcon

from library.app.commands.use_cases.readers.register_reader import (
    RegisterReader,
)
from library.app.queries.readers.find_readers import FindReaders


class ReadersResource:
    def __init__(
        self,
        find_readers: FindReaders,
        register_reader: RegisterReader,
    ) -> None:
        self._find_readers = find_readers
        self._register_reader = register_reader

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._find_readers.run(req.params)  # pyright: ignore[reportArgumentType]

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        resp.media = self._register_reader.run(req.media, req.context.account)
        resp.status = falcon.HTTP_201
