import pandas as pd

from loader import Loader
from util import clean_remove_bracket, clean_subway_line_name


class FloatPopulationSubwayTime:
    def __init__(self, usage_month: int | None = None):
        # Population data
        self.data = self.load_data()
        if usage_month is not None:
            print(f"Using only {usage_month} data")
            self.data = self.data.loc[self.data['사용월'] == usage_month]

    @staticmethod
    def load_data():
        # Load population data
        loader = Loader()
        loader.set_path("./asset/float_subway_time")
        data = pd.read_csv(loader.data_filename_subway_time(), encoding='euc-kr')

        # Clean data
        data = clean_remove_bracket(data)
        data = clean_subway_line_name(data, '호선명')

        return data


if __name__ == "__main__":
    fpt = FloatPopulationSubwayTime()
    df = fpt.data
