# Title Screen

In this section, we will change the default _The Lion Throne_ title screen to the one used by the _The Sacred Stones_. Once you understand how to do that, changing the title menu to use your own custom images should be easy.

![TitleScreen](images/TitleScreen/TitleScreen.png)
![SacredStonesTitleScreen](images/TitleScreen/Finished.png)

There are four main components to the title screen that you can change.

1. Logo
2. Press Start Icon
3. Background
4. Attribution

## Logo

Download the new Sacred Stones logo:

![SacredStonesLogo](images/TitleScreen/logo.png)

To do these changes, we will have to delve into your project's **resources/custom_sprites** directory. If a **custom_sprites** directory does not already exist for your project, create one (make sure it's named exactly **custom_sprites**). Then, put the Sacred Stones logo PNG file into that directory with the exact name **logo.png**.

![CustomSpritesFileExplorer](images/TitleScreen/CustomSpritesFileExplorer.png)

## Press Start

![PressStartSprite](images/TitleScreen/press_start.png)

This works similarly. If you have a new Press Start animation you want to show, you can add the PNG file to the **custom_sprites** directory in your project's **resources**. Make sure it's named exactly **press_start.png**.

![DifferentLogoTitleScreen](images/TitleScreen/ChangedLogo.png)

## Background

![SacredStonesBackground](images/TitleScreen/title_background.png)

Switching out the background is also a simple affair. Open up the Panoramas editor and locate the **title_background** panorama. Delete it. Now you can import your own background. It can be a static background like Sacred Stones uses, or you can import several png files at the same time as long as they have numbers at the end of their filenames (like **title_background0.png**, **title_background1.png**, etc.)

## Attribution

On the bottom left hand corner of the title screen is the attribution. You can change what it says from within your project's **game_data/translations.json** file.

```json
    {
        "nid": "_attribution",
        "text": "created by you"
    }
```

If it's not the last element in your json file, make sure you put a `,` at the end.

## Complete!
Now you can pull up the game and check out the new and improved title screen!

![FinishedTitleMenu](images/TitleScreen/Finished.png)
