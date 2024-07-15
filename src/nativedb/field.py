import dataclasses


@dataclasses.dataclass
class Field:
    name: str
    type: type
    key: bool
    unique: bool
    notnull: bool

    @property
    def unique_or_key(self):
        return self.unique or self.key
