import typing

T = typing.TypeVar('T')


class Key(typing.Generic[T]):
    pass


class Unique(typing.Generic[T]):
    pass


class NotNull(typing.Generic[T]):
    pass
