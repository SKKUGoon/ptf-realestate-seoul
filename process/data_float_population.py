import pandas as pd

from process.loader import Loader
from util import clean_remove_bracket, clean_subway_line_name


class FloatPopulationSubwayTime:
    def __init__(self, usage_month: int | None = None):
        # Population process
        self.data = self.load_data()
        if usage_month is not None:
            print(f"Using only {usage_month} data")
            self.data = self.data.loc[self.data['사용월'] == usage_month]

    @staticmethod
    def load_data():
        # Load population process
        loader = Loader()
        loader.set_path("./asset/float_subway_time")
        data = pd.read_csv(loader.data_filename_subway_time(), encoding='euc-kr')

        # Clean process
        data = clean_remove_bracket(data)
        data = clean_subway_line_name(data, '호선명')

        return data

    def get_timely_data(self, hour: int) -> pd.DataFrame:
        def _pad(val: int, standard: int = 2):
            s = str(val)
            if len(s) < standard:
                return f"0{val}"
            else:
                return str(val)

        assert 0 <= hour < 24
        embark = f"{_pad(hour)}시-{_pad(hour+1)}시 승차인원"
        disembark = f"{_pad(hour)}시-{_pad(hour+1)}시 하차인원"

        segment = self.data[['사용월', '호선명', '지하철역', embark, disembark]]
        segment.columns = ['date', 'line', 'stn', 'embark', 'disembark']
        segment['time'] = [f"{_pad(hour)}시-{_pad(hour+1)}시"] * len(segment)
        return segment


if __name__ == "__main__":
    from dao.dao import SimpleDatabaseAccess
    from process.constant import subway_tpop_column

    fpt = FloatPopulationSubwayTime()
    df = fpt.data

    dao = SimpleDatabaseAccess()
    for i in range(0, 24):
        dfseg = fpt.get_timely_data(i)
        dao.insert_dataframe(
            dfseg,
            'FACTOR_SUBWAY_POPULATION_HOUR',
            subway_tpop_column,
            'append',
            True
        )



