from typing import ClassVar

import falcon
from pydantic import TypeAdapter

from demo.app.commands.create_cat import CreateCat, CreateCatDTO
from demo.app.commands.domain.aggregates.cat import Cat
from demo.app.queries.find_cats import CatDTO as FindCatDTO, FindCats


class CatsCollection:
    _CREATE_CAT_ADAPTER: ClassVar = TypeAdapter(CreateCatDTO)
    _CAT_ADAPTER: ClassVar = TypeAdapter(Cat)
    _CAT_LIST_ADAPTER: ClassVar = TypeAdapter(list[FindCatDTO])

    def __init__(self, create_cat: CreateCat, find_cats: FindCats) -> None:
        self._create_cat = create_cat
        self._find_cats = find_cats

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        raw = req.bounded_stream.read()
        dto = self._CREATE_CAT_ADAPTER.validate_json(raw)
        result = self._create_cat.run(dto)
        resp.status = falcon.HTTP_201
        resp.text = self._CAT_ADAPTER.dump_json(result)
        resp.content_type = falcon.MEDIA_JSON

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        age_from = req.get_param_as_int('age_from', required=True)
        age_to = req.get_param_as_int('age_to', required=True)
        result = self._find_cats.run(age_from=age_from, age_to=age_to)
        resp.status = falcon.HTTP_200
        resp.text = self._CAT_LIST_ADAPTER.dump_json(result)
        resp.content_type = falcon.MEDIA_JSON
