class Loader:
    def __init__(self, max_month: int = None):
        self.path = ""
        self.max_month = max_month

    def set_path(self, path: str):
        if path[-1] == "/":
            self.path = path
        else:
            self.path = f"{path}/"

    def data_filename_subway_location(self):
        return f"{self.path}지하철_좌표.csv"

    def data_filename_subway_time(self):
        return f"{self.path}서울시_지하철_호선별_역별_시간대별_승하차_인원_정보.csv"

    def data_filename_subway_day(self, year: int, month: int = None) -> str:
        base_filename = "{}CARD_SUBWAY_MONTH_{}.csv"
        if month is None:
            assert year <= 2022
            return base_filename.format(self.path, str(year))
        else:
            assert year > 2022, "Years above 2023 needs month information"
            if month > self.max_month:
                return ""
            year_month = f'{year}{"0" * (2 - len(str(month)))}{str(month)}'
            return base_filename.format(self.path, str(year_month))


if __name__ == "__main__":
    loader = Loader()

    # Generate filename
    fn1 = loader.data_filename_subway_day(2023, 1)
    fn2 = loader.data_filename_subway_day(2021)
    print(fn1, fn2)
