from typing import List, Optional, Union

from zeno.classes.base import CamelModel, ZenoColumn


class FilterPredicate(CamelModel):
    column: ZenoColumn
    operation: str
    value: Union[str, float, int, bool]
    join: Optional[str]


class FilterPredicateGroup(CamelModel):
    predicates: List[Union[FilterPredicate, "FilterPredicateGroup"]]
    join: str


class FilterIds(CamelModel):
    ids: List[str]


class Slice(CamelModel):
    slice_name: str
    folder: str
    filter_predicates: FilterPredicateGroup
