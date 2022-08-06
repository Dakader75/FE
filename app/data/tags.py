from dataclasses import dataclass

from app.utilities.data import Data, Prefab
from app.utilities import str_utils

@dataclass
class Tag(Prefab):
    nid: str = None

    def save(self):
        return self.nid

    @classmethod
    def restore(cls, dat):
        return cls(dat)

class TagCatalog(Data[Tag]):
    datatype = Tag

    def __init__(self, strs):
        super().__init__()
        for s in strs:
            self.append(Tag(s))

    def add_new_default(self, db):
        nid = str_utils.get_next_name("New Tag", self.keys())
        new_tag = Tag(nid)
        self.append(new_tag)
        return new_tag
