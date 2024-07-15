import nativedb.mongodb


def database(database_or_name):
    def decorator(cls):
        if hasattr(cls, '__mro__') and nativedb.mongodb.MongoDbModel in cls.__mro__:
            cls.set_database(database_or_name)
        return cls

    return decorator


def collection(collection_or_name):
    def decorator(cls):
        if hasattr(cls, '__mro__') and nativedb.mongodb.MongoDbModel in cls.__mro__:
            cls.set_collection(collection_or_name)
        return cls

    return decorator
