# Multi Items

*Credit to Zelix for the Parallel Falchion icon used for this tutorial.*

## What is a multi item?

Multi items are items which consist of one or more other items. These inner items, referred to here as sub items, are usable by the unit like any other item they possess, although multi items have some unique properties:

* When an item inside a multi item is used, a use is consumed from both the multi item and its sub item. If only the multi item or sub item has infinite uses, a use is still consumed from the other.
* A unit must fulfill restrictions set by both the multi item and a sub item to use that sub item. For example, if the multi item has a sword rank and the sub item has a lance rank, the user would need both sword and lance ranks.
* Multi items are stored in the convoy based on the weapon type of the multi item, rather than any of the sub items.

## How do I make a multi item?

**Step 1: Create the multi item.**

Open the item editor and create a new item. For this example, we will be creating the Parallel Falchion, a sword that can also be used as an item to heal the user. 

![component](./images/Multi-Item/MultiItem1.png)

Once you add the Multi Item component, you should add other components that apply to the item as a whole. In this case, a weapon type, uses, and price are appropriate. Specific stats like hit rate and damage should be left to the sub items. The multi item itself is also intentionally not a weapon despite having a weapon type, as the weapons that are meant to be "equipped" are the sub items in this case. It is also perfectly valid to not include the weapon type at this stage and only have weapon types associated wtih the sub items.

![skeleton](./images/Multi-Item/MultiItem2.png)

When initially added, the multi item component will be blank. Once sub items are created, they can be added here.

**Step 3: Create sub items.**

Sub items can be created as normal. If the uses of the sub item are meant to be tied to the multi item, then no uses need to be specified. Other shared information can be omitted as well.

![sword1](./images/Multi-Item/MultiItem3.png)

As the below example illustrates, the two functions of a multi item do not necessarily need to be related to each other, as the healing portion of the Parallel Falchion would be treated as a usable item rather than a weapon.

![sword2](./images/Multi-Item/MultiItem4.png)

You may notice that there is a chapter uses component associated with the healing sub item. You can associate uses to the sub items to have certain options of a multi item be usable only a limited number of times. Any time a sub item is used, one use will be subtracted from the multi item as well (if the multi item has uses). However, using one sub item will not subtract a use from another sub item. Sub items also do not need to have their own uses; if a multi item has uses and a sub item does not, using that sub item will still subtract a use from the multi item.

**Step 4: Add the sub items to the multi item.**

Return to the multi item and use the + symbol above the multi item component to add the sub items, which will be displayed in a drop down list of all items. Theoretically any item can be added to multi item as a sub item, allowing this component great flexibility.

![swordfinal](./images/Multi-Item/MultiItem5.png)

After this, the Parallel Falchion can be used in-game as a multi item.

## Why do I make a multi item?

The scenario given in this example is fairly simple: a sword that can harm and heal. However, multi items have many uses beyond that. They can represent a weapon with a limited-use finisher attack, by having a multi item consisting of one normal use sub item and one powerful sub item with only one use. They do not need to be limited to weaponry, either; a multi item could be a tome with no properties of its own that contains various spells for healing or status ailments, each having its own mana cost. Thus, if you have any item at all which has more than one function, the multi item component is likely to be of use.