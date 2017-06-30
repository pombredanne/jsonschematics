import json

from six import iteritems

from schematics.types.base import (BaseType, NumberType, IntType, LongType, FloatType,
                                   DecimalType, BooleanType)
from schematics.types.compound import ModelType, ListType

from collections import OrderedDict

__version__ = '1.0'


SCHEMATIC_TYPE_TO_JSON_TYPE = {
    'NumberType': 'number',
    'IntType': 'integer',
    'LongType': 'integer',
    'FloatType': 'number',
    'DecimalType': 'number',
    'BooleanType': 'boolean',
    'BaseType': 'object'
}

# Schema Serialization

# Parameters for serialization to JSONSchema
schema_kwargs_to_schematics = {
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'pattern': 'regex',
    'minimum': 'min_value',
    'maximum': 'max_value',
    'enum': 'choices'
}


def jsonschema_for_single_field(field_instance):
    field_schema = OrderedDict()

    if hasattr(field_instance, 'metadata'):
        field_schema["title"] = field_instance.metadata.get('label', '')
        field_schema["description"] = field_instance.metadata.get('description', '')

    field_schema["type"] = SCHEMATIC_TYPE_TO_JSON_TYPE.get(field_instance.__class__.__name__, 'string')

    for js_key, schematic_key in iteritems(schema_kwargs_to_schematics):
        value = getattr(field_instance, schematic_key, None)
        if value is not None:
            field_schema[js_key] = value

    return field_schema


def jsonschema_for_fields(model):
    properties = {}
    required = []
    for field_name, field_instance in iteritems(model.fields):
        serialized_name = getattr(field_instance, 'serialized_name', None) or field_name

        if isinstance(field_instance, ModelType):
            node = jsonschema_for_model(field_instance.model_class)

        elif isinstance(field_instance, ListType):
            try:
                node = jsonschema_for_model(field_instance.model_class, 'array')
            except AttributeError:
                field_schema = jsonschema_for_single_field(field_instance.field)
                node = OrderedDict([
                    ('type', 'array'),
                    ('items', field_schema)
                ])

        # Convert field as single model
        elif isinstance(field_instance, BaseType):
            node = jsonschema_for_single_field(field_instance)

        if getattr(field_instance, 'required', False):
            required.append(serialized_name)
            properties[serialized_name] = node
        else:
            properties[serialized_name] = {
                "oneOf": [
                    {'type': 'null'},
                    node
                ]
            }

    return properties, required


def jsonschema_for_model(model, _type='object'):

    properties, required = jsonschema_for_fields(model)

    if hasattr(model, 'metadata'):
        schema_title = model.metadata.get('label', '')
        schema_description = model.metadata.get('description', '')
    else:
        schema_title = ''
        schema_description = ''

    schema = OrderedDict([
        ('title', schema_title),
        ('description', schema_description),
        ('type', 'object'),
    ])

    if required:
        schema['required'] = required

    if hasattr(model, '_schema_order'):
        ordered_properties = [(i, properties.pop(i)) for i in model._schema_order]
        schema['properties'] = OrderedDict(ordered_properties)
    else:
        schema['properties'] = properties

    if _type == 'array':
        schema = OrderedDict([
            ('type', 'array'),
            ('items', schema),
        ])

    return schema


def to_jsonschema(model, **kwargs):
    """Returns a representation of this schema class as a JSON schema."""
    schema_id = kwargs.pop('schema_id', '')
    jsonschema = OrderedDict([
        ('$schema', 'http://json-schema.org/draft-04/schema#'),
        ('id', schema_id)
    ])
    jsonschema.update(jsonschema_for_model(model))
    return jsonschema
