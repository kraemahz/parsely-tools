import json
import re

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List


def del_none(d: dict) -> dict:
    """Delete keys with the value ``None`` in a dictionary."""
    d = deepcopy(d)
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            d[key] = del_none(value)
    return d


def to_dict(item: Any) -> dict:
    d = asdict(item)
    return del_none(d)


@dataclass
class Prop:
    type: str
    description: str
    items: dict | None

    def __init__(self, type, description, items=None):
        self.type = type
        assert len(description) <= 1024, \
            f"Max description length {len(description)}: {description}"
        self.description = description
        self.items = items


@dataclass
class Params:
    required: List[str]
    properties: Dict[str, Prop]
    type: str = "object"


@dataclass
class Tool:
    name: str
    description: str
    parameters: Params

    def __init__(self, name, description, parameters):
        self.name = name
        assert len(description) <= 1024, \
            f"Max description length {len(description)}: {description}"
        self.description = description
        self.parameters = parameters


@dataclass
class Function:
    function: Tool
    type: str = "function"


class ToolCallMixin:
    def __call__(self, function_name, function_args):
        try:
            return getattr(self, function_name)(**function_args)
        except AttributeError as e:
            return {"error": "AttributeError: {}".format(e)}
        except TypeError as e:
            return {"error": "TypeError: {}".format(e)}
        except TimeoutError as e:
            return {"error": "TimeoutError: {}".format(e)}
        except ValueError as e:
            return {"error": "ValueError: {}".format(e)}
        except Exception as e:
            return {"error": "Exception {}".format(e)}


class LifeCycleHandler:
    def __init__(self):
        self.completed = False

    def abort(self, content):
        self.complete(f"Abort: {content}")
        raise RuntimeError(content)

    def complete(self, message):
        self.completed = True

    def incomplete(self):
        return not self.completed


class ToolBox(ToolCallMixin, LifeCycleHandler):
    def __init__(self, **props):
        super().__init__()
        self.props = props


def try_json_load(result):
    pattern = r"```json\n(.*)\n```"
    match = re.search(pattern, result, re.DOTALL)
    if match:
        result = match.group(1)
    return json.loads(result)
