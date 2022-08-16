from __future__ import annotations

from app.data.components import Type
from app.data.database import DB
from app.data.skill_components import SkillComponent, SkillTags
from app.engine import (action, banner, combat_calcs, engine, equations,
                        image_mods, item_funcs, item_system, skill_system,
                        static_random, target_system)
from app.engine.game_state import game
from app.engine.objects.unit import UnitObject
from app.utilities import utils


class DoNothing(SkillComponent):
    nid = 'do_nothing'
    desc = 'does nothing'
    tag = SkillTags.CUSTOM

    expose = Type.Int
    value = 1
