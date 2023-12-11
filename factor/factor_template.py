from grid.grid import Coordinate, Grid, grid_matching_point, grid_matching_line
from grid.grid_major_coordinate import GANGNAM_STN_LAT, GANGNAM_STN_LON
from grid.grid_major_coordinate import GangnamStnBoundary

# ---- Data Layout ---- #

# ---- Grid Mapping ---- #
gangnam = Coordinate(GANGNAM_STN_LON, GANGNAM_STN_LAT)
g = Grid(gangnam, GangnamStnBoundary, 100, "GangnamNPS")

# ---- Grid Assigning ---- #

# 1) If Grid matching to coordinate
matched_point = grid_matching_point(g, ..., (..., ...), True)
matched_np_point = matched_point.to_numpy()

# 2) If Grid matching to line
matched_line = grid_matching_line(g, ..., ..., True)
matched_np_line = matched_line.to_numpy()

g.push_data_to_grids({v[0]: v[...] for v in matched_np_point}, '...', '...', True)  # Your value

# ---- Grid Spillover ---- #

# ---- Data Display ---- #

