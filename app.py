import requests
import folium
from streamlit_folium import st_folium

import streamlit as st
import os

API_URL = os.environ.get("API_URL", "https://taxifare.lewagon.ai")

NYC_COORDS = [40.75, -73.98]
NYC_BOUNDS = {"min_lat": 40.5, "max_lat": 41.0, "min_lng": -74.3, "max_lng": -73.7}

POINTS = {"pickup": "green", "dropoff": "red"}


@st.cache_data(ttl="1h")
def call_api(params):
    print("call_api", params)
    r = requests.get(f"{API_URL}/predict", params)
    r.raise_for_status()
    return r.json()


st.session_state.setdefault("mode", "Pickup")


def is_in_nyc(lat, lng):
    return (
        NYC_BOUNDS["min_lat"] <= lat <= NYC_BOUNDS["max_lat"]
        and NYC_BOUNDS["min_lng"] <= lng <= NYC_BOUNDS["max_lng"]
    )


def get_markers():
    fg = folium.FeatureGroup(name="points")
    for key, color in POINTS.items():
        if key in st.session_state:
            folium.Marker(st.session_state[key], icon=folium.Icon(color=color)).add_to(
                fg
            )
    return fg


@st.fragment(key="map")
def render_locations():
    if "next_mode" in st.session_state:
        st.session_state.mode = st.session_state.pop("next_mode")

    mode = st.segmented_control(
        "Click sets…",
        ["Pickup", "Dropoff"],
        key="mode",
        persist_state="session",
        selection_mode="single",
        required=True,
        default=st.session_state.mode,
    )
    f_map = folium.Map(tiles="Stadia.OSMBright", location=NYC_COORDS, zoom_start=12)

    fg = get_markers()

    # Render map
    out = st_folium(
        f_map,
        key="st_map",
        height=500,
        width=700,
        feature_group_to_add=fg,
        returned_objects=["last_clicked"],
    )
    print(out)

    # Handle session state
    if out["last_clicked"]:
        point = (out["last_clicked"]["lat"], out["last_clicked"]["lng"])

        if not is_in_nyc(point[0], point[1]):
            st.warning("You like Clowns do you ? They are mostly around NYC 🤡")
            return
        if st.session_state.get("last_handled_click") != point:
            st.session_state["last_handled_click"] = point
            st.session_state[mode.lower()] = point
            st.session_state["next_mode"] = (
                "Pickup" if mode.lower() == "dropoff" else "Dropoff"
            )
            st.rerun(scope="fragment")


def render_form():
    with st.form("ride_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.datetime_input(
                "When's the pickup date and time ?",
                persist_state="session",
                key="pickup_datetime",
            )
        with col2:
            st.slider(
                "How many passengers ?",
                1,
                10,
                persist_state="session",
                key="passenger_count",
            )

        submitted = st.form_submit_button("Predict")
        if submitted:
            if "pickup" not in st.session_state or "dropoff" not in st.session_state:
                st.warning("Please select pickup and dropff locations")
                return

            pick_lat, pick_lng = st.session_state["pickup"]
            dropoff_lat, dropoff_lng = st.session_state["dropoff"]

            params = {
                "pickup_datetime": st.session_state.pickup_datetime,
                "pickup_longitude": pick_lng,
                "pickup_latitude": pick_lat,
                "dropoff_longitude": dropoff_lng,
                "dropoff_latitude": dropoff_lat,
                "passenger_count": st.session_state.passenger_count,
            }
            try:
                response = call_api(params)
                st.write("Ride cost", f"$ {response["fare"]:.2f}")
            except requests.RequestException as rqerr:
                st.error("API Http Error", icon="🚨")
                st.error(rqerr.args[0])


########### RENDERING ###########

"""
# TaxiFareModel Predictor
"""

"""
### Choose Pickup and Dropoff locations
"""
render_locations()
render_form()
