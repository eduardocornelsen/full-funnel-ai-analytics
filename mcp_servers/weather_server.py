from fastmcp import FastMCP
import httpx
from datetime import datetime

# Initialize FastMCP server
mcp = FastMCP("Weather")

@mcp.tool()
async def get_historical_weather(latitude: float, longitude: float, date: str):
    """Get historical weather data for a specific location and date via Open-Meteo.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        date: YYYY-MM-DD
    """
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={date}&end_date={date}&daily=temperature_2m_max,precipitation_sum&timezone=auto"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        
    return {
        "date": date,
        "max_temp": data['daily']['temperature_2m_max'][0],
        "precipitation": data['daily']['precipitation_sum'][0],
        "unit": data['daily_units']
    }

if __name__ == "__main__":
    mcp.run()
