import unittest
from convert_coordinates import convert_coordinates, setup_transformers

class TestConvertCoordinates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transformers = setup_transformers()

    def test_utm_conversion(self):
        # Test a known UTM Zone 14N coordinate
        # Northing: 3541269.28, Easting: 779101.86 -> Lat: 31.973137, Lon: -96.046585
        northing = 3541269.28
        easting = 779101.86
        lat, lon = convert_coordinates(northing, easting, self.transformers)

        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        self.assertAlmostEqual(lat, 31.973137, places=4)
        self.assertAlmostEqual(lon, -96.046585, places=4)

    def test_invalid_range_skipped(self):
        # Test coordinates outside valid ranges
        # Northing: 1000000 (Too low for UTM/SP), Easting: 500000
        northing = 1000000
        easting = 500000
        lat, lon = convert_coordinates(northing, easting, self.transformers)

        self.assertIsNone(lat)
        self.assertIsNone(lon)

    def test_state_plane_ft_detection(self):
        # Test a theoretical State Plane coordinate (approximate)
        # NAD83 Texas North Central (ftUS)
        # Origin (31.66N, 98.5W) -> Northing ~2,000,000m (6.5M ft), Easting ~600,000m (2M ft)
        # Let's try Northing 7,000,000 ft, Easting 2,000,000 ft
        northing = 7000000
        easting = 2000000
        lat, lon = convert_coordinates(northing, easting, self.transformers)

        # Should be detected and converted
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        # Should be within Texas bounds (roughly 25-37N, -107 to -93W)
        self.assertTrue(31 < lat < 34)
        self.assertTrue(-99 < lon < -97)

if __name__ == '__main__':
    unittest.main()
