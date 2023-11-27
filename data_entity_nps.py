import pandas as pd
import numpy as np

from loader import Loader


class NPS:
    def __init__(self):
        self.data = self.load_data()
        self._prep_merge()

    @staticmethod
    def load_data():
        # Load NPS data
        loader = Loader()
        loader.set_path("./asset/entity_wage")
        data = pd.read_csv(loader.data_filename_nps(), encoding='cp949')

        # Clean data - pick essential column
        cols = [
            'data_gen_dt', 'business', 'business_nps_reg_code', 'business_reg_stat',
            'postcode', 'j_addr', 'r_addr', 'bjd', 'hjd', 'bjd_district', 'bjd_sgg', 'bjd_emd',
            'business_own', 'business_type', 'business_type_nm',
            'nps_dt', 're_reg', 'exit_reg', 'ppl', 'amount', 'ppl_new', 'ppl_exit'
        ]

        essential_cols = [
            'business', 'business_reg_stat', 'j_addr', 'r_addr', 'bjd', 'hjd',
            'business_own', 'business_type_nm', 'ppl', 'amount'
        ]

        data.columns = cols
        data = data[essential_cols]

        # Clean data - pick only seoul data
        data = data.loc[data['j_addr'].str.contains('서울특별시')]

        # Clean data - huristic.
        data['ppp'] = data['amount'] / data['ppl']
        data = data.loc[data['ppp'] >= 370490]  # Drop average NPS payment under 370,490 - 평균 연봉 1억
        data = data.loc[data['ppl'] >= 100]  # Drop business that has less than 100 employees.

        return data

    @staticmethod
    def __road_addr_parse(val: str):
        address_elements = str(val).split(" ")
        if len(address_elements) < 3:
            return np.nan
        else:
            return address_elements[2].replace(" ", "")

    @staticmethod
    def __sig_cd_parse(val: str):
        if len(str(val)) < 5:
            return np.nan
        return str(val)[:5]

    def _prep_merge(self):
        # Create 2 columns for joining key: SIG_CD and RN
        self.data['RN'] = self.data['r_addr'].apply(self.__road_addr_parse)
        self.data['SIG_CD'] = self.data['bjd'].apply(self.__sig_cd_parse)


if __name__ == "__main__":
    nps = NPS()
    df = nps.data
