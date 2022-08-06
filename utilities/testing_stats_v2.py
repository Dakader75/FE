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

myrm = Character('Myrmidon', 5, 19, 11, 17, 13, 12, 2)
fighter = Character('Fighter', 5, 29, 19, 9, 7, 6, 2)
knight = Character('Knight', 5, 24, 15, 16, 4, 3, 8)
merc = Character('Mercenary', 5, 26, 14, 18, 9, 9, 3)
cavalier = Character('Cavalier', 5, 23, 14, 13, 8, 7, 3)
peg_knight = Character('Peg Knight', 5, 17, 10, 15, 14, 11, 1)
wyvern_knight = Character('Wyvern', 5, 27, 18, 12, 6, 8, 6)
thief = Character('Thief', 5, 17, 9, 14, 15, 8, 1)
soldier = Character('Soldier', 5, 20, 14, 15, 5, 1, 3)
brigand = Character('Brigand', 5, 30, 18, 8, 6, 9, 0)
lord = Character('Lord', 5, 25, 13, 15, 10, 10, 3)

myrm20 = Character('Myrmidon', 20, 32, 20, 26, 25, 20, 6)
fighter20 = Character('Fighter', 20, 46, 29, 15, 12, 14, 9)
knight20 = Character('Knight', 20, 36, 24, 27, 7, 8, 16)

swordmaster30 = Character('Swordmaster', 30, 47, 29, 36, 34, 29, 11)
warrior30 = Character('Warrior', 30, 68, 39, 23, 20, 24, 16)
general30 = Character('General', 30, 56, 34, 36, 12, 14, 24)

def arena(u1, u2):
    mt1 = u1.POW - u2.DEF
    mt2 = u2.POW - u1.DEF
    hit1 = u1.SKL*5 + 50 - u2.SPD*5
    hit2 = u2.SKL*5 + 50 - u1.SPD*5
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

"""
arena(myrm, fighter)
print("")
arena(myrm, knight)
print("")
arena(fighter, knight)
print("")
arena(myrm20, fighter20)
print("")
arena(myrm20, knight20)
print("")
arena(fighter20, knight20)
print("")
arena(swordmaster30, warrior30)
print("")
arena(swordmaster30, general30)
print("")
arena(warrior30, general30)
print("")
arena(fighter, merc)
print("")
arena(myrm, myrm)
print("")
arena(fighter, fighter)
print("")
arena(knight, knight)
"""
import itertools
for pair in itertools.combinations([myrm, knight, fighter, merc, cavalier, peg_knight, wyvern_knight, thief, soldier, brigand, lord], 2):
    print("")
    arena(*pair)
