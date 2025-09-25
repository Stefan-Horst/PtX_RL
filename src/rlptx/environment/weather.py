from glob import glob
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from rlptx.util import DATA_DIR


WEATHER_DATA_DIR = "yearly_profiles/"


class WeatherDataProvider():
    """Wrapper for the weather data originally provided in multiple csv files."""
    
    def __init__(self, dir_data=WEATHER_DATA_DIR, ticks_per_day=24, test_size=0.1, seed=None):
        """This class directly provides the weather data in train and test sets. 
        The size of the test set is set to the last 20% of the total data by default."""
        self.dir_data = dir_data
        self.ticks_per_day = ticks_per_day
        self.test_size = test_size
        self.seed = seed
        self.weather_data = self._load_data(dir_data)
        self.weather_data_joined = pd.concat(self.weather_data, ignore_index=True)
        # train and test data must not be shuffled as it is a time series
        self.weather_data_train, self.weather_data_test = train_test_split(
            self.weather_data_joined, test_size=test_size, random_state=seed, shuffle=False
        )
        self.rng = np.random.default_rng(seed)
    
    def get_weather_from_random_plus_n(self, n, mode="train"):
        """Returns n consecutive weather data points from a random starting point. 
        The mode determines which data set is used."""
        assert mode in ["train", "test"], "Mode must be 'train' or 'test'."
        if mode == "train":
            weather_data = self.weather_data_train
        elif mode == "test":
            weather_data = self.weather_data_test
        start = self.rng.integers(0, len(weather_data) - n)
        return weather_data.iloc[start:start+n]
        
    
    def get_weather_from_tick_plus_n(self, tick, n, offset=0):
        """Returns n weather data points starting from tick"""
        actual_tick = tick + offset
        return self.weather_data_joined.iloc[actual_tick:actual_tick+n]
    
    def get_weather_of_tick(self, tick, offset=0):
        actual_tick = tick + offset
        return self.weather_data_joined.iloc[actual_tick]
    
    def get_weather_between_datetimes(self, datetime1, datetime2):
        """Returns all weather data points between datetime1 and datetime2 including these two."""
        return self.weather_data_joined[self.weather_data_joined["time"].between(
            pd.to_datetime(datetime1), pd.to_datetime(datetime2)
        )]
    
    def get_weather_of_datetime(self, datetime):
        return self.weather_data_joined[
            self.weather_data_joined["time"] == pd.to_datetime(datetime)
    ]
    
    def _load_data(self, dir_data):
        """Load all yearly csv files into a list of dataframes."""
        file_paths = glob(str(DATA_DIR / dir_data / "*.csv"))
        file_paths.sort()
        data = []
        for file_path in file_paths:
            yearly_data = pd.read_csv(file_path)
            yearly_data["time"] = pd.to_datetime(yearly_data["time"])
            yearly_data["dayofyear"] = yearly_data.index // self.ticks_per_day
            yearly_data["hour"] = yearly_data["time"].dt.hour
            data.append(yearly_data)
        return data

    def __repr__(self):
        return (f"WeatherDataProvider(dir_data={self.dir_data!r}, ticks_per_day={self.ticks_per_day}, "
                f"test_size={self.test_size}, seed={self.seed}, data_amount={len(self.weather_data_joined)})")
