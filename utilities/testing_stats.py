import math
from dataclasses import dataclass

@dataclass
class Character():
    name: str = ''
    LVL: int = 1
    HP: int = 1
    POW: int = 0
    SKL: int = 0
    SPD: int = 0
    BRV: int = 0
    DEF: int = 0

@dataclass
class Weapon():
    name: str = ""
    MT: int = 0
    HIT: int = 0

myrm = Character('Myrmidon', 5, 20, 6, 9, 9, 8, 2)
fighter = Character('Fighter', 5, 28, 12, 5, 5, 4, 2)
knight = Character('Knight', 5, 24, 9, 8, 2, 2, 7)
merc = Character('Mercenary', 5, 26, 7, 10, 7, 6, 3)

myrm20 = Character('Myrmidon', 20, 32, 15, 20, 23, 20, 6)
fighter20 = Character('Fighter', 20, 44, 22, 13, 12, 14, 9)
knight20 = Character('Knight', 20, 36, 18, 21, 7, 8, 16)

swordmaster30 = Character('Swordmaster', 30, 47, 24, 30, 32, 29, 11)
warrior30 = Character('Warrior', 30, 68, 32, 21, 20, 24, 16)
general30 = Character('General', 30, 56, 28, 30, 12, 14, 24)

knife = Weapon("Iron Knife", 3, 90)
sword = Weapon("Iron Sword", 4, 80)
lance = Weapon("Iron Lance", 5, 70)
bow = Weapon("Iron Bow", 6, 60)
axe = Weapon("Iron Axe", 7, 50)

def arena(u1, w1, u2, w2):
    mt1 = u1.POW + w1.MT - u2.DEF
    mt2 = u2.POW + w2.MT - u1.DEF
    hit1 = u1.SKL*5 + w1.HIT - u2.SPD*5
    hit2 = u2.SKL*5 + w2.HIT - u1.SPD*5
    as1 = u1.BRV > u2.SPD
    as2 = u2.BRV > u1.SPD

    print("%s: HP: %d Mt: %d Hit: %d Double: %s" % (u1.name, u1.HP, mt1, hit1, as1))
    print("%s: HP: %d Mt: %d Hit: %d Double: %s" % (u2.name, u2.HP, mt2, hit2, as2))
    min_num_rounds_to_ko1 = math.ceil(u2.HP / mt1 / (1.5 if as1 else 1)) if hit1 > 0 else 99
    min_num_rounds_to_ko2 = math.ceil(u1.HP / mt2 / (1.5 if as2 else 1)) if hit2 > 0 else 99
    avg_num_rounds_to_ko1 = math.ceil(u2.HP / (mt1 * min(1, hit1/100)) / (1.5 if as1 else 1)) if hit1 > 0 else 99
    avg_num_rounds_to_ko2 = math.ceil(u1.HP / (mt2 * min(1, hit2/100)) / (1.5 if as2 else 1)) if hit2 > 0 else 99
    print("%s KOs %s in %d rounds (min: %d rounds)" % (u1.name, u2.name, avg_num_rounds_to_ko1, min_num_rounds_to_ko1))
    print("%s KOs %s in %d rounds (min: %d rounds)" % (u2.name, u1.name, avg_num_rounds_to_ko2, min_num_rounds_to_ko2))

arena(myrm, sword, fighter, axe)
print("")
arena(myrm, sword, knight, lance)
print("")
arena(fighter, axe, knight, lance)
print("")
arena(myrm20, sword, fighter20, axe)
print("")
arena(myrm20, sword, knight20, lance)
print("")
arena(fighter20, axe, knight20, lance)
print("")
arena(swordmaster30, sword, warrior30, axe)
print("")
arena(swordmaster30, sword, general30, lance)
print("")
arena(warrior30, axe, general30, lance)
print("")
arena(fighter, axe, merc, axe)
print("")
arena(myrm, sword, myrm, sword)
print("")
arena(fighter, axe, fighter, axe)
print("")
arena(knight, lance, knight, lance)
