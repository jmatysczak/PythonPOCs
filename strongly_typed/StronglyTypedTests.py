# Run all tests in module with:
# python -m unittest discover . *Tests.py

from datetime import datetime
import unittest


class StronglyTypedTests(unittest.TestCase):
    def test_that_dynamic_properties_can_not_be_set(self):
        model = MockModel()
        with self.assertRaises(AttributeError):
            model.someDynamicProperty = 'some value'

    def test_that_two_instances_can_be_created(self):
        model1 = MockModel()
        model1.string_field = 'Model 1'
        self.assertEqual(model1.string_field, 'Model 1')

        model2 = MockModel()
        model2.string_field = 'Model 2'
        self.assertEqual(model2.string_field, 'Model 2')

    def test_that_the_int_field_can_be_set_and_gotten_only_as_a_string(self):
        model = MockModel()

        model.int_field = 1
        self.assertEqual(model.int_field, 1)

        with self.assertRaises(TypeError):
            model.int_field = 'Not an int'

    def test_that_the_string_field_can_be_set_and_gotten_only_as_a_string(self):
        model = MockModel()

        model.string_field = 'A string value'
        self.assertEqual(model.string_field, 'A string value')

        with self.assertRaises(TypeError):
            model.string_field = 1

    def test_that_the_datetime_field_can_be_set_and_gotten_only_as_a_datetime(self):
        model = MockModel()

        a_datetime = datetime.now()

        model.datetime_field = a_datetime
        self.assertEqual(model.datetime_field, a_datetime)

        with self.assertRaises(TypeError):
            model.datetime_field = 'Not a datetime'


from Freezeable import Freezeable
from typed_property import typed_property


class MockModel(Freezeable):
    def __init__(self):
        self.__int_field = None
        self.__string_field = None
        self.__datetime_field = None
        self._freeze()

    @property
    def int_field(self):
        return self.__int_field

    @int_field.setter
    @typed_property(int)
    def int_field(self, int_field):
        self.__int_field = int_field

    @property
    def string_field(self):
        return self.__string_field

    @string_field.setter
    @typed_property(basestring)
    def string_field(self, string_field):
        self.__string_field = string_field

    @property
    def datetime_field(self):
        return self.__datetime_field

    @datetime_field.setter
    @typed_property(datetime)
    def datetime_field(self, datetime_field):
        self.__datetime_field = datetime_field


if __name__ == '__main__':
    unittest.main()
