(Build-Engine)=
# Build Engine

If you want to be able to distribute an executable to others for release and playtesting, this document will tell you how.

## Non-Python Process

If you are working with an executable version of the editor, follow this process. 

You can download the current version of the standalone engine from here: https://gitlab.com/rainlash/lt-maker/-/jobs/artifacts/release/download?job=build_engine (Download will start automatically!)

![GenericEngineProject](images/GenericEngineProject.png)

Unzip the download, stick your `.ltproj` file in the folder `lt_engine/lt_engine` (should be at the same level as `app`, `Include`, etc.), and then you should be good to go. Test that the engine works with your project, and then re-zip it all up for distribution to others!

## Python Process

If are working with the Python version of the **Lex Talionis** engine, follow this process.

First, make sure that you have everything installed from the [Python Installation](PyInstall) guide, including PyInstaller.

Next, go to your `/saves/config.ini` file and set debug to 0. Make sure it says `debug=0` at the top. This will remove the debug menu and some other small things from your game that you probably don't want the player to have access to.

Make sure that your .ltproj folder is located directly in the `lt-maker` directory. For instance, I put my `lion_throne.ltproj` folder right next to the other folders, like `app`, `saves`, `sprites`, etc.

Now from **Git Bash** in the `lt-maker` directory, run:

`./utilities/build_tools/engine_build.sh lion_throne`

You should replace `lion_throne` with the name of your own project file. If your project file is called `blazing_sword.ltproj`, use `blazing_sword`.

If bash gives you an error like "cannot locate file", try running `chmod 777 ./utilities/build_tools/engine_build.sh`, and then try again.

It may take several minutes to build the engine. You should see some text appear on the terminal, and then `Done` should appear.

## Complete!

Your engine, ready for distribution, should be one directory above the `lt-maker` directory, and named the same as your project. Make sure to test it out first before delivering it to others!
