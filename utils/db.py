import duckdb
import pandas as pd
import streamlit as st


@st.cache_data(ttl=300, show_spinner=True)
def get_all_tx_data() -> pd.DataFrame:
    """Get transaction data from DUckDB"""

    query = """
        WITH tx_data as (
            SELECT
                tx_number,
                tx_ts,
                tx_type,
                tx_subtype,
                reg_type,
                is_free_hold,
                usage,
                area,
                prop_type,
                prop_subtype,
                tx_value,
                tx_size_sqm,
                prop_size_sqm,
                rooms,
                parking,
                near_metro,
                near_mall,
                near_landmark,
                buy_count,
                sell_count,
                master_project,
                project
            FROM dubailand_tx_hist
            UNION ALL
            SELECT 
                tx_number,
                tx_ts,
                tx_type,
                tx_subtype,
                reg_type,
                is_free_hold,
                usage,
                area,
                prop_type,
                prop_subtype,
                tx_value,
                tx_size_sqm,
                prop_size_sqm,
                rooms,
                parking,
                near_metro,
                near_mall,
                near_landmark,
                buy_count,
                sell_count,
                master_project,
                project
            FROM dubailand_tx )
        SELECT tx.*, da."area" AS area_norm, da.latitude, da.longitude FROM tx_data tx
        JOIN dubai_areas da
        ON LOWER(tx.area) = da.area
        ORDER BY tx.tx_ts ASC;
    """

    with duckdb.connect("data/dre.db", read_only=True) as con:
        return con.sql(query).df()


@st.cache_data(ttl=300, show_spinner=True)
def get_tx_data() -> pd.DataFrame:
    """Get transaction data from DuckDB"""

    query = """
        SELECT dt.*, da."area" AS area_norm, da.latitude, da.longitude FROM dubailand_tx dt
        JOIN dubai_areas da
        ON LOWER(dt.area) = da.area
        ORDER BY dt.tx_ts ASC;
    """

    with duckdb.connect("data/dre.db", read_only=True) as con:
        return con.sql(query).df()


@st.cache_data(ttl=300, show_spinner=True)
def get_dubai_areas() -> pd.DataFrame:
    """Get Dubai areas/coordinates data from DuckDB"""

    query = """
        SELECT *
        FROM dubai_areas da
        ORDER BY area ASC;
    """

    with duckdb.connect("data/dre.db", read_only=True) as con:
        return con.sql(query).df()


def persist_changes_dubai_areas(df: pd.DataFrame) -> None:
    """Save any changes to the dubai areas table in DuckDB."""

    with duckdb.connect("data/dre.db", read_only=False) as con:
        con.execute(f"DROP TABLE IF EXISTS dubai_areas;")
        con.execute(
            f"""
            CREATE TABLE dubai_areas (
                "area" varchar unique not null,
                "latitude" FLOAT8,
                "longitude" FLOAT8
            );
            """
        )
        con.register("df", df)
        con.execute(f"INSERT INTO dubai_areas SELECT * FROM df;")
