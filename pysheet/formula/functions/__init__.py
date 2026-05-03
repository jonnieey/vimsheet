"""Auto-import all function modules to populate the registry."""

from pysheet.formula.functions import (  # noqa: F401
    date_funcs,
    logic_funcs,
    lookup_funcs,
    math_funcs,
    net_funcs,
    text_funcs,
)
from pysheet.formula.functions.registry import all_names, get  # noqa: F401
