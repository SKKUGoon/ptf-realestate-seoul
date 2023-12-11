from dao.dao import SimpleDatabaseAccess
from grid.grid import Coordinate, Grid, grid_matching_point
from grid.grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid.grid_major_coordinate import GangnamStnBoundary

# ---- Data Layout ---- #
# Get it from Database
dao = SimpleDatabaseAccess()
df = dao.select_geo_dataframe('CLEAN_PENSION')

# ---- Grid Mapping ---- #
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100, "GangnamNPS")

# ---- Grid Assigning ---- #
matched = grid_matching_point(g, df, ('x', 'y'), True)
matched_np = matched.to_numpy()

g.push_data_to_grids({v[0]: v[4] for v in matched_np}, 'amount', 'number', True)
g.push_data_to_grids({v[0]: v[1] for v in matched_np}, 'business', 'string', True)
g.push_data_to_grids({v[0]: v[3] for v in matched_np}, 'workers', 'number', True)

# ---- Grid Spillover ---- #
g.trickle_down(
    [g.grid_element_map[v[0]] for v in matched_np],
    1000 // g.single_size,
    'amount',
    '*0.8'
)

g.trickle_down(
    [g.grid_element_map[v[0]] for v in matched_np],
    1000 // g.single_size,
    'workers',
    '*0.6'
)

# ---- Data Display ---- #
df = g.grid_dataframe('amount')
dfw = g.grid_dataframe('workers')
dfn = g.grid_dataframe('business')

dfk = g.kepler_dataframe(['amount', 'workers', 'business'])
