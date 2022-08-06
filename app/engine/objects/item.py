from app.utilities.data import Data

from app.data.database import DB
import app.engine.item_component_access as ICA

class ItemObject():
    next_uid = 100

    def __init__(self, nid, name, desc, icon_nid=None, icon_index=(0, 0), components=None):
        self.uid = ItemObject.next_uid
        ItemObject.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc

        self.icon_nid = icon_nid
        self.icon_index = icon_index

        self.droppable = False

        self.components = components or Data()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value
            # Assign parent to component
            component_value.item = self

        self.data = {}
        
        # For subitems
        self.subitem_uids = []
        self.subitems = []
        self.parent_item = None

    def change_owner(self, nid):
        self.owner_nid = nid
        for item in self.subitems:
            item.owner_nid = nid

    @classmethod
    def from_prefab(cls, prefab):
        # Components NEED To be copies! Since they store individualized information
        components = Data()
        for component in prefab.components:
            new_component = ICA.restore_component((component.nid, component.value))
            components.append(new_component)
        return cls(prefab.nid, prefab.name, prefab.desc, prefab.icon_nid, prefab.icon_index, components)

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __str__(self):
        return "Item: %s %s" % (self.nid, self.uid)

    def __repr__(self):
        return "Item: %s %s" % (self.nid, self.uid)

    def save(self):
        serial_dict = {}
        serial_dict['uid'] = self.uid
        serial_dict['nid'] = self.nid
        serial_dict['name'] = self.name
        serial_dict['desc'] = self.desc
        serial_dict['owner_nid'] = self.owner_nid
        serial_dict['droppable'] = self.droppable
        serial_dict['data'] = self.data
        serial_dict['subitems'] = self.subitem_uids 
        return serial_dict

    @classmethod
    def restore(cls, dat):
        prefab = DB.items.get(dat['nid'])
        if prefab:
            self = cls.from_prefab(prefab)
            self.name = dat.get('name', prefab.name)
            self.desc = dat.get('desc', prefab.desc)
        else:
            desc = 'This is a placeholder for %s generated when the database cannot locate an item' % dat['nid']
            self = cls(dat['nid'], 'Placeholder', desc)
        self.uid = dat['uid']
        self.owner_nid = dat['owner_nid']
        self.droppable = dat['droppable']
        self.data = dat['data']
        self.subitem_uids = dat.get('subitems', [])
        return self
