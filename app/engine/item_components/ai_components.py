from app.data.item_components import ItemComponent

class NoAI(ItemComponent):
    nid = 'no_ai'
    desc = "Item cannot be used by the AI"
    tag = 'base'

    def ai_priority(self, unit, item, target, move):
        return -1

    def ai_targets(self, unit, item) -> set:
        return set()
