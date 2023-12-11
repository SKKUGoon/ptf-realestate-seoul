import geopandas as gpd

from process.loader import Loader


class SeoulCityMapper:
    """
    Match
        seoul location process with coordinate (standard)
        nps process with partial address (comparison)

    +proj=tmerc: Specifies the Transverse Mercator projection.
    +ellps=bessel: Uses the Bessel ellipsoid.
    +lon_0=15: The central meridian (replace 15 with your value).
    +k=1: Scale factor (usually 1 for most applications).
    +x_0=0 and +y_0=0: False easting and northing (set to 0 if not applicable).
    +datum=WGS84: Even though you're using the Bessel ellipsoid, this sets the datum transformation method to WGS84, which can be adjusted if needed.
    +units=m: Units of the coordinate system, usually meters.
    +no_defs: Prevents the use of default parameters.
    """
    def __init__(self):
        # Load standard process - coordinate process (polygon process)
        loader = Loader()
        loader.set_path("./asset/location/seoul_shape")
        self.data = gpd.read_file(
            loader.data_filename_seoulshape_location(),
            encoding='cp949'
        )

        # Coordinate system projection. Bessel/central -> WGS84
        self.data = self.data.to_crs(epsg=5174)  # Default is wgs84, Read as bessel
        self.data = self.data.to_crs(epsg=4326)  # Convert to wgs84

        # Add central point
        self.data['centroid'] = self.data['geometry'].centroid


if __name__ == "__main__":
    scm = SeoulCityMapper()
