import collections.abc
import inspect
import weakref
from typing import Self, Optional

import bson
import pymongo.database
import pymongo.errors

import nativeserializer

from .dbmodel import DbModel
from .exceptions import MultipleKeys, NoCollection, NoDatabase, UniqueConflict
from .generics import Key


def register_type(type_, store_fn: collections.abc.Callable, retrive_fn: collections.abc.Callable):
    MongoDbModel.register_type(type_, store_fn, retrive_fn)


# noinspection PyProtectedMember
def mongodb_config(
        *,
        client: pymongo.mongo_client.MongoClient = None,
        database: [str, pymongo.database.Database] = None,
        host=None,
        port=None,
        document_class=dict,
        tz_aware=None,
        connect=None,
        type_registry=None,
):
    """Single time config for MongoDb to set up a particular client, database etc. for all database models,
    avoiding repeat decorators etc.  This must be called before any class definitions subclassing MongoDbModel.

    The following code is equivalent:
    Snippet 1:
        @database('MyDB')
        class FirstModel(MongoDbModel):
            pass

        @database('MyDB')
        class FirstModel(MongoDbMOdel):
            pass

    Snippet 2:
        mongodb_config(database='MyDB')

        class FirstModel(MongoDbModel):
            pass

        class FirstModel(MongoDbMOdel):
            pass
    """
    # set the default client, and default database on the MongoDbModel class, NOT on subclasses directly
    if client:
        MongoDbModel._DEFAULT_CLIENT = client
    elif (
            any(kwarg is not None for kwarg in [host, port, tz_aware, connect, type_registry]) or
            document_class is not dict
    ):
        client = pymongo.MongoClient(host, port, document_class, tz_aware, connect, type_registry)
        MongoDbModel._DEFAULT_CLIENT = client
    else:
        client = MongoDbModel._DEFAULT_CLIENT

    if isinstance(database, str):
        MongoDbModel._DEFAULT_DATABASE = client.get_database(database)
    elif isinstance(database, pymongo.database.Database):
        MongoDbModel._DEFAULT_DATABASE = database


# noinspection PyProtectedMember
def set_default_database(database: [str, pymongo.database.Database] = None):
    client = MongoDbModel._DEFAULT_CLIENT
    if isinstance(database, str):
        MongoDbModel._DEFAULT_DATABASE = client.get_database(database)
    elif isinstance(database, pymongo.database.Database):
        MongoDbModel._DEFAULT_DATABASE = database


class MongoDbModel(DbModel):
    # MongoDbModel class attribute
    _DEFAULT_CLIENT: pymongo.mongo_client.MongoClient = pymongo.MongoClient()
    _DEFAULT_DATABASE: pymongo.database.Database = None
    _SERIALIZER: nativeserializer.Serializer = nativeserializer.Serializer()

    # Subclass attributes (set in __init_subclass__)
    _CLIENT: pymongo.mongo_client.MongoClient
    _DATABASE: pymongo.database.Database
    _COLLECTION: pymongo.collection.Collection
    _COLLECTION_INITIALIZED: bool
    _WEAKREFS: dict[bson.ObjectId, weakref.ref]
    _KEY_FIELD: str = '_id'

    # Instance attributes (set in __init__)
    _id: bson.ObjectId

    def __init__(self, *args, **kwargs):
        # initialize with default values where specified, None otherwise
        for key in self.__annotations__:
            self.__dict__[key] = self.__class__.__dict__.get(key)

        values = {k: v for k, v in zip(self.__annotations__, args)}
        values.update(kwargs)
        self.__dict__.update(values)
        self.__class__._WEAKREFS[self._id] = weakref.ref(self)

    def __init_subclass__(cls, **kwargs):
        cls._SUBCLASS_INITIALIZED = False
        cls._WEAKREFS = {}
        cls._CLIENT = cls._DEFAULT_CLIENT
        cls._DATABASE = cls._DEFAULT_DATABASE
        # noinspection PyTypeChecker
        cls._COLLECTION = None
        cls._COLLECTION_INITIALIZED = False
        database, collection = kwargs.get('database'), kwargs.get('collection')
        if database:
            cls.set_database(database)
        if collection:
            cls.set_collection(collection)
        for anno, val in cls.__annotations__.items():
            if hasattr(val, '__origin__') and val.__origin__ is Key:
                if cls._KEY_FIELD != '_id':
                    raise MultipleKeys(f'Too many Key fields in model "{cls.__name__}". Use Unique'
                                       f' for multiple unique fields.')
                cls._KEY_FIELD = anno
        cls.__init__.__signature__ = inspect.Signature(
            parameters=[inspect.Parameter('self', inspect.Parameter.POSITIONAL_ONLY, annotation=cls)] + [
                inspect.Parameter(k, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=v)
                for k, v in cls.__annotations__.items()
            ],
            return_annotation=None,
        )
        register_type(cls, cls._db_store_, cls._db_retrieve_)

    @classmethod
    def register_type(cls, type_, store_fn, retrive_fn):
        cls._SERIALIZER.register_type(type_, store_fn, retrive_fn)

    @classmethod
    def set_database(cls, database: [str, pymongo.database.Database]):
        if isinstance(database, pymongo.database.Database):
            cls._DATABASE = database
            return
        if isinstance(database, str):
            client = cls._get_client()
            if client:
                cls._DATABASE = cls._get_client().get_database(database)
                return
        raise NoDatabase(f'Unable to set database for {cls}')

    @classmethod
    def get_database(cls):
        return cls._DATABASE

    @classmethod
    def _set_client(cls, client: [str, pymongo.mongo_client.MongoClient]):
        cls._CLIENT = client

    @classmethod
    def _get_client(cls):
        return cls._CLIENT

    @classmethod
    def set_collection(cls, collection: [str, pymongo.collection.Collection]):
        if isinstance(collection, pymongo.collection.Collection):
            cls._COLLECTION = collection
            return
        elif isinstance(collection, str):
            if (database := cls.get_database()) is not None:
                cls._COLLECTION = database.get_collection(collection)
                return
        raise NoDatabase(f'Unable to set collection to {collection} for {cls} as there is no specified database')

    @classmethod
    def _init_collection(cls, collection: pymongo.collection.Collection):
        for k in cls.__annotations__:
            if cls._get_field(k).unique_or_key:
                collection.create_index(k, unique=True)
        cls._COLLECTION_INITIALIZED = True

    @classmethod
    def get_collection(cls):
        collection = None
        if cls._COLLECTION is not None:
            collection = cls._COLLECTION
        database = cls.get_database()
        if database is not None:
            collection = database.get_collection(cls.__name__)
        if collection is None:
            raise NoCollection(f'{cls} has no specified collection, or database for '
                               f'generic collection')
        if not cls._COLLECTION_INITIALIZED:
            cls._init_collection(collection)
        return collection

    @classmethod
    def _get(cls, doc: dict):
        bson_id = doc['_id']
        if bson_id in cls._WEAKREFS:
            if obj := cls._WEAKREFS[bson_id]():
                # ensure the object isn't duplicated in memory, and uses any already existing one
                # this also ensures all references to the same db doc point to the same object
                return obj
        doc.update(cls._get_retrieve_vals(doc))
        return cls(**doc, ___internal___=True)

    @classmethod
    def _get_all_args(cls, *args, **kwargs):
        all_args = {k: v for k, v in zip(cls.__annotations__, args)}
        all_args.update(kwargs)
        return all_args

    @classmethod
    def query(cls, query) -> list[Self]:
        return [cls._get(doc) for doc in cls.get_collection().find(query)]

    @classmethod
    def find(cls, *args, **kwargs) -> list[Self]:
        all_args = cls._get_all_args(*args, **kwargs)
        return [cls._get(doc) for doc in cls.get_collection().find(cls._get_store_vals(all_args))]

    @classmethod
    def find_one(cls, *args, **kwargs) -> Optional[Self]:
        all_args = cls._get_all_args(*args, **kwargs)
        if doc := cls.get_collection().find_one(cls._get_store_vals(all_args)):
            return cls._get(doc)

    @classmethod
    def delete_all(cls, *args, **kwargs):
        all_args = cls._get_all_args(*args, **kwargs)
        cls.get_collection().delete_many(cls._get_store_vals(all_args))

    @classmethod
    def new(cls, *args, **kwargs):
        all_args = cls._get_all_args(*args, **kwargs)
        doc = {k: all_args[k] if k in all_args else cls._get_default(k) for k in cls.__annotations__}
        try:
            insert_result = cls.get_collection().insert_one(cls._get_store_vals(doc))
        except pymongo.errors.DuplicateKeyError as e:
            raise UniqueConflict from e
        doc['_id'] = insert_result.inserted_id
        return cls(**doc, ___internal___=True)

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        return cls.find_one(*args, **kwargs) or cls(*args, **kwargs)

    @classmethod
    def _get_store_vals(cls, d: dict) -> dict:
        """Convert values in param d to database-storable values using cls._SERIALIZER

        :param d: dict containing raw values
        :return: dict containing database-storable values
        """
        return {k: cls._SERIALIZER.serialize(v) for k, v in d.items()}

    @classmethod
    def _get_retrieve_vals(cls, d: dict) -> dict:
        """Convert values in param d from database-storable values back to their original values using cls._SERIALIZER
        :param d: dict containing database-storable values
        :return: dict containing raw values
        """
        rv = {}
        for k, v in d.items():
            if k in cls.__annotations__:
                rv[k] = cls._SERIALIZER.deserialize(cls.__annotations__[k], v)
            else:
                rv[k] = v
        return rv

    def update(self, **kwargs):
        """Update in-memory model instance with values in kwargs, and also write ONLY those changes to the database
        Behaviour differs from save method in that save also writes other changes:

        my_inst.field1 = 'not changed'
        my_inst.update(field2='changed too')  # ONLY writes field2 change to the database

        my_inst.field1 = 'not changed'
        my_inst.save(field2='changed too')  # Writes BOTH field1 and field2 change to the database
        """
        updates = {k: v for k, v in kwargs.items() if k in self.__annotations__}
        if updates:
            self.__dict__.update(updates)
            try:
                self.get_collection().update_one({'_id': self._id},
                                                 {'$set': self.__class__._get_store_vals(updates)})
            except pymongo.errors.DuplicateKeyError as e:
                raise UniqueConflict from e

    def delete(self):
        self.get_collection().delete_one({'_id': self._id})
        self._WEAKREFS.pop(self._id)

    def _db_store_(self):
        return getattr(self, self.__class__._KEY_FIELD)

    @classmethod
    def _db_retrieve_(cls, stored_val):
        return cls.find_one(**{cls._KEY_FIELD: stored_val})
