import pandas as pd

from loader import Loader
from util import clean_remove_bracket, clean_subway_line_name


class FloatPopulationSubwayTime:
    def __init__(self):
        # Population data
        self.data = self.load_data()

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

    # def attach_location(self):
    #     location = SubwayMapper()



class FloatPopulationSubwayDay:
    columns = ["date", "line", "station", "influx", "efflux", "regdate", "_del_"]

    def __init__(self):
        self.data = pd.DataFrame()
        ...

    def load_data(self, from_year: int = 2015, to_year: int = 2023):
        loader = Loader(max_month=10)
        loader.set_path("./asset/float_subway")

        # Data separated by month
        year_with_month = {2023}
        for y in range(from_year, to_year + 1):
            if y in year_with_month:
                yearly_data = pd.DataFrame()

                # Update monthly data
                for m in range(1, 13):
                    fn = loader.data_filename_subway_day(y, m)

                    if fn == "":
                        # Data's filename wasn't able to generate
                        continue

                    # Clean csv data
                    monthly_data = pd.read_csv(fn).reset_index()
                    monthly_data.columns = self.columns

                    yearly_data = pd.concat([yearly_data, monthly_data], axis=0)
            else:
                fn = loader.data_filename_subway_day(y)
                yearly_data = pd.read_csv(fn, encoding='euc-kr')

            self.data = yearly_data


if __name__ == "__main__":
    # float_population = FloatPopulationSubwayDay()
    # float_population.load_data(2023, 2023)
    # pd.read_csv(ind)

    float_population_time = FloatPopulationSubwayTime()
    float_population_time.load_data()


