import datetime
import unittest

from nativedb.nativeserializer import Serializer


class TestSerializer(unittest.TestCase):
    def test_serialize(self):
        serializer = Serializer()
        self.assertEqual('2021-12-25', serializer.serialize(datetime.date(2021, 12, 25)))
        self.assertEqual(datetime.date(2021, 12, 25), serializer.deserialize(datetime.date, '2021-12-25'))
