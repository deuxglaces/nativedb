import functools

import nativedb.mongodb


def _store_enum(value):
    if hasattr(value, 'value'):
        return value.value
    raise AttributeError('EnumMixin subclasses must also subclass enum.Enum')


def _retrieve_enum(cls, value):
    if hasattr(cls, '_value2member_map_'):
        return cls._value2member_map_.get(value)
    raise AttributeError('DbStoreableEnum subclasses must also subclass enum.Enum')


class EnumMixin:
    def __init_subclass__(cls, **kwargs):
        nativedb.mongodb.register_type(cls, _store_enum, functools.partial(_retrieve_enum, cls))
