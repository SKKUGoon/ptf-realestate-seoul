import pandas as pd

from loader import Loader
from util import clean_remove_bracket


class SubwayMapper:
    """
    Match
        subway data with coordinate (standard)
        subway data with float population (comparison)
    """
    def __init__(self):
        # Load standard data - coordinate data
        loader = Loader()
        loader.set_path("./asset/location")
        data = pd.read_csv(loader.data_filename_subway_location())
        data.columns = ['c1', 'station_name', 'line_name', 'lon', 'lat']

        self.standard = clean_remove_bracket(data)
        self.comparison = pd.DataFrame()

    def mount_comparison(self, tbm: pd.DataFrame,
                         station_name_col: str,
                         line_name_col:str):
        assert station_name_col in tbm.columns, "designate correct station name column"
        assert line_name_col in tbm.columns, "designate correct line name column"

        def _name_set_func(x: str) -> str:
            if x != station_name_col and x != line_name_col:
                return x
            elif x == station_name_col:
                return 'station_name'
            else:
                return 'line_name'

        # To be mapped
        self.comparison = tbm.copy()
        self.comparison.columns = [_name_set_func(c) for c in tbm.columns]
