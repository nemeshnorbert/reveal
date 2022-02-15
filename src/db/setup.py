import db.create
import db.read


def setup_database(db_path, src_path):
    db.create.create_database(db_path)
    if src_path is not None:
        db.read.read_rates(db_path, src_path)
