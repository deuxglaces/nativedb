import collections.abc
import datetime
import sqlite3

import nativedb.dbmodel

_DATA_CAST: dict[type, tuple[collections.abc.Callable, collections.abc.Callable]] = {
    datetime.date: (datetime.date.isoformat, datetime.date.fromisoformat),
    datetime.time: (datetime.time.isoformat, datetime.time.fromisoformat),
    datetime.datetime: (datetime.datetime.isoformat, datetime.datetime.fromisoformat),
}


def register_type(type_, store_fn: collections.abc.Callable, retrive_fn: collections.abc.Callable):
    _DATA_CAST[type_] = (store_fn, retrive_fn)


class SqliteDbModel(nativedb.dbmodel.DbModel):
    _CONNECTION: sqlite3.Connection
    _CURSOR: sqlite3.Cursor
    _TABLE_NAME: str

    def __init__(self, **kwargs):
        super().__init__()
        for k in self.__class__.__annotations__:
            self.__dict__[k] = kwargs[k] if k in kwargs else self.__class__._get_default(k)

    def __init_subclass__(cls, **kwargs):
        try:
            database = kwargs['database']
        except KeyError:
            raise SyntaxError('SqliteDbModel subclasses must specify database keyword arg in definition')
        try:
            cls._CONNECTION = sqlite3.connect(database)
        except Exception as e:
            print(e)
        cls._CURSOR = cls._CONNECTION.cursor()

        # database tables are, by default, the name of the subclass
        cls._TABLE_NAME = kwargs.get('table', cls.__name__)
        cls._init_table()

    @classmethod
    def _init_table(cls):
        pass

    @classmethod
    def find(cls, *args, **kwargs):
        pass

    @classmethod
    def find_one(cls, *args, **kwargs):
        pass

    @classmethod
    def all(cls):
        pass

    @classmethod
    def new(cls, *args, **kwargs):
        pass

    def update(self, **kwargs):
        pass

    def delete(self):
        pass


if __name__ == '__main__':
    register_type(str, str, str)
