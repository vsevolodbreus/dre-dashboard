from pathlib import Path

import duckdb

from utils.logger import logger

TABLE_NAME = "dubai_areas"

res_dir = Path(__file__).parent.parent / "res"
data_dir = Path(__file__).parent.parent / "data"
db_file = data_dir / "dre.db"
source_file = res_dir / "dubai-areas.csv"


def create_table() -> None:
    """Create table in DuckDB and persist res data in it."""

    con = duckdb.connect(str(db_file.resolve()))

    # --- drop and (re) create table
    logger.info(f"dropping and recreating {TABLE_NAME}")
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
    con.execute(
        f"""
        CREATE TABLE {TABLE_NAME} (
            "area" varchar unique not null,
            "latitude" FLOAT8,
            "longitude" FLOAT8
        );
        """
    )

    # --- copy data into db from new csv file
    logger.info(f"copying data into {TABLE_NAME}")
    con.execute(f"COPY {TABLE_NAME} FROM '{str(source_file)}' ;")
    logger.info(f"finished copying data into {TABLE_NAME}")


if __name__ == "__main__":
    create_table()
