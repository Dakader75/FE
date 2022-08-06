import os, sys

from app.constants import VERSION
from app.resources.resources import RESOURCES
from app.data.database import DB
from app.engine import engine
from app.engine import config as cf
from app.engine import driver
from app.engine import game_state
from app.engine.component_system_compiler import source_generator

def main(name: str):
    RESOURCES.load(name + '.ltproj')
    DB.load(name + '.ltproj')
    title = DB.constants.value('title')
    driver.start(title)
    game = game_state.start_game()
    driver.run(game)

def test_play(name: str):
    RESOURCES.load(name + '.ltproj')
    DB.load(name + '.ltproj')
    title = DB.constants.value('title')
    driver.start(title, from_editor=True)
    game = game_state.start_level('DEBUG')
    driver.run(game)

def inform_error():
    print("=== === === === === ===")
    print("A bug has been encountered.")
    print("Please copy this error log and send it to rainlash!")
    print('Or send the file "saves/debug.log.1" to rainlash!')
    print("Thank you!")
    print("=== === === === === ===")

def find_and_run_project():
    proj = '.ltproj'
    for name in os.listdir('./'):
        if name.endswith(proj):
            name = name.replace(proj, '')
            if name not in ('autosave',):
                main(name)

if __name__ == '__main__':
    import logging, traceback
    from app import lt_log
    success = lt_log.create_logger()
    if not success:
        engine.terminate()

    # compile necessary files
    if not hasattr(sys, 'frozen'):
        source_generator.generate_component_system_source()

    try:
        find_and_run_project()
        # main('lion_throne')
        # test_play('lion_throne')
        # test_play('sacred_stones')
    except Exception as e:
        logging.exception(e)
        inform_error()
        print('*** Lex Talionis Engine Version %s ***' % VERSION)
        print('Main Crash {0}'.format(str(e)))

        # Now print exception to screen
        import time
        time.sleep(0.5)
        traceback.print_exc()
        time.sleep(0.5)
        inform_error()
        engine.terminate(crash=True)
        if cf.SETTINGS['debug']:
            time.sleep(5)
        else:
            time.sleep(20)
