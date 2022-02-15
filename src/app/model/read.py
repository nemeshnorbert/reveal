import pathlib

import pandas


def _build_converter(info):
    name = info["name"]
    if name == "datetime":
        return lambda arg: pandas.to_datetime(arg, format=info["format"])
    else:
        raise RuntimeError("Unknown convert_type {name}")


def _build_converters(convert_infos):
    return {
        column_name: _build_converter(info)
        for column_name, info in convert_infos.items()
        if info is not None
    }


def _build_dtypes(data_types, converters):
    return {
        column_name: data_type
        for column_name, data_type in data_types.items()
        if column_name not in converters
    }


def _read_operations(files, renames, raw_data_types, convert_infos):
    all_operations = []
    converters = _build_converters(convert_infos)
    dtypes = _build_dtypes(raw_data_types, converters)
    for filename, content in files.items():
        operations = pandas.read_excel(
            content,
            parse_dates=True,
            dtype=dtypes,
            converters=converters,
        )
        operations.rename(
            columns={renames[name]: name for name in renames}, inplace=True
        )
        operations["data_file"] = pandas.Series(
            pathlib.Path(filename).name,
            index=operations.index,
            dtype=dtypes[renames["data_file"]],
        )
        all_operations.append(operations)
    return pandas.concat(all_operations, ignore_index=True)


def _remove_transactions(operations, black_list):
    operations.drop(
        operations[operations["status"].isin(black_list)].index, inplace=True
    )


def _fill_missing_values(operations, fill_values):
    missing_date_mask = operations[operations["payment_date"].isnull()].index
    operations.drop(missing_date_mask, inplace=True)
    for column_name in operations.columns:
        operations[column_name].fillna(fill_values[column_name], inplace=True)


def _convert_dates(operations):
    for column_name in ["operation_date", "payment_date"]:
        operations[column_name] = operations[column_name].astype(
            "datetime64[ns]"
        )


class OperationsReader:
    def __init__(self, config):
        self._config = config

    def read(self, files):
        operations = _read_operations(
            files,
            self._config["renames"],
            self._config["raw_data_types"],
            self._config["convert_infos"],
        )
        _fill_missing_values(operations, self._config["fill_values"])
        _remove_transactions(operations, self._config["black_list_statuses"])
        _convert_dates(operations)
        return operations
