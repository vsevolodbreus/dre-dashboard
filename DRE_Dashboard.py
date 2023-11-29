import ast
import datetime
import enum
from pathlib import Path

import pandas as pd
import pkg_resources
import plotly.express as px
import pydeck as pdk
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from utils.db import get_dubai_areas, get_tx_data, persist_changes_dubai_areas
from utils.formulas import percent_change
from utils.transformations import (
    augment_tx_data,
    get_largest_tx,
    get_median_price_sqm,
    get_median_rental_value,
    get_median_tx_value_per_sqm,
    get_number_of_tx,
    get_payment_type,
    get_reg_type,
    get_slice_of_data,
    get_top_projects,
    get_top_tx,
    get_total_tx_value,
    get_tx_by_room_type,
    get_tx_by_type,
)


class QuickSelectTimeDelta(enum.Enum):
    LAST_DAY = "last day"
    LAST_WEEK = "last week"
    LAST_TWO_WEEKS = "last two weeks"
    LAST_30_DAYS = "last month"
    CUSTOM = "custom"


class AreaUnits(enum.Enum):
    SQ_FEET = "Sq. Feet"
    SQ_METERS = "Sq. Meters"


class DisplayUnits(enum.Enum):
    TX_QTY = "Tx Qty."
    TX_VALUE = "Tx Value"


# --- session state configuration
if "area_units" not in st.session_state:
    st.session_state.area_units = AreaUnits.SQ_METERS.value

if "display_units" not in st.session_state:
    st.session_state.display_units = DisplayUnits.TX_VALUE.value


def set_quick_select_timedelta_values():
    st.session_state.quick_select_timedelta = QuickSelectTimeDelta.CUSTOM.value


def set_selected_date_values():
    st.session_state.search_date_to = datetime.date.today()
    if st.session_state.quick_select_timedelta == QuickSelectTimeDelta.LAST_DAY.value:
        st.session_state.search_date_from = datetime.date.today() - datetime.timedelta(
            days=1
        )
    if st.session_state.quick_select_timedelta == QuickSelectTimeDelta.LAST_WEEK.value:
        st.session_state.search_date_from = datetime.date.today() - datetime.timedelta(
            weeks=1
        )
    if (
        st.session_state.quick_select_timedelta
        == QuickSelectTimeDelta.LAST_TWO_WEEKS.value
    ):
        st.session_state.search_date_from = datetime.date.today() - datetime.timedelta(
            weeks=2
        )
    if (
        st.session_state.quick_select_timedelta
        == QuickSelectTimeDelta.LAST_30_DAYS.value
    ):
        st.session_state.search_date_from = datetime.date.today() - datetime.timedelta(
            days=30
        )


# --- Set page configuration
st.set_page_config(page_title="DRE Insights Dashboard", page_icon="📈", layout="wide")

# --- USER AUTHENTICATION
file_path = Path(__file__).parent / "users.yaml"
with file_path.open("r") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

name, authentication_status, username = authenticator.login("Login", "main")

# --- Auth Error
if authentication_status is False:
    st.error("Username/password is incorrect")

if authentication_status is None:
    st.warning("Please enter your username and password")

# --- Run Application if auth is successful
if authentication_status:
    # --- Configure Sidebar
    st.sidebar.title(f"Welcome {name}!")
    st.sidebar.markdown("---")

    st.sidebar.markdown("#### SELECT A PREDEFINED RANGE:")
    quick_select_timedelta = st.sidebar.selectbox(
        label="Select a predefined range:",
        label_visibility="collapsed",
        options=(
            QuickSelectTimeDelta.CUSTOM.value,
            QuickSelectTimeDelta.LAST_DAY.value,
            QuickSelectTimeDelta.LAST_WEEK.value,
            QuickSelectTimeDelta.LAST_TWO_WEEKS.value,
            QuickSelectTimeDelta.LAST_30_DAYS.value,
        ),
        key="quick_select_timedelta",
        on_change=set_selected_date_values,
    )

    st.sidebar.markdown("#### OR SELECT CUSTOM DATE RANGE")

    search_date_from = st.sidebar.date_input(
        label="Search date from:",
        value=datetime.date.today() - datetime.timedelta(
            weeks=1
        ),
        min_value=datetime.date(2023, 1, 1),
        max_value=datetime.date.today(),
        key="search_date_from",
        on_change=set_quick_select_timedelta_values,
    )

    search_date_to = st.sidebar.date_input(
        label="Search date to:",
        min_value=datetime.date(2023, 1, 1),
        max_value=datetime.date.today(),
        key="search_date_to",
        on_change=set_quick_select_timedelta_values,
    )

    # --- map options
    st.sidebar.markdown("---")

    st.sidebar.markdown("#### SELECT MAP LAYERS")
    display_units = DisplayUnits(
        st.sidebar.radio(
            label="Quantity vs. Price",
            label_visibility="collapsed",
            options=[DisplayUnits.TX_VALUE.value, DisplayUnits.TX_QTY.value],
            key="display_units",
            index=0,
            horizontal=True,
            on_change=None,
        )
    )

    map_display_layer_price_sqm = st.sidebar.checkbox(
        label=f"Price per {st.session_state.area_units}",
        value=False,
        key="map_display_layer_price_sqm",
        on_change=None,
    )

    st.sidebar.markdown("#### SELECT AREA UNITS")
    area_units = AreaUnits(
        st.sidebar.radio(
            label="Which Units to use?",
            label_visibility="collapsed",
            options=[AreaUnits.SQ_METERS.value, AreaUnits.SQ_FEET.value],
            key="area_units",
            index=0,
            horizontal=True,
            on_change=None,
        )
    )

    # --- sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f'Version: {pkg_resources.get_distribution("dre_dashboard").version}'
    )
    authenticator.logout("Logout", "sidebar")

    # --- Main view
    st.write("# DRE Insights Dashboard")
    st.write("---")

    tx_data = augment_tx_data(get_tx_data())
    tx_data_slice = get_slice_of_data(
        df=tx_data, from_date=search_date_from, to_date=search_date_to
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    # --- Total number of transactions
    with col1:
        current_slice_number_of_tx = get_number_of_tx(
            df=tx_data, from_date=search_date_from, to_date=search_date_to
        )
        past_slice_number_of_tx = get_number_of_tx(
            df=tx_data,
            from_date=search_date_from - (search_date_to - search_date_from),
            to_date=search_date_from,
        )
        st.metric(
            label="Number of Transactions",
            value="{:,.0f}".format(current_slice_number_of_tx),
            delta="{:.1f}%".format(
                percent_change(
                    x1=past_slice_number_of_tx,
                    x2=current_slice_number_of_tx,
                )
            ),
        )

    # --- Total transaction value
    with col2:
        current_slice_total_tx_value = get_total_tx_value(
            df=tx_data, from_date=search_date_from, to_date=search_date_to
        )
        past_slice_total_tx_value = get_total_tx_value(
            df=tx_data,
            from_date=search_date_from - (search_date_to - search_date_from),
            to_date=search_date_from,
        )
        st.metric(
            label="Total Transaction Value",
            value="${:,.0f}".format(current_slice_total_tx_value),
            delta="{:.1f}%".format(
                percent_change(
                    x1=past_slice_total_tx_value,
                    x2=current_slice_total_tx_value,
                )
            ),
        )

    # --- Median transaction value per sq. m.
    with col3:
        current_slice_median_tx_value_per_sqm = get_median_tx_value_per_sqm(
            df=tx_data, from_date=search_date_from, to_date=search_date_to
        )
        past_slice_median_tx_value_per_sqm = get_median_tx_value_per_sqm(
            df=tx_data,
            from_date=search_date_from - (search_date_to - search_date_from),
            to_date=search_date_from,
        )
        st.metric(
            label="Median Transaction Value (per sq. m.)",
            value="${:,.0f}".format(current_slice_median_tx_value_per_sqm),
            delta="{:.1f}%".format(
                percent_change(
                    x1=past_slice_median_tx_value_per_sqm,
                    x2=current_slice_median_tx_value_per_sqm,
                )
            ),
        )

    # --- Median rental price
    with col4:
        current_slice_median_rental_value = get_median_rental_value(
            df=tx_data, from_date=search_date_from, to_date=search_date_to
        )
        past_slice_median_rental_value = get_median_rental_value(
            df=tx_data,
            from_date=search_date_from - (search_date_to - search_date_from),
            to_date=search_date_from,
        )
        st.metric(
            label="Median Rental Value",
            value="${:,.0f}".format(current_slice_median_rental_value),
            delta="{:.1f}%".format(
                percent_change(
                    x1=past_slice_median_rental_value,
                    x2=current_slice_median_rental_value,
                )
            ),
        )

    # --- Largest transaction value
    with col5:
        current_slice_largest_tx = get_largest_tx(
            df=tx_data, from_date=search_date_from, to_date=search_date_to
        )
        past_slice_largest_tx = get_largest_tx(
            df=tx_data,
            from_date=search_date_from - (search_date_to - search_date_from),
            to_date=search_date_from,
        )
        st.metric(
            label="Largest Transaction",
            value="${:,.0f}".format(current_slice_largest_tx),
            delta="{:.1f}%".format(
                percent_change(
                    x1=past_slice_largest_tx,
                    x2=current_slice_largest_tx,
                )
            ),
        )

    col1, col2 = st.columns(2)

    with col1:
        # --- Transaction type data figures
        fig = px.bar(
            title="Transactions by type",
            data_frame=get_tx_by_type(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            x="tx_date",
            y="tx_number",
            color="prop_type",
        )
        st.plotly_chart(fig, theme="streamlit")

        # --- by room type
        fig = px.bar(
            title="By Room Type",
            data_frame=get_tx_by_room_type(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            x="tx_number",
            y="rooms",
            orientation="h",
            height=560,
        )
        st.plotly_chart(fig, theme="streamlit")

        # --- test
        # import plotly.graph_objects as go
        #
        # fig = go.Figure(go.Bar(
        #     x=[20, 14, 23],
        #     y=['giraffes', 'orangutans', 'monkeys'],
        #     orientation='h'))
        # st.plotly_chart(fig, theme="streamlit")

    with col2:
        # --- Median price per unit data figure
        fig = px.area(
            title=f"Median Price per {st.session_state.area_units}",
            data_frame=get_median_price_sqm(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            x="tx_date",
            y="price_sqm",
        )
        st.plotly_chart(fig, theme="streamlit")

        # --- Payment method data figure
        fig = px.bar(
            title="By Payment Method?",
            data_frame=get_payment_type(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            x="tx_number",
            y="payment_method_temp",
            color="tx_type",
            orientation="h",
            height=270,
            labels={"tx_type": "Quantity", "payment_method_temp": ""},
        )
        st.plotly_chart(fig, theme="streamlit")

        # --- Registration type data figure
        fig = px.bar(
            title="By Registration",
            data_frame=get_reg_type(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            x="tx_number",
            y="reg_type_temp",
            color="reg_type",
            orientation="h",
            height=270,
            facet_col_spacing=0.9,
            labels={"tx_number": "Quantity", "reg_type_temp": ""},
        )
        st.plotly_chart(fig, theme="streamlit")

    col1, col2 = st.columns(2)

    with col1:
        # --- Top 5 Transactions
        st.markdown("##### Top 5 Transactions")
        st.dataframe(
            data=get_top_tx(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            use_container_width=True,
        )

    with col2:
        # --- Top 5 Projects
        st.markdown("##### Top 5 Projects")
        st.dataframe(
            data=get_top_projects(
                df=tx_data, from_date=search_date_from, to_date=search_date_to
            ),
            use_container_width=True,
        )

    # --- Dubai map
    layers = []
    tooltip = {"text": "area: {area}"}

    if display_units == DisplayUnits.TX_QTY:
        # TODO: Move to transforms
        df_temp = (
            tx_data_slice[["latitude", "longitude", "tx_number"]][
                tx_data_slice[["latitude", "longitude"]].notnull().all(1)
            ]
            .groupby(["latitude", "longitude"], as_index=False)
            .count()
        )

        df_temp["norm_count"] = (df_temp["tx_number"] - df_temp["tx_number"].min()) / (
            df_temp["tx_number"].max() - df_temp["tx_number"].min()
        )

        layers.append(
            pdk.Layer(
                "ColumnLayer",
                data=df_temp,
                get_position="[longitude, latitude]",
                get_elevation="norm_count",
                get_fill_color=[
                    "200 + norm_count * 50",
                    "255 - norm_count * 255",
                    0,
                    130,
                ],
                radius=150,
                elevation_scale=20000,
                auto_highlight=True,
                pickable=True,
                extruded=True,
            )
        )

        tooltip["text"] += "\ntx_qty: {tx_number}"

    if display_units == DisplayUnits.TX_VALUE:
        # TODO: Move to transforms
        df_temp = (
            tx_data_slice[["latitude", "longitude", "tx_value_usd"]][
                tx_data_slice[["latitude", "longitude"]].notnull().all(1)
            ]
            .groupby(["latitude", "longitude"], as_index=False)
            .sum("tx_value_usd")
        )
        df_temp["norm_tx_value_usd"] = (
            df_temp["tx_value_usd"] - df_temp["tx_value_usd"].min()
        ) / (df_temp["tx_value_usd"].max() - df_temp["tx_value_usd"].min())

        layers.append(
            pdk.Layer(
                "ColumnLayer",
                data=df_temp,
                get_position="[longitude, latitude]",
                get_elevation="norm_tx_value_usd",
                get_fill_color=[
                    "200 + norm_tx_value_usd * 50",
                    "255 - norm_tx_value_usd * 255",
                    0,
                    130,
                ],
                radius=150,
                elevation_scale=20000,
                auto_highlight=True,
                pickable=True,
                extruded=True,
            )
        )

        tooltip["text"] += "\ntx_value_usd: {tx_value_usd}"

    if map_display_layer_price_sqm is True:
        # TODO: move...
        areas_polygons = pd.read_csv("res/dubai-areas-poygons.csv")
        areas_polygons = areas_polygons[["area", "latitude", "longitude", "polygons"]]
        areas_polygons["polygons"] = areas_polygons["polygons"].apply(
            lambda x: ast.literal_eval(x)
        )

        df_temp = (
            tx_data_slice[["latitude", "longitude", "price_sqm"]][
                tx_data_slice[["latitude", "longitude"]].notnull().all(1)
            ]
            .groupby(["latitude", "longitude"], as_index=False)
            .median("price_sqm")
        )

        df_temp["norm_price_sqm"] = (
            df_temp["price_sqm"] - df_temp["price_sqm"].min()
        ) / (df_temp["price_sqm"].max() - df_temp["price_sqm"].min())

        df_temp = df_temp.merge(areas_polygons, on=["latitude", "longitude"])

        layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=df_temp,
                get_polygon="polygons",
                opacity=0.8,
                auto_highlight=True,
                pickable=True,
                stroked=False,
                filled=True,
                wireframe=True,
                get_fill_color=[
                    "200 + norm_price_sqm * 50",
                    "255 - norm_price_sqm * 255",
                    0,
                    90,
                ],
                get_line_color=[255, 255, 255],
            )
        )

        tooltip["text"] += "\nprice_sqm: {price_sqm}"

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=25.176987,
                longitude=55.256249,
                zoom=10.5,
                pitch=50,
                bearing=0,
            ),
            layers=layers,
            tooltip=tooltip,
        )
    )

    # --- Map Coordinates
    expander_areas = st.expander("Dubai Areas & Projects Coordinates")
    dubai_areas_edited_df = expander_areas.experimental_data_editor(
        data=get_dubai_areas(),
        width=500,
        key="dubai_areas_edited_df",
        on_change=None,
        num_rows="dynamic",
    )
    expander_areas.write(st.session_state.dubai_areas_edited_df)
    expander_areas.button(
        label="Update Areas",
        on_click=persist_changes_dubai_areas,
        kwargs={"df": dubai_areas_edited_df},
    )

    # --- Table Data
    expander_data = st.expander("Raw Table Data")
    expander_data.dataframe(tx_data_slice)
