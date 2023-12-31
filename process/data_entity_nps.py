import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

from process.loader import Loader

from typing import Tuple
import os
import re


class NPS:
    def __init__(self):
        self.data = self.load_data()

    @staticmethod
    def load_data():
        # Load NPS process
        loader = Loader()
        loader.set_path("./asset/entity_wage")
        data = pd.read_csv(loader.data_filename_nps(), encoding='cp949')

        # Clean process - pick essential column
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

        # Clean process - pick only seoul process
        data = data.loc[data['j_addr'].str.contains('서울특별시')]

        # Clean process - drop paper company (SPC etc.)
        pattern = r'\d'
        data = data[~data['business'].str.contains('/', na=False)]
        data = data[~data['business'].str.contains('학교', na=False)]
        data = data[~data['business'].str.contains('조합', na=False)]
        data = data[~data['business'].str.contains(pattern, na=False)]

        # Clean process - huristic.
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

    @staticmethod
    def prep_merge(data: pd.DataFrame):
        # Create 2 columns for joining key: SIG_CD and RN
        data['RN'] = data['r_addr'].apply(NPS.__road_addr_parse)
        data['SIG_CD'] = data['bjd'].apply(NPS.__sig_cd_parse)
        return data


class CollectEntityCoordinate:
    # Merge NPS entity with main
    # Merge NPS
    def __init__(self):
        # DART code process
        self.data = self.load_data(use_collected=True)

    @staticmethod
    def load_data(use_collected: bool = True):
        loader = Loader()
        loader.set_path("./asset/entity_dart")
        if use_collected:
            data = pd.read_csv(loader.data_filename_collected())
        else:
            data = pd.read_csv(loader.data_filename_dart(), index_col=0)
        return data

    # Business name cleaning will be done by multiple stages
    # After each stage you try to match the name.
    @staticmethod
    def clean_name_stg1(val: str):
        # Remove company types and white spaces
        s = str(val)
        s = (s.replace(' ', '').
             replace('（주）', '').  # Different (주)
             replace('(주)', '').
             replace('(주）', '').
             replace('(재)', '').
             replace('(사)', '').
             replace('(유)', '').
             replace('(유한)', '').
             replace('(특수법인)', '').
             replace('(직장)', '').
             replace('본사', '').
             replace('국내', '').
             replace('해외', '').
             replace('주식회사', '').
             replace('유한회사', ''))
        return s

    @staticmethod
    def clean_name_stg2(val: str):
        # Replace English company name into Korean
        rep = {
            'A': '에이', 'B': '비', 'C': '씨', 'D': '디', 'E': '이',
            'F': '에프', 'G': '지', 'H': '에이치', 'I': '아이', 'J': '제이',
            'K': '케이', 'L': '엘', 'M': '엠', 'N': '엔', 'O': '오', 'P': '피',
            'Q': '큐', 'R': '알', 'S': '에스', 'T': '티', 'U': '유', 'V': '브이',
            'W': '더블유', 'X': '엑스', 'Y': '와이', 'Z': '지'
        }
        s = str(val)
        for alp, kor in rep.items():
            s = s.replace(alp, kor)
        return s

    @staticmethod
    def clean_name_stg3(val: str):
        # Change targeted name - SK, LG, 기업은행 등
        # From NPS -> DART
        specific = {
            '중소기업은행': '기업은행',
            '신한금융지주회사': '신한지주',
            'KB금융지주': 'KB금융',
            '에쓰-오일': 'S-Oil',
            '뱅크오브아메리카': '아메리카은행',
            '한화생명보험': '한화생명',
            '한국생산성본부': '한국생산성본부인증원',

            # LG Group
            '엘지': 'LG',

            # SK Group
            '에스케이': 'SK',

            # GS Group
            '지에스': 'GS',

            # NICE Group
            '나이스': 'NICE'
        }
        s = str(val)
        for fuckups, dart_standard in specific.items():
            s = s.replace(fuckups, dart_standard)
        return s

    @staticmethod
    def clean_duplicate(data: pd.DataFrame, full_address: str, part_address: (str, str)):
        land_addr, road_addr = part_address

        data_np = data.to_numpy()

        no_dup = list()
        for idx, addr in enumerate(data[[full_address, land_addr, road_addr]].to_numpy()):
            full, land, road = addr
            condition_land = land.replace(' ', '') in full.replace(' ', '')
            condition_road = road.replace(' ', '') in full.replace(' ', '')
            if condition_land or condition_road:
                no_dup.append(data_np[idx])
        return pd.DataFrame(no_dup, columns = data.columns)

    def clean(self, nps_data: pd.DataFrame) -> pd.DataFrame:
        nps = nps_data.copy(deep=True)
        nps['corpNm'] = nps['business']

        col = nps.columns
        post_clean_col = ['corpNm', 'address', 'ppl', 'amount', 'ppp']

        s1, f1 = self._try1(nps)  # First clean up
        s2, f2 = self._try2(f1[col])  # Second clean up (First clean up cumulative)
        s3, _ = self._try3(f2[col])  # Third clean up

        s1 = self.clean_duplicate(s1, 'address', ('j_addr', 'r_addr'))[post_clean_col]
        s2 = self.clean_duplicate(s2, 'address', ('j_addr', 'r_addr'))[post_clean_col]
        s3 = self.clean_duplicate(s3, 'address', ('j_addr', 'r_addr'))[post_clean_col]

        clean = pd.concat([s1, s2, s3]).reset_index(drop=True)
        return clean

    def _try1(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg1)
        mrg = pd.merge(data, self.data, on=['corpNm'], how='left')

        success = mrg.loc[mrg['address'].notna()]
        fail = mrg.loc[mrg['address'].isna()]
        return success, fail

    def _try2(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg1)
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg2)
        mrg = pd.merge(data, self.data, on=['corpNm'], how='left')

        success = mrg.loc[mrg['address'].notna()]
        fail = mrg.loc[mrg['address'].isna()]
        return success, fail

    def _try3(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg1)
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg2)
        data.loc[:, 'corpNm'] = data['corpNm'].apply(self.clean_name_stg3)
        mrg = pd.merge(data, self.data, on=['corpNm'], how='left')

        success = mrg.loc[mrg['address'].notna()]
        fail = mrg.loc[mrg['address'].isna()]
        return success, fail

    @staticmethod
    def address_to_coord(addr: str, verbose: bool = False):
        """
        Return the coordinates tuple of given full address
        """
        # Strip address of brackets substring and whitespaces
        clean_addr = (re.sub(r'\(.*?\)', '', addr)
                      .strip()
                      .replace('  ', ' '))
        if verbose:
            print(f"Query vworld for {clean_addr}")

        url = 'http://api.vworld.kr/req/address'
        params = {
            "service": "address",
            "request": "getcoord",
            "crs": "epsg:4326",
            "address": clean_addr,
            "format": "json",
            "type": "road",
            "key": os.getenv('VWORLD')
        }
        resp = requests.get(url, params= params)
        if resp.status_code == 200:
            try:
                return resp.json()['response']['result']['point']
            except KeyError:
                # Empty coordinate
                return {'x': np.nan, 'y': np.nan}
        else:
            raise FileNotFoundError(f"Query vworld fail for {clean_addr}")
