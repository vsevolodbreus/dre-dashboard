from pathlib import Path

import duckdb

from utils.logger import logger

TABLE_NAME = "dubailand_tx_hist"

data_dir = Path(__file__).parent.parent / "data"
db_file = data_dir / "dre.db"
source_file = data_dir / "dubailand-tx-hist-data.csv"

FIELD_NAMES = {
    "transaction_number": "tx_number",
    "transaction_date": "tx_ts",
    "transaction_date_year": "tx_year",
    "property_id": "prop_id",
    "transaction_type": "tx_type",
    "transaction_subtype": "tx_subtype",
    "registration_type": "reg_type",
    "is_free_hold": "is_free_hold",
    "usage": "usage",
    "area": "area",
    "property_type": "prop_type",
    "property_subtype": "prop_subtype",
    "amount": "tx_value",
    "transaction_size_sq_m": "tx_size_sqm",
    "property_size_sq_m": "prop_size_sqm",
    "rooms": "rooms",
    "parking": "parking",
    "nearest_metro": "near_metro",
    "nearest_mall": "near_mall",
    "nearest_landmark": "near_landmark",
    "number_of_buyers": "buy_count",
    "number_of_sellers": "sell_count",
    "master_project": "master_project",
    "project": "project",
}


def create_table() -> None:
    """Create table in DuckDB and persist res data in it."""

    con = duckdb.connect(str(db_file.resolve()))

    # --- drop and (re) create table
    logger.info(f"dropping and recreating {TABLE_NAME}")
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")

    con.execute(
        f"""
        CREATE TABLE {TABLE_NAME} (        
            {FIELD_NAMES["transaction_number"]} varchar,
            {FIELD_NAMES["transaction_date"]} timestamp,
            {FIELD_NAMES["transaction_date_year"]} varchar,
            {FIELD_NAMES["property_id"]} numeric,
            {FIELD_NAMES["transaction_type"]} varchar,
            {FIELD_NAMES["transaction_subtype"]} varchar,
            {FIELD_NAMES["registration_type"]} varchar,
            {FIELD_NAMES["is_free_hold"]} varchar,
            {FIELD_NAMES["usage"]} varchar,
            {FIELD_NAMES["area"]} varchar,
            {FIELD_NAMES["property_type"]} varchar,
            {FIELD_NAMES["property_subtype"]} varchar,
            {FIELD_NAMES["amount"]} numeric,
            {FIELD_NAMES["transaction_size_sq_m"]} numeric,
            {FIELD_NAMES["property_size_sq_m"]} numeric,
            {FIELD_NAMES["rooms"]} varchar,
            {FIELD_NAMES["parking"]} varchar,
            {FIELD_NAMES["nearest_metro"]} varchar,
            {FIELD_NAMES["nearest_mall"]} varchar,
            {FIELD_NAMES["nearest_landmark"]} varchar,
            {FIELD_NAMES["number_of_buyers"]} integer,
            {FIELD_NAMES["number_of_sellers"]} integer,
            {FIELD_NAMES["master_project"]} varchar,
            {FIELD_NAMES["project"]} varchar
        ); """
    )

    # --- copy data into db from new csv file
    logger.info(f"copying data into {TABLE_NAME}")
    con.execute(f"COPY {TABLE_NAME} FROM '{str(source_file)}' ( HEADER ) ;")
    logger.info(f"finished copying data into {TABLE_NAME}")


if __name__ == "__main__":
    create_table()
