import pandas as pd
import numpy as np
from pyproj import Geod
from shapely import LineString, box

from collections import deque
from copy import copy

from grid.grid_major_coordinate import BaseBoundary


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

        self.index = -1  # -1 means that the Grid is yet to be assigned an index
        self.data_single = dict()

        # Nearby Grid
        self.north: GridElement | None = None
        self.south: GridElement | None = None
        self.west: GridElement | None = None
        self.east: GridElement | None = None

        self.northeast: GridElement | None = None
        self.northwest: GridElement | None = None
        self.southeast: GridElement | None = None
        self.southwest: GridElement | None = None

    def __repr__(self):
        def dply(val: GridElement | None, standard: int):
            if val is None:
                return ' ' * standard
            s = str(val.index)
            if len(s) > standard:
                return f"{len(s)[:(standard-3)]}..."
            elif len(s) == standard:
                return s
            else:
                return f"{s}{' '* (standard - len(s))}"

        display = {
            'n': self.north,
            's': self.south,
            'w': self.west,
            'e': self.east,
            'ne': self.northeast,
            'nw': self.northwest,
            'se': self.southeast,
            'sw': self.southwest,
        }
        max_pad = 0
        for obj in display.values():
            if obj is not None:
                max_pad = max(max_pad, len(str(obj.index)))

        rep = f"""
+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+
| {dply(self.northwest, max_pad)} | {dply(self.north, max_pad)} | {dply(self.northeast, max_pad)} |
+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+
| {dply(self.west, max_pad)} | {dply(self, max_pad)} | {dply(self.east, max_pad)} |
+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+
| {dply(self.southwest, max_pad)} | {dply(self.south, max_pad)} | {dply(self.southeast, max_pad)} |
+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+{'-' * (max_pad + 2)}+
{self.data_single}
"""
        return rep

    def upsert_data_value(self, data_key: str, data_value: any):
        if data_key in self.data_single.keys():
            self.data_single[data_key] += data_value
        else:
            self.data_single[data_key] = data_value

    def set_data_value(self, data_key: str, data_value: any):
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

    def pass_through(self, linestring: LineString) -> bool:
        """
        Checks if a shapely.geometry.LineString passes through or is contained
        :param linestring: shapely.geometry.LineString object.
        :return:
        """
        # Define a shapely box (polygon) representing the grid
        grid_box = box(
            self.top_left.lon, self.top_left.lat,
            self.bottom_right.lon, self.bottom_right.lat
        )

        # Check if the LineString intersects or is contained in the grid
        return grid_box.intersects(linestring) or grid_box.contains(linestring)


class Grid:
    EARTH_RADIUS = 6371.0

    def __init__(self, start: Coordinate, boundary: BaseBoundary, grid_size_meter: float, name: str):
        # Boundary and size define number of cells to be created
        self.boundary = boundary
        self.single_size = grid_size_meter

        # n (vertical) * m (horizontal) grid. Control n with latitude, and m with longitude
        self.n = (self.boundary.UP.value + self.boundary.DOWN.value) * 1000 // self.single_size + 1
        self.m = (self.boundary.LEFT.value + self.boundary.RIGHT.value) * 1000 // self.single_size + 1

        # Generate Grid Map, and its mapper.
        self.grid_name = f"{name}_{self.n}by{self.m}grid_{self.single_size}size"
        self.start = start
        self.grid_element_map = dict()
        self.nm_grid_element()

    def _create_nm_coordinate(self) -> [Coordinate]:
        """
        Create center coordinates for each to-be-generated grid element.
        :return: list of class Coordinate
        """
        # Calculate top right of the grid
        grid_start = (self.start.
                      move(self.boundary.UP.value * 1000, 'north').
                      move(self.boundary.LEFT.value * 1000, 'west').
                      move(self.single_size, 'west'))

        result = []
        for i in range(self.n):
            grid_i = copy(grid_start).move(i * self.single_size, 'south', False)

            for j in range(self.m):
                grid_i = grid_i.move(self.single_size, 'east', False)
                result.append(copy(grid_i))

        return result

    def nm_grid_element(self) -> [GridElement]:
        grid_center_points = self._create_nm_coordinate()
        grid_elements = [GridElement(p, grid_size_meter=self.single_size)
                         for p in grid_center_points]

        # Assign each grid an index. Record it in self.grid_element_map
        for idx, e in enumerate(grid_elements):
            e.index = idx
            self.grid_element_map[idx] = e

        # Assign relationship with each grid
        for i in range(self.n):
            no_up: bool = i == 0
            no_down: bool = i == (self.n - 1)

            for j in range(self.m):
                grid_to_assign = i * self.m + j

                no_left: bool = j == 0
                no_right: bool = j == (self.m - 1)

                # Right angle bearing assign
                if not no_up:
                    grid_elements[grid_to_assign].north = grid_elements[(i - 1) * self.m + j]
                if not no_down:
                    grid_elements[grid_to_assign].south = grid_elements[(i + 1) * self.m + j]
                if not no_left:
                    grid_elements[grid_to_assign].west = grid_elements[i * self.m + (j - 1)]
                if not no_right:
                    grid_elements[grid_to_assign].east = grid_elements[i * self.m + (j + 1)]

                # Diagonal bearing assign
                if not no_up and not no_left:
                    grid_elements[grid_to_assign].northwest = grid_elements[(i - 1) * self.m + j - 1]
                if not no_up and not no_right:
                    grid_elements[grid_to_assign].northeast = grid_elements[(i - 1) * self.m + j + 1]
                if not no_down and not no_left:
                    grid_elements[grid_to_assign].southwest = grid_elements[(i + 1) * self.m + j - 1]
                if not no_down and not no_right:
                    grid_elements[grid_to_assign].southeast = grid_elements[(i + 1) * self.m + j + 1]

        return grid_elements

    def push_data_to_grids(self, grid_data_map: dict, value_key: str, value_type: str, verbose: bool = False):
        """
        Push single or multiple process regarding one key into grids in the grid map
        :param grid_data_map: { grid index (as an identifier) : process value }
        :param value_key: Keys that'll be stored for Grid.data_single
        :param value_type: Differs by its type. string or number(float or int)
        :param verbose:
        """
        for k, v in self.grid_element_map.items():
            if value_type == "string":
                if k in grid_data_map.keys():
                    if verbose:
                        print(f"[Grid {k}] Update")
                        print(f"Already process inserted beforehand. Adding {grid_data_map[k]} to {self.grid_element_map[k]}")
                    v.upsert_data_value(value_key, f" {grid_data_map[k]}")
                else:
                    v.upsert_data_value(value_key, "")
            elif value_type == "number":
                if k in grid_data_map.keys():
                    if verbose:
                        print(f"[Grid {k}] Update")
                        print(f"Already process inserted beforehand. Adding {grid_data_map[k]} to {self.grid_element_map[k]}")
                    v.upsert_data_value(value_key, grid_data_map[k])
                else:
                    v.upsert_data_value(value_key, 0)
            else:
                raise RuntimeError(f"{value_type} not supported in `push_data_to_grids` function")

    def trickle_down(self,
                     startings: [GridElement],
                     steps: int,
                     value_key: str,
                     decay_factors: str,
                     initial_value: float | None = None):
        """
        Trickle downing can be started from multiple GridElement.
            For single GridElement the trickle-down effect are applied with for loop
        If there's an initial_value that trickling-down starts from
            use that initial_value and log it in the GridElement's data_single
            using `value_key`.
        However, if there's no initial_value (None), the tricking down starts from the
            value stored in GridElement's data_single found with `value_key`
        For each loop, `impace_value_name` is assigned as a key to be stored in data_single dictionary.
        When the for loop is done for all starting GridElement, temporary impact_value_name will be
            added to a single `value_key`.

        :param startings: Starting points for trickling down
        :param steps: How many steps to trickkle down.
            If 10, goes additional 10 GridElements away using BFS
        :param value_key: (See the main comment)
        :param decay_factors: Can be either "*<decay element>" or "-<decay element>" or "<decay element>"
        :param initial_value:
        """
        # Set individual trickle down event for value_key Grid wise
        value_names = set()
        for i, grid in enumerate(startings):
            # To prevent `set_data_value` updating the original trickled down value,
            # Use separate trickle_down_tmp
            impact_value_name = f"{value_key}_trickle_down_tmp_{i}"
            value_names.add(impact_value_name)
            if initial_value is not None:
                self._single_trickle_down_bfs(
                    grid,
                    steps,
                    impact_value_name,
                    initial_value,
                    decay_factors
                )
            else:
                self._single_trickle_down_bfs(
                    grid,
                    steps,
                    impact_value_name,
                    grid.data_single[value_key],
                    decay_factors
                )

        # Sum all the {value_key}_temp_{i} and make it into {value_key}
        for grid in self.grid_element_map.values():
            # Sum the temporary value and save it as a value_key
            sum_value = 0
            for k, v in grid.data_single.items():
                if k in value_names:
                    sum_value += grid.data_single[k]
            grid.data_single[value_key] = sum_value

            # Delete key after giving it to sum
            for k in value_names:
                if k in grid.data_single.keys():
                    del grid.data_single[k]

    @staticmethod
    def _decay(current_value: float, decay_factors: str):
        # Calculate the new value for the next step
        if "*" in decay_factors:
            decay = float(decay_factors.replace("*", ''))
            next_value = current_value * decay
        elif "-" in decay_factors:
            decay = float(decay_factors.replace("-", ''))
            next_value = current_value - decay
        else:
            decay = float(decay_factors)
            next_value = current_value + decay
        return next_value

    def _single_trickle_down_bfs(self,
                                 starting: GridElement,
                                 steps: int,
                                 value_key: str,
                                 value: float,
                                 decay_factors: str):
        """
        Use Breadth to assign value based on the shortest distance from the starting point.
            BFS explores all the neighbors at the current depth (distance)
            before moving to the next level.
        :param starting: Starting point of the trickle down of an impact
        :param steps: How many steps to trickle down
        :param value_key: Key to be set inside GridElement's `data_single` dictionary
        :param value: Value to be set inside GridElement's `data_single` dictionary under key `key`
        :param decay_factors: should be string in order to make different calculation
            1. *<number>: value * decay number(float)
            2. -<number>: value - decay number(float)
            3. (else): value + decay number(float)
        :return:
        """
        visited = dict()
        queue = deque([(starting, steps, value)])

        while queue:
            current_element, current_steps, current_value = queue.popleft()

            # Skip if already visited with fewer steps
            already_visited = current_element.index in visited
            visited_fewer_steps = (
                    current_element.index in visited and
                    visited[current_element.index] <= current_steps
            )
            if already_visited or visited_fewer_steps:
                continue

            # Update the GridElement's process and mark as visited
            current_element.set_data_value(value_key, current_value)
            visited[current_element.index] = current_steps

            # Calculate the new value for the ext step
            next_value = self._decay(current_value, decay_factors)

            # Add the neighbors to the queue with reduced steps
            if current_steps > 0:
                for neighbor in [current_element.north,
                                 current_element.south,
                                 current_element.east,
                                 current_element.west,
                                 current_element.northeast,
                                 current_element.northwest,
                                 current_element.southeast,
                                 current_element.southwest]:
                    if neighbor is not None:
                        queue.append((neighbor, current_steps - 1, next_value))

    def grid_dataframe(self, target: str) -> pd.DataFrame:
        """
        If `target` key is inside the grid map's GridElement's data_single dictionary
            display it as a dataframe.
        You can easily check the corresponding Grid's process.
        :param target: key for dictionary `data_single`
        :return: pandas dataframe
        """
        result = list()
        for i in range(self.n):
            rows = list()
            for j in range(self.m):
                grid_index = i * self.m + j
                grid_data = self.grid_element_map[grid_index].data_single

                if target in grid_data.keys():
                    rows.append(grid_data[target])
                else:
                    rows.append(np.nan)
            result.append(rows)

        return pd.DataFrame(result)

    def kepler_dataframe(self, targets: [str], save: bool = True) -> pd.DataFrame:
        result = list()
        col = ['grid_index', *targets, 'lon', 'lat']
        for k, v in self.grid_element_map.items():
            row = [k, *[v.data_single[tgt] for tgt in targets], *v.center.coordinate]
            result.append(row)

        result = pd.DataFrame(result, columns=col)
        if save:
            filename = f"/Users/goonzard/Developer/portfolio-realestate/generate/{self.grid_name}.csv"
            result.to_csv(filename)
        return result


def grid_matching_point(grid: Grid, data: pd.DataFrame, lon_lat_col_name: (str, str), verbose: bool = False):
    lon_col, lat_col = lon_lat_col_name
    assert lon_col in data.columns
    assert lat_col in data.columns

    # Return only the grid - matched process points
    data_np = data.to_numpy()

    result = list()
    for i, (lon, lat) in enumerate(zip(data[lon_lat_col_name[0]], data[lon_lat_col_name[1]])):
        if verbose:
            print(f"matching grid for {data_np[i][0]}", flush=True)

        for ge in grid.grid_element_map.values():
            if ge.has(lon, lat):
                result.append([ge.index, *data_np[i]])
                break  # one coordinate can only match one grid (not intersecting)

    return pd.DataFrame(result, columns=['grid_index', *data.columns])


def grid_matching_line(grid: Grid, data: pd.DataFrame, line_segs_col_name: str, verbose: bool = False):
    assert line_segs_col_name in data.columns

    # Return only the grid - matched line. Drop the line
    cols_no_line = data.columns.tolist()
    cols_no_line.remove(line_segs_col_name)
    data_np = data[cols_no_line].to_numpy()

    result = list()
    for i, line_segs in enumerate(data[line_segs_col_name]):
        if verbose:
            print(f"matching grid for {data_np[i][0]}", flush=True)

        # Multiple line in line_segs
        # If one of the line is matched, save the grid
        # There can be multiple grids matched, so the returning dataframe might be bumped up
        for line in line_segs:
            for ge in grid.grid_element_map.values():
                if ge.pass_through(line):
                    result.append([ge.index, *data_np[i]])

    return pd.DataFrame(result, columns=['grid_index', *cols_no_line])
