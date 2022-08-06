from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations

class Canto(SkillComponent):
    nid = 'canto'
    desc = "Unit can move again after certain actions"
    tag = 'movement'

    def has_canto(self, unit, unit2) -> bool:
        """
        Can move again if hasn't attacked or attacked self
        """
        return not unit.has_attacked or unit is unit2

class CantoPlus(SkillComponent):
    nid = 'canto_plus'
    desc = "Unit can move again even after attacking"
    tag = 'movement'

    def has_canto(self, unit, unit2) -> bool:
        return True

class CantoSharp(SkillComponent):
    nid = 'canto_sharp'
    desc = "Unit can move and attack in either order"
    tag = 'movement'

    def has_canto(self, unit, unit2) -> bool:
        return not unit.has_attacked or unit.movement_left >= equations.parser.movement(unit)

class MovementType(SkillComponent):
    nid = 'movement_type'
    desc = "Unit will have a non-default movement type"
    tag = 'movement'

    expose = Type.MovementType

    def movement_type(self, unit):
        return self.value

class Pass(SkillComponent):
    nid = 'pass'
    desc = "Unit can move through enemies"
    tag = 'movement'

    def pass_through(self, unit):
        return True

class IgnoreTerrain(SkillComponent):
    nid = 'ignore_terrain'
    desc = "Unit will not be affected by terrain"
    tag = 'movement'

    def ignore_terrain(self, unit):
        return True

    def ignore_region_status(self, unit):
        return True

class IgnoreRescuePenalty(SkillComponent):
    nid = 'ignore_rescue_penalty'
    desc = "Unit will ignore the rescue penalty"
    tag = 'movement'

    def ignore_rescue_penalty(self, unit):
        return True

class Grounded(SkillComponent):
    nid = 'grounded'
    desc = "Unit cannot be forcibly moved"
    tag = 'movement'

    def ignore_forced_movement(self, unit):
        return True
