import collections.abc

import nativedb.field
import nativedb.generics


class DbModel:
    def __new__(cls, *args, **kwargs):
        if '___internal___' in kwargs:
            kwargs.pop('___internal___')
            return super().__new__(cls)
        return cls.new(*args, **kwargs)

    @classmethod
    def _get_field(cls, fieldname: str, key=False, unique=False, notnull=False, anno=None) -> nativedb.field.Field:
        anno = anno or cls.__annotations__[fieldname]
        if hasattr(anno, '__origin__'):
            if anno.__origin__ is nativedb.generics.Key:
                return cls._get_field(fieldname, key=True, unique=unique, notnull=notnull, anno=anno.__args__[0])
            if anno.__origin__ is nativedb.generics.Unique:
                return cls._get_field(fieldname, key=key, unique=True, notnull=notnull, anno=anno.__args__[0])
            if anno.__origin__ is nativedb.generics.NotNull:
                return cls._get_field(fieldname, key=key, unique=key, notnull=True, anno=anno.__args__[0])
            if anno.__origin__ in {set, list, dict, tuple}:
                return nativedb.field.Field(fieldname, anno.__origin__, key, unique, notnull)

        return nativedb.field.Field(fieldname, anno, key, unique, notnull)

    @classmethod
    def _get_default(cls, fieldname: str):
        default = cls.__dict__.get(fieldname)
        if isinstance(default, collections.abc.Callable):
            return default()
        if isinstance(default, collections.abc.Iterator):
            return next(default)
        t = cls._get_field(fieldname).type
        if t in {list, set, dict, tuple}:
            return t()
        return default

    @classmethod
    def find(cls, *args, **kwargs):
        pass

    @classmethod
    def find_one(cls, *args, **kwargs):
        pass

    @classmethod
    def all(cls):
        return cls.find()

    @classmethod
    def new(cls, *args, **kwargs):
        pass

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        pass

    def update(self, **kwargs):
        """Update the database ONLY with values from kwargs.  Any other updated values will not be saved.
        If you need
        :param kwargs:
        :return:
        """
        pass

    def delete(self):
        pass

    def save(self, **kwargs):
        """Save the current state of the instance to the database, after updating any fields with values
        from kwargs
        :param kwargs:
        :return:
        """
        update_vals = {
            k: v for k, v in self.__dict__.items() if k in self.__annotations__
        }
        update_vals.update(kwargs)
        return self.update(**update_vals)

    def _db_store_(self):
        pass

    @classmethod
    def _db_retrieve_(cls, stored_val):
        pass
