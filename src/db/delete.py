import pathlib


def delete_database(db_path):
    return pathlib.Path(db_path).unlink(missing_ok=True)
