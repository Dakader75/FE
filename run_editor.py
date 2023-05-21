import os, sys

from app.editor.settings import MainSettingsController
from app.editor.editor_locale import init_locale
from app.engine.component_system_compiler import source_generator

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QLockFile, QDir, Qt
from PyQt5.QtGui import QIcon


if __name__ == '__main__':
    init_locale()
    # Hack to get a Windows icon to show up
    try:
        import ctypes
        myappid = u'rainlash.lextalionis.ltmaker.current' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        print("Maybe not Windows? But that's OK")

    # compile necessary files
    if not hasattr(sys, 'frozen'):
        source_generator.generate_component_system_source()

    from app import lt_log
    success = lt_log.create_logger()
    if not success:
        sys.exit()

    lockfile = QLockFile(QDir.tempPath() + '/lt-maker.lock')
    if lockfile.tryLock(100):
        # For High DPI displays
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

        ap = QApplication(sys.argv)
        ap.setWindowIcon(QIcon('favicon.ico'))
        from app import dark_theme
        theme = dark_theme.get_theme()
        dark_theme.set(ap, theme)
        from app.editor.main_editor import MainEditor
        window = MainEditor()
        window.show()
        ap.exec_()
    else:
        print('LT-maker is already running!')
