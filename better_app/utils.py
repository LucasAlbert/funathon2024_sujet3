"""
Utils.
"""
from typing import Dict, Optional, List
from FlightRadar24 import FlightRadar24API
import numpy as np


def fetch_flight_data(
    client: FlightRadar24API,
    airline_icao: Optional[str] = None,
    aircraft_type: Optional[str] = None,
    zone_str: Optional[str] = None
) -> List[Dict]:
    """
    Fetch flight data from FlightRadar24 API for
    a given airline, aircraft type and zone.

    Args:
        client (FlightRadar24API): FlightRadar24API client.
        airline_icao (str): ICAO code of the airline.
        aircraft_type (str): Type of aircraft.
        zone_str (str): Zone string.

    Returns:
        List[Dict]: List of flights. A flight should be represented
            as a dictionary with latitude, longitude and id keys.
    """
    zone = client.get_zones()[zone_str]
    bounds = client.get_bounds(zone)

    flights = client.get_flights(
        aircraft_type=aircraft_type,
        airline=airline_icao,
        bounds=bounds
    )
    return [
        {
            "latitude": flight.latitude,
            "longitude": flight.longitude,
            "id": flight.id,
        } for flight in flights
    ]


def update_rotation_angles(data: List[Dict], previous_data: List[Dict]) -> None:
    """
    Update flights data by adding a rotation angle key.

    Args:
        data (List[Dict]): Flight data at time $t$ containing dictionaries
            with longitude, latitude and id keys.
        previous_data (List[Dict]): Flight data at time $t-1$ containing dictionaries
            with longitude, latitude and id keys.
    """
    for idx, flight_data in enumerate(data):
        identifier = flight_data["id"]
        if identifier not in [data["id"] for data in previous_data]:
            bearing = 0
        else:
            previous_flight_data = next(item for item in previous_data if item["id"] == identifier)
            longitude = flight_data["longitude"]
            latitude = flight_data["latitude"]
            previous_longitude = previous_flight_data["longitude"]
            previous_latitude = previous_flight_data["latitude"]

            # If no change keep previous bearing
            if (longitude == previous_longitude) & (latitude == previous_latitude):
                bearing = previous_flight_data["rotation_angle"]
            else:
                bearing = bearing_from_positions(
                    longitude,
                    latitude,
                    previous_longitude,
                    previous_latitude,
                )

        flight_data.update(rotation_angle=bearing)
    return


def bearing_from_positions(
    longitude: float,
    latitude: float,
    previous_longitude: float,
    previous_latitude: float,
) -> float:
    """
    Compute bearing from two sets of coordinates, at
    t-1 and t. Bearing is measured clockwise from the north.

    Args:
        longitude (float): Longitude (in degrees).
        latitude (float): Latitude (in degrees).
        previous_longitude (float): Previous longitude (in degrees).
        previous_latitude (float): Previous latitude (in degrees).

    Returns:
        float: Bearing in degrees.
    """
    lat1, lon1, lat2, lon2 = map(
        np.radians,
        [previous_latitude, previous_longitude, latitude, longitude]
    )
    y = np.sin(lon2-lon1)*np.cos(lat2)
    x = np.cos(lat1)*np.sin(lat2) - np.sin(lat1)*np.cos(lat2)*np.cos(lat2-lat1)
    alpha = np.arctan2(y, x)
    return (alpha*180/np.pi + 360) % 360

def get_closest_round_angle(angle: float) -> int:
    """
    Get closest round angle (multiple of 15 degrees)
    to the given angle.

    Args:
        angle (float): Given angle.

    Returns:
        int: Closest angle among the following values:
            0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150,
            165, 180, 195, 210, 225, 240, 255, 270,
            285, 300, 315, 330, 345.
    """
    if angle < 0:
        angle += 360
    q = angle // 15
    r = angle % 15
    if r > 7:
        q += 1
    if q == 24:
        return 0
    else:
        return int(q*15)

print(get_closest_round_angle(10))


def get_custom_icon(round_angle: int) -> Dict:
    """
    Get custom plane icon corresponding to the
    given round_angle.

    Args:
        round_angle (int): Round angle.

    Returns:
        Dict: Icon dict.
    """
    if round_angle not in [
        0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180,
        195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345
    ]:
        raise ValueError(
            "The round angle provided is not valid. "
            "Use the `get_closest_round_angle` function to get a valid angle."
        )
    icon_url = f'https://github.com/tomseimandi/flightradar/blob/main/img/plane_{round_angle}.png?raw=true'
    return dict(
        iconUrl=icon_url,
        iconSize=[38, 38],
    )
