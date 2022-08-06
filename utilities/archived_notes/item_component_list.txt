# Item Components

Weapon (WeaponType) : Cannot be Spell
Spell (WeaponType AND Beneficial/Detrimental/Neutral AND Target (Ally/Enemy/Unit/Tile/Tile Without Unit)) : Cannot be Weapon
Usable (bool)
Might (int) : Spell or Weapon
Hit (int): Spell or Weapon
Rank (Weapon Rank): Spell or Weapon
Locked to Unit (list of Unit): Spell or Weapon or Usable
Locked to Class (list of Class): Spell or Weapon or Usable
Status on Hit (Status): Spell or Weapon
Status while Equipped (Status): Weapon
Status while Held (Status)
Status on Use (Status): Usable
Locked (bool)
Uses (int)
Chapter Uses (int)
Weight (int): Spell or Weapon
Experience (int): Spell or Weapon
Maximum Experience (int): Spell or Weapon
Unrepairable (bool)
Movement on Hit (Movement): Spell or Weapon
Movement on Use (Movement): Usable
Brave (bool): Weapon
Brave on Attack (bool): Weapon
Brave on Defense (bool): Weapon
Cannot Be Countered (bool): Weapon
Cannot Double (bool): Weapon
Heal on Hit (int): Weapon or Spell
Heal on Use (int): Usable
Repair (bool): Spell or Usable  -- will work on both hit and use
EventTile Interact (EventTileType): Spell
Extra Targets (list of (Min Range / Max Range AND Target)): Spell
Target Restrict (Eval): Spell
Crit (int): Weapon or Spell AND Might
Effective Versus (list of (Tag and int)): Weapon or Spell AND Might
Reverse (bool): Weapon or Spell
Magical (bool): Weapon or Spell and not Magical only at Range
Magical only at Range (bool): Weapon or Spell and not Magic
Ignores Weapon Triangle (bool): Weapon or Spell
Weapon Experience (int): Weapon or Spell
Does Half Damage on Miss (bool): Weapon or Spell
Lifelink (bool): Weapon or Spell and not Lifelink
Half Lifelink (bool): Weapon or Spell and not Half Lifelink
Ignore Defense (bool): Weapon or Spell and not Ignore Half Defense
Ignore Half Defense (bool): Weapon or Spell and not Ignore Defense
Area of Effect (AOEType): Weapon or Spell
Alternate Damage, Defense, Accuracy, Avoid, Crit Accuracy, Crit Avoid (Equation): Weapon or Spell AND associated Might, Hit, or Crit component
Booster (bool): Usable
Promotion (list of Classes): Spell or Usable
Permanent Stat Increase (list of Stats): Spell or Usable
Permanent Growth Increase (list of Growths): Spell or Usable
Hit Point Cost (int): Weapon or Spell or Usable
Mana Cost (int): Weapon or Spell or Usable
Cooldown (int): Weapon or Spell or Usable
Triggers Event (Event): Weapon or Spell or Usable

No AI (bool)
AI Item Priority (float)


