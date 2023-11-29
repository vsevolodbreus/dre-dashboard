import datetime
from typing import Optional

import pandas as pd
import streamlit


@streamlit.cache_data
def augment_tx_data(df: pd.DataFrame) -> pd.DataFrame:
    """Adds the following new columns to the transactions dataframe:
    - week_number
    - tx_date (YYYY-MM-DD)
    - tx_value_usd
    - price_sqm
    """
    df["week_number"] = df["tx_ts"].dt.isocalendar().week
    df["tx_date"] = df["tx_ts"].dt.strftime("%Y-%m-%d")
    df["tx_value_usd"] = df["tx_value"] / 3.6725  # TODO: fetch dynamically
    df["price_sqm"] = df["tx_value_usd"] / df["prop_size_sqm"]
    return df


@streamlit.cache_data
def get_slice_of_data(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Gets the section of the data for the provided week"""
    return df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]


@streamlit.cache_data
def get_number_of_tx(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> int:
    """Gets the total number of transactions for the provided date range"""
    return df.loc[
        (df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)
    ].shape[0]


@streamlit.cache_data
def get_total_tx_value(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> float:
    """Gets the total value of transactions for the provided date range"""
    return df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)][
        "tx_value_usd"
    ].sum()


@streamlit.cache_data
def get_median_tx_value_per_sqm(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> float:
    """Gets the median transaction value per sq. m. for the provided date range"""
    return df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)][
        "price_sqm"
    ].median(0, numeric_only=True)


@streamlit.cache_data
def get_median_rental_value(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> float:
    """Gets the median rental transaction value for the provided date range"""
    # TODO: get data from rental data-set
    return 0.0


@streamlit.cache_data
def get_largest_tx(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> float:
    """Gets the largest transaction value for the provided date range"""
    return df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)][
        "tx_value_usd"
    ].max(numeric_only=True)


@streamlit.cache_data
def get_tx_by_type(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Get the transactions grouped by type for the provided date range"""
    return (
        df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby(["prop_type", "tx_date"], as_index=False)
        .count()
    )


@streamlit.cache_data
def get_reg_type(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Get the transactions grouped by registration type for the provided date range"""
    df_temp = (
        df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby("reg_type", as_index=False)
        .count()
    )
    df_temp["reg_type_temp"] = ""
    return df_temp


@streamlit.cache_data
def get_payment_type(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Get the payment methods used the provided date range"""
    df_temp = (
        df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby("tx_type", as_index=False)
        .count()
    )
    df_temp["payment_method_temp"] = ""
    return df_temp


@streamlit.cache_data
def record_sale(df: pd.DataFrame):
    df = df[(df["prop_type"] != "Land")]
    df = df.sort_values(by=["tx_value"], ascending=False)
    df = df[:5]
    df = df[
        [
            "tx_date",
            "project",
            "tx_value",
            "tx_value_usd",
            "prop_type",
            "reg_type",
            "tx_subtype",
            "rooms",
            "week_number",
        ]
    ]
    df["tx_value"] = df["tx_value"].map("{:,.0f}".format)
    df["tx_value_usd"] = df["tx_value_usd"].map("{:,.0f}".format)
    return df


@streamlit.cache_data
def get_median_price_sqm(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Get median price of square meter for the provided date range"""
    return (
        df[["tx_date", "price_sqm"]]
        .loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby(["tx_date"], as_index=False)
        .median(numeric_only=True)
    )


@streamlit.cache_data
def get_top_tx(
    df: pd.DataFrame,
    from_date: datetime.date,
    to_date: datetime.date,
    top: Optional[int] = 5,
) -> pd.DataFrame:
    """Get top transactions to display"""
    df_temp = (
        df[(df["prop_type"] != "Land")]
        .loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .sort_values(by=["tx_value_usd"], ascending=False)[:top][
            [
                "project",
                "area",
                "tx_value_usd",
                "tx_size_sqm",
                "prop_subtype",
            ]
        ]
    )
    df_temp["tx_value_usd"] = df_temp["tx_value_usd"].map("{:,.0f}".format)
    return df_temp.set_index(pd.Index(list(range(1, top + 1))))


@streamlit.cache_data
def get_top_projects(
    df: pd.DataFrame,
    from_date: datetime.date,
    to_date: datetime.date,
    top: Optional[int] = 5,
) -> pd.DataFrame:
    """Get top projects to display"""
    df_temp = (
        df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby("project")
        .agg({"tx_number": "count", "tx_value_usd": "sum"})
        .reset_index()
        .rename(columns={"tx_number": "units_sold"})
        .sort_values("units_sold", ascending=False)[:top]
    )
    df_temp["tx_value_usd"] = df_temp["tx_value_usd"].map("{:,.0f}".format)
    return df_temp.set_index(pd.Index(list(range(1, top + 1))))


@streamlit.cache_data
def get_tx_by_room_type(
    df: pd.DataFrame, from_date: datetime.date, to_date: datetime.date
) -> pd.DataFrame:
    """Get median price of square meter for the provided date range"""
    return (
        df.loc[(df.tx_ts.dt.date >= from_date) & (df.tx_ts.dt.date <= to_date)]
        .groupby(["rooms"], as_index=False)
        .count()
        .sort_values(by=["rooms"], ascending=False)
    )
