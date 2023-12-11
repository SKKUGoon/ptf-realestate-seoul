import pandas as pd

from process.data_entity_nps import NPS, CollectEntityAddress
from process.loc_road import RoadMapper
from grid.grid import Coordinate, Grid, grid_matching_point
from grid.grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid.grid_major_coordinate import GangnamStnBoundary

from dao.dao import SimpleDatabaseAccess
from process.constant import road_column

dao = SimpleDatabaseAccess()
df_db = NPS.prep_merge(dao.select_dataframe('FACTOR_PENSION'))
collect = CollectEntityAddress()

# Clean the name of NPS. `corpNm` is on collect.data
df_db['corpNm'] = df_db['business'].apply(CollectEntityAddress.clean_name_stg1)

mrg = pd.merge(df_db, collect.data, on=['corpNm'], how='left')
mrg_success = mrg.loc[mrg['address'].notna()]
mrg_fail = mrg.loc[mrg['address'].isna()]

mrg_retry = mrg[df_db.columns].loc[mrg_fail.index]
mrg_retry['corpNm'] = mrg_retry['corpNm'].apply(CollectEntityAddress.clean_name_stg1)
mrg_retry['corpNm'] = mrg_retry['corpNm'].apply(CollectEntityAddress.clean_name_stg2)

mrg2 = pd.merge(mrg_retry, collect.data, on=['corpNm'], how='left')
mrg2_success = mrg2.loc[mrg2['address'].notna()]
mrg2_fail = mrg2.loc[mrg2['address'].isna()]

mrg_retry2 = mrg2[df_db.columns].loc[mrg2_fail.index]
mrg_retry2['corpNm'] = mrg_retry2['corpNm'].apply(CollectEntityAddress.clean_name_stg1)
mrg_retry2['corpNm'] = mrg_retry2['corpNm'].apply(CollectEntityAddress.clean_name_stg2)
mrg_retry2['corpNm'] = mrg_retry2['corpNm'].apply(CollectEntityAddress.clean_name_stg3)

mrg3 = pd.merge(mrg_retry2, collect.data, on=['corpNm'], how='left')
mrg3_success = mrg3.loc[mrg3['address'].notna()]
mrg3_fail = mrg3.loc[mrg3['address'].isna()]

mrg1_clean = CollectEntityAddress.clean_duplicate(mrg_success, 'address', ('j_addr', 'r_addr'))
mrg2_clean = CollectEntityAddress.clean_duplicate(mrg2_success, 'address', ('j_addr', 'r_addr'))
mrg3_clean = CollectEntityAddress.clean_duplicate(mrg3_success, 'address', ('j_addr', 'r_addr'))
