# NPS data is given with truncated address
# Merge NPS entity data with real-address given from DART
# Get coordinate from the Vworld using real-address.
# Save it in the database

import pandas as pd
import numpy as np
from dotenv import load_dotenv

from process.data_entity_nps import NPS, CollectEntityCoordinate
from dao.dao import SimpleDatabaseAccess

load_dotenv()

dao = SimpleDatabaseAccess()
df = NPS.prep_merge(dao.select_dataframe('FACTOR_PENSION'))

# Merge NPS entity data with real-address
collect = CollectEntityCoordinate()
cleaned = collect.clean(df)

# Get coordinate
coords = list()
for addr in cleaned['address']:
    try:
        coord = CollectEntityCoordinate.address_to_coord(
            addr,
            True
        )
        coords.append(coord)
    except FileNotFoundError as e:
        coords.append({'x': np.nan, 'y': np.nan})

coords_df = pd.DataFrame([[c['x'], c['y']] for c in coords],
                         columns=['x', 'y'])

# Merge NPS data with Coordinate
nps_with_coord = pd.concat([cleaned, coords_df], axis=1)





