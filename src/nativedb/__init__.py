"""nativedb

By deuxglaces
"""

import nativedb.mongodb
from nativedb.enum import EnumMixin
from nativedb.exceptions import DatabaseError, UniqueConflict, NoDatabase
from nativedb.decorators import collection, database
from nativedb.generics import Key, Unique, NotNull
from nativedb.mongodb import MongoDbModel, mongodb_config, set_default_database
from nativedb.sqlite import SqliteDbModel

__version__ = '0.1.1'
