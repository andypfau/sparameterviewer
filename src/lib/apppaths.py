from .utils import is_windows, open_file_in_default_viewer, is_running_from_binary
from info import Info

import os
from typing import Optional
from PyQt6.QtCore import QStandardPaths



class AppPaths:


    _content_dir: Optional[str] = None


    @staticmethod
    def _get_root_dir() -> str:
        lib_dir = os.path.abspath(os.path.dirname(__file__))
        src_dir = os.path.dirname(lib_dir)
        app_dir = os.path.dirname(src_dir)
        return app_dir
    

    @staticmethod
    def _get_content_dir() -> str:
        if AppPaths._content_dir is not None:
            return AppPaths._content_dir

        root_dir = AppPaths._get_root_dir()
        content_dir = root_dir

        # special case for compiled app
        if is_running_from_binary():
            binary_content_dir = os.path.join(content_dir, '_internal')
            if os.path.exists(binary_content_dir):
                content_dir = binary_content_dir

        AppPaths._content_dir = content_dir
        return content_dir


    @staticmethod
    def get_log_dir() -> str:
        return AppPaths._get_root_dir()


    def get_log_path() -> str:
        return os.path.join(AppPaths.get_log_dir(), 'sparamviewer.log')


    @staticmethod
    def get_resource_dir() -> str:
        return os.path.join(AppPaths._get_content_dir(), 'res')


    @staticmethod
    def get_doc_dir() -> str:
        return os.path.join(AppPaths._get_content_dir(), 'doc')


    @staticmethod
    def get_changelog() -> str:
        return os.path.join(AppPaths._get_root_dir(), 'CHANGELOG.md')


    @staticmethod
    def get_license() -> str:
        return os.path.join(AppPaths._get_root_dir(), 'LICENSE')


    @staticmethod
    def get_settings_dir(settings_format_version_str: str) -> str:
        return os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation),
            Info.Domain,
            Info.AppName,
            settings_format_version_str
        )


    @staticmethod
    def get_settings_path(settings_format_version_str: str) -> str:
        return os.path.join(AppPaths.get_settings_dir(settings_format_version_str), 'app_settings.json')


    @staticmethod
    def get_default_file_dir() -> str:
        return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
