import dataclasses
from typing import Any, Callable, Dict, List, Optional, Union

from prodict import Prodict

from rubrix.client.models import Record


@dataclasses.dataclass
class Search:
    """
    Search results for a single listener execution

    Args:
        total: The total number of records affected by the listener query
        query_params: The query parameters applied to the executed search
    """

    total: int
    query_params: Optional[Dict[str, Any]] = None


class Metrics(Prodict):
    """
    Metrics results for a single listener execution.

    The metrics object exposes the metrics configured for the listener as property values.
    For example, if you define a listener including the metric "F1", the results will be
    accessible as ``metrics.F1``
    """

    pass


@dataclasses.dataclass
class RBListenerContext:
    """
    The Rubrix listener execution context. This class keeps the context components related to a listener

    Args:

        listener: The rubrix listener instance
        search: Search results for current execution
        metrics: Metrics results for current execution
        query_params: Dynamic parameters used in the listener query
    """

    listener: "RBDatasetListener" = dataclasses.field(repr=False, hash=False)
    search: Optional[Search] = None
    metrics: Optional[Metrics] = None
    query_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.__listener__ = self.listener
        del self.listener

    @property
    def dataset(self) -> str:
        """Computed property that returns the configured listener dataset name"""
        return self.__listener__.dataset

    @property
    def query(self) -> Optional[str]:
        """Computed property that returns the configured listener query string"""
        return self.__listener__.formatted_query


ListenerCondition = Callable[[Search, Optional[RBListenerContext]], bool]
ListenerAction = Union[
    Callable[[List[Record], RBListenerContext], bool],
    Callable[[RBListenerContext], bool],
]
