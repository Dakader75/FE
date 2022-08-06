from app.data.item_components import ItemComponent
from app.data.components import Type

class AlternateDamageFormula(ItemComponent):
    nid = 'alternate_damage_formula'
    desc = 'Item uses a different damage formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'DAMAGE'

    def damage_formula(self, unit, item):
        return self.value

class AlternateResistFormula(ItemComponent):
    nid = 'alternate_resist_formula'
    desc = 'Item uses a different resist formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'DEFENSE'

    def resist_formula(self, unit, item):
        return self.value

class AlternateAccuracyFormula(ItemComponent):
    nid = 'alternate_accuracy_formula'
    desc = 'Item uses a different accuracy formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'HIT'

    def accuracy_formula(self, unit, item):
        return self.value

class AlternateAvoidFormula(ItemComponent):
    nid = 'alternate_avoid_formula'
    desc = 'Item uses a different avoid formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'AVOID'

    def avoid_formula(self, unit, item):
        return self.value

class AlternateCritAccuracyFormula(ItemComponent):
    nid = 'alternate_crit_accuracy_formula'
    desc = 'Item uses a different critical accuracy formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'CRIT_HIT'

    def crit_accuracy_formula(self, unit, item):
        return self.value

class AlternateCritAvoidFormula(ItemComponent):
    nid = 'alternate_crit_avoid_formula'
    desc = 'Item uses a different critical avoid formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'CRIT_AVOID'

    def crit_avoid_formula(self, unit, item):
        return self.value

class AlternateAttackSpeedFormula(ItemComponent):
    nid = 'alternate_attack_speed_formula'
    desc = 'Item uses a different attack speed formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'HIT'

    def attack_speed_formula(self, unit, item):
        return self.value

class AlternateDefenseSpeedFormula(ItemComponent):
    nid = 'alternate_defense_speed_formula'
    desc = 'Item uses a different defense speed formula'
    tag = 'formula'

    expose = Type.Equation
    value = 'HIT'

    def defense_speed_formula(self, unit, item):
        return self.value
