from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from demo.app.queries.get_cat import CatDTO, GetCat


class GetCatResource:
    _CAT_ADAPTER: ClassVar = TypeAdapter(CatDTO)

    def __init__(self, get_cat: GetCat) -> None:
        self._get_cat = get_cat

    def on_get(
        self, req: falcon.Request, resp: falcon.Response, cat_id: str,
    ) -> None:
        result = self._get_cat.run(cat_id=cat_id)
        if result is None:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Cat not found'}
            resp.content_type = falcon.MEDIA_JSON
            return
        resp.status = falcon.HTTP_200
        resp.text = self._CAT_ADAPTER.dump_json(result)
        resp.content_type = falcon.MEDIA_JSON
