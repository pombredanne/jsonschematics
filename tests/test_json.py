import json
import unittest

from schematics.models import Model
from schematics.types import StringType, URLType, IntType, LongType, DecimalType
from schematics.types.compound import ModelType, ListType

from jsonschematics import to_jsonschema


class BankAccount(Model):
    """An Account in A Bank"""
    account_id = LongType(required=True, min_value=0)
    amount = DecimalType()


class BirthPlace(Model):
    """The location of a Person's birth"""
    name = StringType(required=True, min_length=1, max_length=30)
    planet = StringType(default='Earth')


class Person(Model):
    """A human being"""
    name = StringType(required=True)
    website = URLType()
    age = IntType()
    birth_place = ModelType(BirthPlace)
    bank_accounts = ListType(ModelType(BankAccount))
    guitar_preference = StringType(choices=['stratocaster', 'telecaster', 'gretsch'])


test_data = {
    'name': u'Joe Strummer',
    'website': 'http://soundcloud.com/joestrummer',
    'age': 15,
    'birth_place': {
        'name': 'Somewhere, World'
    },
    'bank_accounts': [{
        'account_id': long(123),
        'amount': 10.23,
    }, {
        'account_id': long(456),
        'amount': 100.54,
    }],
    'guitar_preference': 'telecaster'
}

converted_schema_string = '{"description": "A human being", "properties": {"age": {"type": "integer"}, "bank_accounts": {"items": {"description": "An Account in A Bank", "properties": {"account_id": {"minimum": 0, "type": "integer"}, "amount": {"type": "number"}}, "required": ["account_id"], "title": "BankAccount", "type": "object"}, "title": "BankAccount Set", "type": "array"}, "birth_place": {"description": "The location of a Person\'s birth", "properties": {"name": {"maxLength": 30, "minLength": 1, "type": "string"}, "planet": {"default": "Earth", "type": "string"}}, "required": ["name"], "title": "BirthPlace", "type": "object"}, "guitar_preference": {"enum": ["stratocaster", "telecaster", "gretsch"], "type": "string"}, "name": {"type": "string"}, "website": {"type": "string"}}, "required": ["name"], "title": "Person", "type": "object"}'

class TestModelFunctions(unittest.TestCase):

    def test_schema_serialization(self):
        val = to_jsonschema(Person, sort_keys=True)
        self.assertEquals(val, converted_schema_string)

    def test_validation_schema_validation(self):
        from jsonschema import validate

        person = Person(test_data)

        try:
            person.validate()
        except:
            self.fail("person.validate() raised Exception unexpectedly!")

        try:
            validate(test_data, json.loads(converted_schema_string))
        except:
            self.fail("jsonschema.validate() raised Exception unexpectedly!")
