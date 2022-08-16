# Recruit Skill

## Description

I want a skill that:

* Grants an **ability** called **Recruit.**
* When this **ability** is used, recruits the enemy that it is used on.

## Tutorial

**Step 1: Create an event that changes the target's team.**

<span dir="">Open the event editor and create a **global** event</span>. `{unit2}` is the reference to the target in Events that are called on skills.

![des](./images/Recruit-Skill/des.png)

<span dir="">I left the AI setting blank. Enter whatever script you want to give the unit. I recommend just setting it to no AI.</span>

**Step 2: Create an Item that calls this event.**

![des2](./images/Recruit-Skill/des2.png)

<span dir="">The Event on Hit component must refer to the event script you just made.</span> That field is what calls the event specifically.

**Step 3: Create a Skill that is an Ability, and that uses your new Item.**

<span dir="">Open the skill editor and create a new skill. This skill will let a unit use the item you just made as an ability from the action menu.</span>

![des4](./images/Recruit-Skill/des4.png)

**Step 4: Add this skill to a unit or class.**

![des5](./images/Recruit-Skill/des5.png)

<span dir="">That’s all there is to it. Note that right now it’s extremely overpowered and game-breaking as it can recruit any unit (even bosses) and always works as long as the item hits. You will need to tailor it to work like you want by editing the item components and the event script.</span>