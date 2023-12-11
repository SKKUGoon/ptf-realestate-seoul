# Process NPS data
# Release processed data into database
# Get processed data from the database

from dao.dao import SimpleDatabaseAccess
from process.data_entity_nps import NPS
from process.constant import nps_column

nps = NPS()
df = nps.data  # Processed data

# Insert into database
dao = SimpleDatabaseAccess()
dao.insert_dataframe(
    nps.data,
    'FACTOR_PENSION',
    nps_column,
    'replace',
    True
)

# Retrieve it from database
df_db = NPS.prep_merge(
    dao.select_dataframe('FACTOR_PENSION')
)
