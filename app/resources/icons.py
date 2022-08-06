from app.resources.base_catalog import ManifestCatalog

class Icon():
    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path
        self.image = None
        self.pixmap = None

        self.parent_nid = None
        self.icon_index = (0, 0)

    def set_full_path(self, full_path):
        self.full_path = full_path

    def save(self):
        return self.nid

    @classmethod
    def restore(cls, nid):
        self = cls(nid)
        return self

class IconCatalog(ManifestCatalog[Icon]):
    manifest = 'icons.json'
    title = 'icons'
    filetype = '.png'
    datatype = Icon

class Icon16Catalog(IconCatalog):
    manifest = 'icons16.json'

class Icon32Catalog(IconCatalog):
    manifest = 'icons32.json'

class Icon80Catalog(IconCatalog):
    manifest = 'icons80.json'
