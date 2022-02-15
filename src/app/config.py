import copy
import os
import pathlib

import app.utils


def _get_default_project_path():
    return pathlib.Path(__file__).resolve().parent.parent.parent


def _read_settings(path):
    return app.utils.read_json(path)


def _read_localizations(path):
    return app.utils.read_json(path)


def _read_datascheme(path):
    return app.utils.read_json(path)


def _read_credentials(api):
    api_name = api.upper()
    variable_name = f"{api_name}_APP_IDS"
    if variable_name not in os.environ:
        raise RuntimeError(f"Environment variable {variable_name} is not set")
    return [
        dict(app_id=app_id) for app_id in os.environ[variable_name].split(":")
    ]


def _setup_model_config(config, datascheme, project_path):
    database_config = config["convert"]["rates"]["database"]
    database_config["path"] = str(project_path / "resources" / "reveal.db")
    api_config = config["convert"]["rates"]["api"]
    api_config["credentials"] = _read_credentials(api_config["provider"])
    read_config = config["read"]
    read_config["renames"] = {
        info["name"]: info["field"] for info in datascheme
    }
    read_config["data_types"] = {
        info["field"]: info["data_type"] for info in datascheme
    }
    read_config["raw_data_types"] = {
        info["field"]: info["raw_data_type"] for info in datascheme
    }
    read_config["convert_infos"] = {
        info["field"]: info["convert_info"] for info in datascheme
    }
    read_config["fill_values"] = {
        info["name"]: info["fill_value"] for info in datascheme
    }


def _setup_view_config(config, datascheme, localizations):
    config["localizer"]["localizations"] = localizations
    tabs_group_config = config["elements"]["root"]["tabs_group"]
    tabs_group_config["table_tab"]["operations_table"]["columns"] = [
        {
            "field": info["name"],
            "name": info["name"],
            "data_type": info["data_type"],
        }
        for info in datascheme
    ]
    tabs_group_config["help_tab"]["help_table"]["columns"] = [
        {
            "field": info["field"],
            "data_type": info["data_type"],
            "value_required": info["value_required"],
        }
        for info in datascheme
    ]


def _setup_controller_config(config, project_path):
    example_path = project_path / "resources" / "example.xls"
    config["example_path"] = str(example_path)


def _build_config_impl(settings, datascheme, localizations, project_path):
    config = copy.deepcopy(settings)
    datascheme = copy.deepcopy(datascheme)
    localizations = copy.deepcopy(localizations)
    _setup_model_config(config["handler"]["model"], datascheme, project_path)
    _setup_view_config(config["handler"]["view"], datascheme, localizations)
    _setup_controller_config(config["handler"]["controller"], project_path)
    return config


def build_config(project_path=None):
    if project_path is None:
        project_path = _get_default_project_path()
    settings_path = project_path / "config" / "settings.json"
    settings = _read_settings(settings_path)
    localizations_path = project_path / "config" / "localizations.json"
    localizations = _read_localizations(localizations_path)
    datascheme_path = project_path / "config" / "datascheme.json"
    datascheme = _read_datascheme(datascheme_path)
    return _build_config_impl(settings, datascheme, localizations, project_path)
