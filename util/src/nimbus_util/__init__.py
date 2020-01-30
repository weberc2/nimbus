from typing import List

from nimbus_core import Tag, ParameterString


def mktags(**tags: ParameterString) -> List[Tag]:
    return [Tag(Key=key, Value=value) for key, value in tags.items()]
