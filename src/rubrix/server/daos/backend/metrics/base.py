import dataclasses
from typing import Any, Dict, List, Optional, Union

from rubrix.server.daos.backend.query_helpers import aggregations
from rubrix.server.helpers import unflatten_dict


@dataclasses.dataclass
class ElasticsearchMetric:
    id: str

    @property
    def metric_arg_names(self):
        return self.__args__

    def __post_init__(self):
        self.__args__ = self.get_function_arg_names(self._build_aggregation)

    @staticmethod
    def get_function_arg_names(func):
        return func.__code__.co_varnames

    def aggregation_request(
        self, *args, **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Configures the summary es aggregation definition
        """
        return {self.id: self._build_aggregation(*args, **kwargs)}

    def aggregation_result(self, aggregation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the es aggregation result. Override this method
        for result customization

        Parameters
        ----------
        aggregation_result:
            Retrieved es aggregation result

        """
        return aggregation_result.get(self.id, aggregation_result)

    def _build_aggregation(self, *args, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError()


@dataclasses.dataclass
class NestedPathElasticsearchMetric(ElasticsearchMetric):
    """
    A ``ElasticsearchMetric`` which need nested fields for summary calculation.

    Aggregations for nested fields need some extra configuration and this class
    encapsulate these common logic.

    Attributes:
    -----------
    nested_path:
        The nested
    """

    nested_path: str

    def __post_init__(self):
        self.__args__ = self.get_function_arg_names(self._inner_aggregation)

    def _inner_aggregation(self, *args, **kwargs) -> Dict[str, Any]:
        """The specific aggregation definition"""
        raise NotImplementedError()

    def _build_aggregation(self, *args, **kwargs) -> Dict[str, Any]:
        """Implements the common mechanism to define aggregations with nested fields"""
        return aggregations.nested_aggregation(
            nested_path=self.nested_path,
            inner_aggregation=self._inner_aggregation(*args, **kwargs),
        )

    def compound_nested_field(self, inner_field: str) -> str:
        return f"{self.nested_path}.{inner_field}"


@dataclasses.dataclass
class HistogramAggregation(ElasticsearchMetric):
    """
    Base elasticsearch histogram aggregation metric

    Attributes
    ----------
    field:
        The histogram field
    script:
        If provided, it will be used as scripted field
        for aggregation
    fixed_interval:
        If provided, it will used ALWAYS as the histogram
        aggregation interval
    """

    field: str
    script: Optional[Union[str, Dict[str, Any]]] = None
    fixed_interval: Optional[float] = None

    def _build_aggregation(self, interval: Optional[float] = None) -> Dict[str, Any]:
        if self.fixed_interval:
            interval = self.fixed_interval

        return aggregations.histogram_aggregation(
            field_name=self.field, script=self.script, interval=interval
        )


@dataclasses.dataclass
class TermsAggregation(ElasticsearchMetric):

    field: str = None
    script: Union[str, Dict[str, Any]] = None
    fixed_size: Optional[int] = None
    default_size: Optional[int] = None
    missing: Optional[str] = None

    def _build_aggregation(self, size: int = None) -> Dict[str, Any]:
        if self.fixed_size:
            size = self.fixed_size
        return aggregations.terms_aggregation(
            self.field,
            script=self.script,
            size=size or self.default_size,
            missing=self.missing,
        )


@dataclasses.dataclass
class BidimensionalTermsAggregation(ElasticsearchMetric):
    field_x: str
    field_y: str

    def _build_aggregation(self, size: int = None) -> Dict[str, Any]:
        return aggregations.bidimentional_terms_aggregations(
            field_name_x=self.field_x,
            field_name_y=self.field_y,
            size=size,
        )


@dataclasses.dataclass
class NestedTermsAggregation(NestedPathElasticsearchMetric):
    terms: TermsAggregation

    def __post_init__(self):
        super().__post_init__()
        self.terms.field = f"{self.nested_path}.{self.terms.field}"

    def _inner_aggregation(self, size: int) -> Dict[str, Any]:
        return self.terms.aggregation_request(size)


@dataclasses.dataclass
class NestedBidimensionalTermsAggregation(NestedPathElasticsearchMetric):
    biterms: BidimensionalTermsAggregation

    def __post_init__(self):
        super().__post_init__()
        self.biterms.field_x = f"{self.nested_path}.{self.biterms.field_x}"
        self.biterms.field_y = f"{self.nested_path}.{self.biterms.field_y}"

    def _inner_aggregation(self, size: int = None) -> Dict[str, Any]:
        return self.biterms.aggregation_request(size)


@dataclasses.dataclass
class NestedHistogramAggregation(NestedPathElasticsearchMetric):
    histogram: HistogramAggregation

    def __post_init__(self):
        super().__post_init__()
        self.histogram.field = f"{self.nested_path}.{self.histogram.field}"

    def _inner_aggregation(self, interval: float) -> Dict[str, Any]:
        return self.histogram.aggregation_request(interval)


@dataclasses.dataclass
class WordCloudAggregation(ElasticsearchMetric):
    default_field: str

    def _build_aggregation(
        self, text_field: str = None, size: int = None
    ) -> Dict[str, Any]:
        field = text_field or self.default_field
        terms_id = f"{self.id}_{field}" if text_field else self.id
        return TermsAggregation(id=terms_id, field=field,).aggregation_request(
            size=size
        )[terms_id]


@dataclasses.dataclass
class MetadataAggregations(ElasticsearchMetric):
    def __post_init__(self):
        super().__post_init__()
        self.__args__ = self.get_function_arg_names(self.aggregation_request)

    def aggregation_request(
        self,
        schema: Dict[str, Any],
        size: int = None,
    ) -> List[Dict[str, Any]]:

        metadata_aggs = aggregations.custom_fields(fields_definitions=schema, size=size)
        return [{key: value} for key, value in metadata_aggs.items()]

    def aggregation_result(self, aggregation_result: Dict[str, Any]) -> Dict[str, Any]:
        data = unflatten_dict(aggregation_result, stop_keys=["metadata"])
        return data.get("metadata", {})
