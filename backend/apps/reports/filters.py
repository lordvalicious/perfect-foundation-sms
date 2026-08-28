"""Report filtering utilities for dynamic filter construction."""

from decimal import Decimal
from django.db.models import Q, Field
from django.db.models.fields import DateField, DateTimeField, DecimalField, IntegerField, BooleanField
from django.utils import timezone


class FilterOperator:
    """Supported filter operators."""
    EXACT = "exact"
    IEEXACT = "iexact"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    IN = "in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    RANGE = "range"
    ISNULL = "isnull"
    DATE = "date"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"


FIELD_OPERATOR_MAP = {
    "CharField": [FilterOperator.EXACT, FilterOperator.IEEXACT, FilterOperator.CONTAINS,
                  FilterOperator.ICONTAINS, FilterOperator.STARTSWITH, FilterOperator.ISTARTSWITH,
                  FilterOperator.ENDSWITH, FilterOperator.IENDSWITH, FilterOperator.IN, FilterOperator.ISNULL],
    "TextField": [FilterOperator.EXACT, FilterOperator.IEEXACT, FilterOperator.CONTAINS,
                  FilterOperator.ICONTAINS, FilterOperator.ISNULL],
    "IntegerField": [FilterOperator.EXACT, FilterOperator.GT, FilterOperator.GTE,
                     FilterOperator.LT, FilterOperator.LTE, FilterOperator.IN,
                     FilterOperator.RANGE, FilterOperator.ISNULL],
    "DecimalField": [FilterOperator.EXACT, FilterOperator.GT, FilterOperator.GTE,
                     FilterOperator.LT, FilterOperator.LTE, FilterOperator.RANGE,
                     FilterOperator.ISNULL],
    "FloatField": [FilterOperator.EXACT, FilterOperator.GT, FilterOperator.GTE,
                   FilterOperator.LT, FilterOperator.LTE, FilterOperator.RANGE,
                   FilterOperator.ISNULL],
    "BooleanField": [FilterOperator.EXACT, FilterOperator.ISNULL],
    "DateField": [FilterOperator.EXACT, FilterOperator.GT, FilterOperator.GTE,
                  FilterOperator.LT, FilterOperator.LTE, FilterOperator.RANGE,
                  FilterOperator.DATE, FilterOperator.YEAR, FilterOperator.MONTH,
                  FilterOperator.DAY, FilterOperator.ISNULL],
    "DateTimeField": [FilterOperator.EXACT, FilterOperator.GT, FilterOperator.GTE,
                      FilterOperator.LT, FilterOperator.LTE, FilterOperator.RANGE,
                      FilterOperator.DATE, FilterOperator.YEAR, FilterOperator.MONTH,
                      FilterOperator.DAY, FilterOperator.ISNULL],
    "ForeignKey": [FilterOperator.EXACT, FilterOperator.IN, FilterOperator.ISNULL],
    "ManyToManyField": [FilterOperator.EXACT, FilterOperator.IN, FilterOperator.ISNULL],
}


def get_field_operators(field: Field):
    """Get supported operators for a model field."""
    field_type = field.get_internal_type()
    return FIELD_OPERATOR_MAP.get(field_type, [FilterOperator.EXACT, FilterOperator.ISNULL])


def parse_filter_value(value: str, field: Field):
    """Parse a filter value string to the appropriate Python type."""
    field_type = field.get_internal_type()

    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    if field_type in ("IntegerField", "BigIntegerField", "SmallIntegerField",
                      "PositiveIntegerField", "PositiveBigIntegerField",
                      "PositiveSmallIntegerField"):
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    if field_type in ("DecimalField", "FloatField"):
        try:
            return Decimal(value)
        except (ValueError, TypeError):
            return value

    if field_type in ("DateField", "DateTimeField"):
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y",
                        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    if field_type == "DateField":
                        return timezone.datetime.strptime(value, fmt).date()
                    return timezone.datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return value

    return value


def build_filter_q(field_path: str, operator: str, value, field: Field = None):
    """Build a Q object for a filter."""
    if operator == FilterOperator.ISNULL:
        is_null = value.lower() == "true" if isinstance(value, str) else bool(value)
        return Q(**{f"{field_path}__isnull": is_null})

    if operator == FilterOperator.IN:
        if isinstance(value, str):
            values = [v.strip() for v in value.split(",") if v.strip()]
        elif isinstance(value, list):
            values = value
        else:
            values = [value]
        if field:
            values = [parse_filter_value(v, field) for v in values]
        return Q(**{f"{field_path}__in": values})

    if operator == FilterOperator.RANGE:
        if isinstance(value, str):
            parts = [v.strip() for v in value.split(",")]
            if len(parts) == 2:
                if field:
                    parts = [parse_filter_value(p, field) for p in parts]
                return Q(**{f"{field_path}__range": parts})
        elif isinstance(value, list) and len(value) == 2:
            if field:
                value = [parse_filter_value(v, field) for v in value]
            return Q(**{f"{field_path}__range": value})
        return Q()

    if field:
        value = parse_filter_value(value, field)

    lookup = f"{field_path}__{operator}"
    return Q(**{lookup: value})


def apply_filters(queryset, filters: dict, model, filter_fields: dict = None):
    """
    Apply filters to a queryset.

    Args:
        queryset: Base queryset
        filters: Dict of {field_path: {operator: value}} or {field_path: value}
        model: Django model class
        filter_fields: Optional dict mapping field_path to field config

    Returns:
        Filtered queryset
    """
    if not filters:
        return queryset

    q_objects = Q()

    for field_path, filter_config in filters.items():
        if filter_config is None:
            continue

        if isinstance(filter_config, dict):
            operator = filter_config.get("operator", FilterOperator.EXACT)
            value = filter_config.get("value")
        else:
            operator = FilterOperator.EXACT
            value = filter_config

        if value is None or value == "":
            continue

        field = None
        if filter_fields and field_path in filter_fields:
            field = filter_fields[field_path].get("field")

        if not field:
            try:
                parts = field_path.split("__")
                current_model = model
                for part in parts:
                    field = current_model._meta.get_field(part)
                    if hasattr(field, "related_model") and field.related_model:
                        current_model = field.related_model
            except Exception:
                pass

        q_objects &= build_filter_q(field_path, operator, value, field)

    return queryset.filter(q_objects)


class ReportFilterSpec:
    """Specification for a report filter field."""

    def __init__(self, key: str, label: str, field_path: str, field_type: str = None,
                 operators: list = None, default_operator: str = FilterOperator.EXACT,
                 choices: list = None, placeholder: str = "", help_text: str = "",
                 required: bool = False, depends_on: str = None):
        self.key = key
        self.label = label
        self.field_path = field_path
        self.field_type = field_type
        self.operators = operators or []
        self.default_operator = default_operator
        self.choices = choices or []
        self.placeholder = placeholder
        self.help_text = help_text
        self.required = required
        self.depends_on = depends_on

    def to_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "field_path": self.field_path,
            "field_type": self.field_type,
            "operators": self.operators,
            "default_operator": self.default_operator,
            "choices": self.choices,
            "placeholder": self.placeholder,
            "help_text": self.help_text,
            "required": self.required,
            "depends_on": self.depends_on,
        }


def get_model_filter_specs(model, filter_config: list):
    """Generate filter specs from model fields and config."""
    specs = []

    for config in filter_config:
        if isinstance(config, str):
            field_path = config
            label = field_path.replace("_", " ").title()
            field_type = None
            try:
                parts = field_path.split("__")
                current = model
                for part in parts:
                    field = current._meta.get_field(part)
                    field_type = field.get_internal_type()
                    if hasattr(field, "related_model") and field.related_model:
                        current = field.related_model
            except Exception:
                pass
            operators = FIELD_OPERATOR_MAP.get(field_type, [FilterOperator.EXACT])
            specs.append(ReportFilterSpec(key=field_path, label=label, field_path=field_path,
                                          field_type=field_type, operators=operators).to_dict())
        elif isinstance(config, dict):
            specs.append(ReportFilterSpec(**config).to_dict())

    return specs