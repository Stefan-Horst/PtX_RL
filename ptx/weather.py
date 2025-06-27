from glob import glob
import pandas as pd

from util import DATA_DIR


class WeatherDataProvider():
    """Wrapper for the weather data originally provided in multiple csv files."""
    
    def __init__(self, dir_data="yearly_profiles/"):
        self.weather_data = self._load_data(dir_data)
        self.weather_data_joined = pd.concat(self.weather_data)
    
    def get_weather_of_tick(self, tick):
        return self.weather_data_joined.iloc[tick]
    
    def get_weather_from_tick_plus_n(self, tick, n):
        """Returns n weather data points starting from tick"""
        return self.weather_data_joined.iloc[tick:tick+n]
    
    def get_weather_of_datetime(self, datetime):
        return self.weather_data_joined[
            self.weather_data_joined["time"] == pd.to_datetime(datetime)
        ]
    
    def get_weather_between_datetimes(self, datetime1, datetime2):
        """Returns all weather data points between datetime1 and datetime2 including these two."""
        return self.weather_data_joined[self.weather_data_joined["time"].between(
            pd.to_datetime(datetime1), pd.to_datetime(datetime2)
        )]
    
    def _load_data(self, dir_data):
        """Load all yearly csv files into a list of dataframes."""
        file_paths = glob(str(DATA_DIR / dir_data / "*.csv"))
        file_paths.sort()
        data = []
        for file_path in file_paths:
            yearly_data = pd.read_csv(file_path)
            yearly_data["time"] = pd.to_datetime(yearly_data["time"])
            data.append(yearly_data)
        return data
