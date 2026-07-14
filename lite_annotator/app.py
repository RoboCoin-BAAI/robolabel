from __future__ import annotations

import os
import sys

from PyQt5.QtCore import QLibraryInfo
from PyQt5.QtWidgets import QApplication

from lite_annotator.main_window import MainWindow
from lite_annotator.ui_theme import apply_app_theme


def configure_qt_plugin_path() -> None:
    plugin_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path


def main() -> int:
    configure_qt_plugin_path()
    app = QApplication(sys.argv)
    app.setLibraryPaths([QLibraryInfo.location(QLibraryInfo.PluginsPath)])
    apply_app_theme(app)
    window = MainWindow()
    window.resize(1400, 850)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
