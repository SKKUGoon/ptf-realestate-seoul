import pandas as pd
from pyproj import Geod

from enum import Enum
from copy import copy, deepcopy
import math

from const_major_coordinate import BaseBoundary


class Coordinate:
    def __init__(self, longitude: float, latitude: float):
        # Define the WGS84 engine ellipsoid coordinate system
        self.geod = Geod(ellps='WGS84')

        self.lon = longitude
        self.lat = latitude

    @property
    def coordinate(self):
        return self.lon, self.lat

    def move(self, distance_meter: float, direction: str, new: bool = True):
        """
        Move 'distance_meter' to any direction in north, east, south and west and
            returns the new (longitude, latitude)
        """
        head = {
            "north": 0,
            "east": 90,
            "south": 180,
            "west": 270,
        }

        new_lon, new_lat, _ = self.geod.fwd(self.lon, self.lat, head[direction], distance_meter)

        if new is False:
            self.lon = new_lon
            self.lat = new_lat
            return self

        return Coordinate(new_lon, new_lat)

    def __copy__(self):
        # Create a new instance with the same longitude and latitude
        new_copy = Coordinate(*self.coordinate)
        return new_copy


class GridElement:
    def __init__(self, center: Coordinate, grid_size_meter: float):
        self.center = center
        self.single_size = grid_size_meter

        self.data_single = dict()

        # Nearby Grid
        self.neighbor_up: GridElement | None = None
        self.neighbor_down: GridElement | None = None
        self.neighbor_left: GridElement | None = None
        self.neighbor_right: GridElement | None = None

    def __repr__(self):
        up, down, left, right = None, None, None, None

        if self.neighbor_up is not None:
            up = self.neighbor_up.center.coordinate
        if self.neighbor_down is not None:
            down = self.neighbor_down.center.coordinate
        if self.neighbor_left is not None:
            left = self.neighbor_left.center.coordinate
        if self.neighbor_right is not None:
            right = self.neighbor_right.center.coordinate

        rep = f"""
{" " * len(str(left))} {up}

{left}-{self.center.coordinate}-{right}

{" " * len(str(left))} {down}
"""
        return rep

    def __deepcopy__(self, memodict: dict = {}):
        new_copy = GridElement.__new__(GridElement)

        # Copy each attribute using deepcopy
        for key, value in self.__dict__.items():
            setattr(new_copy, key, deepcopy(value, memodict))

        # Correct the neighbor references
        if self.neighbor_up is not None:
            new_copy.neighbor_up = deepcopy(self.neighbor_up, memodict)
        if self.neighbor_down is not None:
            new_copy.neighbor_down = deepcopy(self.neighbor_down, memodict)
        if self.neighbor_left is not None:
            new_copy.neighbor_left = deepcopy(self.neighbor_left, memodict)
        if self.neighbor_right is not None:
            new_copy.neighbor_right = deepcopy(self.neighbor_right, memodict)

        return new_copy

    def set_data_value(self, data_key: str, data_value: any):
        if data_key in self.data_single.keys():
            self.data_single[data_key] += data_value
        else:
            self.data_single[data_key] = data_value

    @property
    def top_left(self) -> Coordinate:
        return (self.center.
                move(self.single_size / 2, 'north').
                move(self.single_size / 2, 'west'))

    @property
    def top_right(self) -> Coordinate:
        return (self.center.
                move(self.single_size / 2, 'north').
                move(self.single_size / 2, 'east'))

    @property
    def bottom_left(self) -> Coordinate:
        return (self.center.
                move(self.single_size / 2, 'south').
                move(self.single_size / 2, 'west'))

    @property
    def bottom_right(self):
        return (self.center.
                move(self.single_size / 2, 'south').
                move(self.single_size / 2, 'east'))

    def has(self, lon: float = None, lat: float = None, coord: Coordinate = None) -> bool:
        if lat is None and lon is None and coord is None:
            raise RuntimeError("must enter (lat, lon) or coordinate")

        grid_top_left = self.top_left
        grid_bottom_right = self.bottom_right

        if lat is not None and lon is not None:
            if (grid_bottom_right.lat < lat < grid_top_left.lat
                    and grid_top_left.lon < lon < grid_bottom_right.lon):
                return True
            else:
                return False

        elif coord is not None:
            if (grid_bottom_right.lat < coord.lat < grid_top_left.lat
                    and grid_top_left.lon < coord.lon < grid_bottom_right.lon):
                return True
            else:
                return False

        else:
            raise RuntimeError("check your input")


class Grid:
    EARTH_RADIUS = 6371.0

    def __init__(self, start: Coordinate, boundary: BaseBoundary, grid_size_meter: float):
        self.boundary = boundary

        self.start = start
        self.single_size = grid_size_meter

        self.grid_element_map = dict()

    def n_by_m_coordinate(self) -> [Coordinate]:
        # n (vertical) * m (horizontal) grid. Control n with latitude, and m with longitude
        n = (self.boundary.UP.value + self.boundary.DOWN.value) * 1000 // self.single_size + 1
        m = (self.boundary.LEFT.value + self.boundary.RIGHT.value) * 1000 // self.single_size + 1

        # Calculate top right of the grid
        grid_start = (self.start.
                      move(self.boundary.UP.value * 1000, 'north').
                      move(self.boundary.LEFT.value * 1000, 'west').
                      move(self.single_size, 'west'))

        result = []
        for i in range(n):
            grid_i = copy(grid_start).move(i * self.single_size, 'south', False)

            for j in range(m):
                grid_i = grid_i.move(self.single_size, 'east', False)
                result.append(copy(grid_i))

        return result

    def n_by_m_gridelement(self) -> [GridElement]:
        n = (self.boundary.UP.value + self.boundary.DOWN.value) * 1000 // self.single_size + 1
        m = (self.boundary.LEFT.value + self.boundary.RIGHT.value) * 1000 // self.single_size + 1

        grid_center_points = self.n_by_m_coordinate()
        grid_elements = [GridElement(p, grid_size_meter=self.single_size)
                         for p in grid_center_points]

        # Assign each grid index
        for idx, e in enumerate(grid_elements):
            e.set_data_value('index', idx)
            self.grid_element_map[idx] = e

        # Assign relationship with each grid
        for i in range(n):
            no_up = i == 0
            no_down = i == (n - 1)

            for j in range(m):
                no_left = j == 0
                no_right = j == (m - 1)

                if not no_up:
                    grid_elements[i * m + j].neighbor_up = grid_elements[(i - 1) * m + j]
                if not no_down:
                    grid_elements[i * m + j].neighbor_down = grid_elements[(i + 1) * m + j]
                if not no_left:
                    grid_elements[i * m + j].neighbor_left = grid_elements[i * m + (j - 1)]
                if not no_right:
                    grid_elements[i * m + j].neighbor_right = grid_elements[i * m + (j + 1)]
                # print(f'Grid index {i}/{n-1}, {j}/{m-1}: {not no_up} {not no_down} {not no_left} {not no_right}')

        return grid_elements

    def n_by_m_dataframe(self) -> pd.DataFrame:
        grid_points = self.n_by_m_coordinate()
        grid_df = pd.DataFrame(
            list(map(lambda x: x.coordinate, grid_points)),
            columns=['lon', 'lat']
        )
        return grid_df


def trickle_down(g: GridElement,
                 value_key: str,
                 single_grid_meter: int | float,
                 total_distance_meters: int | float,
                 trickle_type: str = 'linear-square'):
    if trickle_type != 'linear-square':
        raise NotImplementedError('soon add bell curved decay')

    trickle_down_iter = (total_distance_meters // single_grid_meter
                         + (total_distance_meters % single_grid_meter != 0))
    if trickle_down_iter == 0:
        trickle_down_values = [g.data_single[value_key]]
    else:
        # Since 'linear' create arithmetic sequence trickle
        d = (g.data_single[value_key] - 0) / (trickle_down_iter)
        trickle_down_values = [g.data_single[value_key] - i * d
                               for i in range(trickle_down_iter + 1)]

    # Set relation
    assert 'index' in g.data_single.keys()
    center = g.data_single['index']
    if g.neighbor_down is not None:
        vertical = abs(g.data_single['index'] - g.neighbor_down.data_single['index'])
    elif g.neighbor_up is not None:
        vertical = abs(g.data_single['index'] - g.neighbor_up.data_single['index'])
    else:
        raise RuntimeError('given grid is a line? double check')

    layer_group = list(reversed(range(0, trickle_down_iter + 1))) + list(range(0, trickle_down_iter + 1))[1:]
    result = dict()
    start_index = center - (vertical * trickle_down_iter) - (1 * trickle_down_iter)
    for i in range(trickle_down_iter * 2 + 1):
        for j in range(trickle_down_iter * 2 + 1):
            if i == trickle_down_iter and j == trickle_down_iter:
                # Center. Already has a original value
                continue

            # Trickle down value
            group = max(layer_group[i], layer_group[j])
            value_add = trickle_down_values[group]

            # Set trickle down value to grid map index. Index starts from 0
            if start_index + (i * vertical + j) >= 0:
                result[start_index + (i * vertical + j)] = value_add

    return result
