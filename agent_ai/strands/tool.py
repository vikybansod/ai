from strands import tool
from datetime import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="city_time_tool")
tf = TimezoneFinder()

@tool
def get_current_time(city: str) -> str:
    """Get the current time in a given city.
    Args:
        city: Name of the city to get the time for.
    """
    location = geolocator.geocode(city)

    if not location:
        return f"Could not find location for '{city}'."
    
    tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if not tz_name:
        return f"Could not determine timezone for '{city}'"

    tz = ZoneInfo(tz_name)
    return datetime.now(tz).strftime("%H:%M:%S")

