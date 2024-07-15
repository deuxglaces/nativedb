class DatabaseError(Exception):
    pass


class UniqueConflict(DatabaseError, ValueError):
    pass


class NoDatabase(DatabaseError, ValueError):
    pass


class NoCollection(DatabaseError, ValueError):
    pass


class MultipleKeys(DatabaseError):
    pass
