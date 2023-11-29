from datetime import date
from pathlib import Path

import duckdb
import pydantic as pyd
import requests

from utils.logger import logger

TABLE_NAME = "dubailand_tx"

FIELD_NAMES = {
    "TRANSACTION_NUMBER": "tx_number",
    "INSTANCE_DATE": "tx_ts",
    "GROUP_EN": "tx_type",
    "PROCEDURE_EN": "tx_subtype",
    "IS_OFFPLAN_EN": "reg_type",
    "IS_FREE_HOLD_EN": "is_free_hold",
    "USAGE_EN": "usage",
    "AREA_EN": "area",
    "PROP_TYPE_EN": "prop_type",
    "PROP_SB_TYPE_EN": "prop_subtype",
    "TRANS_VALUE": "tx_value",
    "PROCEDURE_AREA": "tx_size_sqm",
    "ACTUAL_AREA": "prop_size_sqm",
    "ROOMS_EN": "rooms",
    "PARKING": "parking",
    "NEAREST_METRO_EN": "near_metro",
    "NEAREST_MALL_EN": "near_mall",
    "NEAREST_LANDMARK_EN": "near_landmark",
    "TOTAL_BUYER": "buy_count",
    "TOTAL_SELLER": "sell_count",
    "MASTER_PROJECT_EN": "master_project",
    "PROJECT_EN": "project",
}


def fetch(
    from_date: pyd.condate(ge=date(2023, 1, 1)) = date(2023, 1, 1),
    to_date: pyd.condate(ge=date(2023, 1, 1), le=date.today()) = date.today(),
    no_download: bool = False,
) -> Path:
    """Fetches file from Dubailand transaction data section."""

    url = "https://gateway.dubailand.gov.ae/open-data/transactions/export/csv"

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://dubailand.gov.ae",
        "Referer": "https://dubailand.gov.ae/",
        "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Brave";v="110"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    }

    body = {
        "parameters": {
            "P_FROM_DATE": from_date.strftime("%m/%d/%Y"),
            "P_TO_DATE": to_date.strftime("%m/%d/%Y"),
            "P_GROUP_ID": "",
            "P_IS_OFFPLAN": "",
            "P_IS_FREE_HOLD": "",
            "P_AREA_ID": "",
            "P_USAGE_ID": "",
            "P_PROP_TYPE_ID": "",
            "P_TAKE": "-1",
            "P_SKIP": "",
            "P_SORT": "TRANSACTION_NUMBER_ASC",
        },
        "command": "transactions",
        "labels": FIELD_NAMES,
    }

    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    output_file_name = (
        data_dir / "dubailand-tx-data-from-"
        f'{from_date.strftime("%d-%m")}-to-{to_date.strftime("%d-%m")}.csv'
    )

    if no_download:
        return output_file_name

    try:
        logger.info(f"fetching {url}")

        with requests.post(url=url, headers=headers, json=body, stream=True) as resp:
            resp.raise_for_status()
            with open(output_file_name, "wb") as f:
                for chunk in resp.iter_content():
                    f.write(chunk)

    except Exception as e:
        logger.error("fetching data failed!")
        logger.error(e)

    # Ensure file was downloaded
    if not output_file_name.exists():
        raise Exception(f"{output_file_name} was not downloaded")

    logger.info(f"successfully fetched {url}")
    logger.info(f"saved to file {output_file_name}")

    return output_file_name


def persist(data_file: Path) -> None:
    """Persists the data in DuckDB."""

    # --- Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    db_file = data_dir / "dre.db"
    con = duckdb.connect(str(db_file.resolve()))

    # --- drop and (re) create table
    logger.info(f"dropping and recreating {TABLE_NAME}")
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
    con.execute(
        f"""
        CREATE TABLE {TABLE_NAME} (
            {FIELD_NAMES["TRANSACTION_NUMBER"]} varchar,
            {FIELD_NAMES["INSTANCE_DATE"]} timestamp,
            {FIELD_NAMES["GROUP_EN"]} varchar,
            {FIELD_NAMES["PROCEDURE_EN"]} varchar,
            {FIELD_NAMES["IS_OFFPLAN_EN"]} varchar,
            {FIELD_NAMES["IS_FREE_HOLD_EN"]} varchar,
            {FIELD_NAMES["USAGE_EN"]} varchar,
            {FIELD_NAMES["AREA_EN"]} varchar,
            {FIELD_NAMES["PROP_TYPE_EN"]} varchar,
            {FIELD_NAMES["PROP_SB_TYPE_EN"]} varchar,
            {FIELD_NAMES["TRANS_VALUE"]} numeric,
            {FIELD_NAMES["PROCEDURE_AREA"]} numeric,
            {FIELD_NAMES["ACTUAL_AREA"]} numeric,
            {FIELD_NAMES["ROOMS_EN"]} varchar,
            {FIELD_NAMES["PARKING"]} varchar,
            {FIELD_NAMES["NEAREST_METRO_EN"]} varchar,
            {FIELD_NAMES["NEAREST_MALL_EN"]} varchar,
            {FIELD_NAMES["NEAREST_LANDMARK_EN"]} varchar,
            {FIELD_NAMES["TOTAL_BUYER"]} integer,
            {FIELD_NAMES["TOTAL_SELLER"]} integer,
            {FIELD_NAMES["MASTER_PROJECT_EN"]} varchar,
            {FIELD_NAMES["PROJECT_EN"]} varchar
        ); """
    )

    # --- copy data into db from new csv file
    logger.info(f"copying data into ")
    con.execute(f"COPY {TABLE_NAME} FROM '{str(data_file)}' (AUTO_DETECT TRUE);")
    logger.info(f"finished copying data into {TABLE_NAME}")


if __name__ == "__main__":
    persist(data_file=fetch(no_download=False))
