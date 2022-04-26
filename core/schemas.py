from typing import List, Dict, Optional, Union, Any, OrderedDict
from enum import Enum
from pydantic import BaseModel, Field, create_model
from datetime import datetime
from fastapi import HTTPException

import numpy as np
import pandas as pd

from pyshop import ShopSession
from pyshop.shopcore.shop_api import get_attribute_info
from pyshop.helpers.timeseries import remove_consecutive_duplicates

from .sessions import SessionManager

# this dummy user and session is used to dynamically get enums and other metadata from a live ShopSession
# TODO: make this cleaner, ... wrap in some init construct or something.
dummy_user = '__dummy_user__'
SessionManager.add_user_session('__dummy_user__', None)
SessionManager.add_shop_session(dummy_user, 'default_session')
_shop_session = SessionManager.get_shop_session(dummy_user, 1)

class StrEnum(str, Enum):
    pass

# Auth schemas

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

_SHOP_OBJECT_TYPE_NAMES = _shop_session.model._all_types
_SHOP_RELATION_TYPES = [
    _shop_session.shop_api.GetValidRelationTypes(object_type)
    for object_type in _SHOP_OBJECT_TYPE_NAMES
] # flattens
_SHOP_RELATION_TYPES = [e for sub in _SHOP_RELATION_TYPES for e in sub ]
_SHOP_COMMANDS = _shop_session._commands

ApiCommandEnum = StrEnum(
    'ApiCommandEnum',
    names={
        name: name for name in filter(lambda x : x[0] != '_', _shop_session.shop_api.__dir__())
    }
)

# here we simply make sure start* commands come first in the enum giving the SwaggerUI better default
_ordered_shop_commands = [ c for c in _SHOP_COMMANDS.keys() if c[0:5] == 'start']
_ordered_shop_commands += [ c for c in _SHOP_COMMANDS.keys() if c[0:8] == 'set_code']
_ordered_shop_commands += list(_SHOP_COMMANDS.keys()) # adding all of the rest is ok, repeats are automatically ignored by enum

ShopCommandEnum = StrEnum(
    'ShopCommandEnum',
    names={ name:name for name in _ordered_shop_commands}
)

ObjectTypeEnum = StrEnum(
    'ObjectTypeEnum',
    names={
        name: name for name in _SHOP_OBJECT_TYPE_NAMES
    }
)

RelationTypeEnum = StrEnum(
    'RelationTypeEnum',
    names={
        name: name for name in (['default', 'bypass', 'spill'])
    }
)

RelationDirectionEnum = StrEnum(
    'RelationDirectionEnum',
    names={name: name for name in ['both', 'input', 'output']}
)

# Session

class Session(BaseModel):
    session_id: Optional[int] = Field(1, description='unique session identifier per user session')
    session_name: Optional[str] = Field('unnamed', description='name of session')
    log_file: Optional[str] = Field('pyshop_log.py', description='name of pyshop logfile')

# Commands

class Commands(BaseModel):
    commands: List[str] = Field(description="list of commands")

class CommandStatus(BaseModel):
    message: str
    status: bool
    error: Optional[str] = None

class ApiCommands(BaseModel):
    command_types: List[str] = None
    
class ApiCommandArgs(BaseModel):
    args: tuple
    kwargs: dict

class ApiCommandDescription(BaseModel):
    description: str


# Pandas like schemas

class Series(BaseModel):

    name: Optional[str] = None
    index: List[datetime]
    values: List[float]

def array_to_list_str(array: np.array) -> List[str]:
    
    # convert pandas series and index object to array
    if isinstance(array, pd.Series) or isinstance(array, pd.Index):
        array = array.values
    
    # convert timestamps to ISO timestamps
    if type(array[0]) == np.datetime64 or type(array[0]) == pd.Timestamp:
        list(pd.to_datetime(array).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    
    # convert numpy array to list
    return list(array.astype(str))

    
def Series_from_pd(series: pd.Series) -> Series:

    if series is None or len(series) == 0:
        return None

    return Series(
        name = series.name,
        index = list(series.index),
        values = list(series.values)
    )

class DataFrame(BaseModel):

    name: Optional[str] = None
    columns: Dict[str, List[str]]
    dataframe_index: List[str]

def DataFrame_from_pd(data_frame: pd.DataFrame) -> DataFrame:
    
    if data_frame is None or len(data_frame) == 0:
        return None

    columns = {
        c_name: array_to_list_str(data_frame[c_name]) for c_name in data_frame.columns
    }

    return DataFrame(
        name = data_frame[data_frame.columns[0]].name,
        columns = columns,
        data_frame_index = array_to_list_str(data_frame.index),
    )


# ----------------- Primitive data types

class TimeSeries(BaseModel):
    name: Optional[str] = Field(None, description="name of the series")
    unit: Optional[str] = Field('NOK', description='unit of time series values')
    # values: Dict[datetime, List[float]] = Field({}, description='values')
    timestamps: List[datetime]
    values: List[List[float]]

def TimeSeries_from_pd(series: pd.Series) -> TimeSeries:

    if series is None or len(series) == 0:
        return None

    return TimeSeries(
        name = series.name,
        timestamps = list(series.index),
        values = [list(series.values)]
    )

class Curve(BaseModel):
    x_unit: Optional[str] = Field('MW', description='unit of x_values')
    y_unit: Optional[str] = Field('%', description='unit of y_values')
    x_values: List[float]
    y_values: List[float]

#
# Notice
# - xy             <-> Curve 
# - xy_array, xyn  <-> OrderedDict[float, Curve]
# - xyt            <-> OrderedDict[datetime, Curve]
# - txy, #ttxy     <-> TimeSeries
#

class ObjectAttributeTypeEnum(str, Enum):
    boolean = 'boolean'
    integer = 'integer'
    float = 'float'
    string = 'string'
    datetime = 'datetime'
    float_array = 'float_array',
    integer_array = 'integer_array',
    string_array = 'string_array';
    Curve = 'Curve'
    MapFloatCurve = 'OrderedDict[float, Curve]'
    MapTimeCurve = 'OrderedDict[datetime, Curve]'
    TimeSeries = 'TimeSeries'


def new_attribute_type_name_from_old(name: str) -> ObjectAttributeTypeEnum:
    
    conversion_map = {
        'bool': ObjectAttributeTypeEnum.boolean,
        'int': ObjectAttributeTypeEnum.integer,
        'double': ObjectAttributeTypeEnum.float,
        'str': ObjectAttributeTypeEnum.string,
        'string': ObjectAttributeTypeEnum.string,
        'double_array': ObjectAttributeTypeEnum.float_array,
        'int_array': ObjectAttributeTypeEnum.integer_array,
        'string_array': ObjectAttributeTypeEnum.string_array,
        'xy': ObjectAttributeTypeEnum.Curve,
        'xy_array': ObjectAttributeTypeEnum.MapFloatCurve,
        'xyn': ObjectAttributeTypeEnum.MapFloatCurve,
        'xyt': ObjectAttributeTypeEnum.MapTimeCurve,
        'txy': ObjectAttributeTypeEnum.TimeSeries,
    }

    if name in conversion_map:
        return conversion_map[name]
    else:
        raise HTTPException(500, f'name {{{name}}} not in understood type_name list ... needs to be handled ...')
    return name
    

AttributeValue = Union[None, float, str, List[float], List[str], Curve, OrderedDict[float, Curve], OrderedDict[datetime, Curve], TimeSeries]

class ObjectAttribute(BaseModel):
    attribute_name: str
    attribute_type: ObjectAttributeTypeEnum
    is_input: Optional[bool]
    is_output: Optional[bool]
    legacy_datatype: Optional[str]
    x_unit: Optional[str]
    y_unit: Optional[str]
    license_name: Optional[str]
    full_name: Optional[str]
    data_func_name: Optional[str]
    description: Optional[str]
    documentation_url: Optional[str]
    example_url_prefix: Optional[str]
    example: Optional[str]


class ObjectInstance(BaseModel):
    # object_name: str = Field('example_res', description='name of instance')
    # object_type: str = Field('reservoir', description='type of instance')
    attributes: Dict[str, AttributeValue] = Field({}, description='attributes that can be set on the given object_type')

class ObjectTypeInstance(BaseModel):
    object_type: str
    instances: Dict[str, ObjectInstance]

class ObjectType(BaseModel):
    object_type: str = Field(description='name of the object_type')
    # instances: Optional[Dict[str, ObjectInstance]] = Field(description='list of instances of this type')
    instances: List[str] = Field(description='list of instances of this type')
    attributes: Optional[Dict[str, Union[ObjectAttributeTypeEnum, ObjectAttribute]]]  \
        = Field(description='attributes that can be set on the given object_type')

# Connection

# class ObjectID(BaseModel):
#     object_type: str
#     object_name: str

# class Connection(BaseModel):
#     from_object: ObjectID
#     to_object: ObjectID
#     relation_type: RelationTypeEnum = Field(RelationTypeEnum.default, desription="relation type")
#     relation_direction: RelationDirectionEnum = RelationDirectionEnum.both

class Connection(BaseModel):
    from_: str = Field(alias='from')
    from_type: str
    to: str
    to_type: str
    relation_type: RelationTypeEnum = Field(RelationTypeEnum.default, description="relation type")
    relation_direction: RelationDirectionEnum = RelationDirectionEnum.both
    class Config:
        allow_population_by_field_name = True

# Model

class ModelOld(BaseModel):
    object_types: List = Field(description='List of all object types and their corresponding object instances.')

ObjectModel = {
    o: create_model(
        f'ObjectModel{o}',
        **{a: (AttributeValue, None) for a in _shop_session.shop_api.GetObjectTypeAttributeNames(o)}
    ) for o in _SHOP_OBJECT_TYPE_NAMES
}

class TimeResolution(BaseModel):
    start_time: datetime = Field(description="optimization start time")
    end_time: datetime = Field(description="optimization end time")
    time_unit: str = Field('hour', description="optimization time unit")
    time_resolution: Optional[TimeSeries] = None

ObjectTypeModel = create_model(
    'ObjectTypeModel',
    **{o: (Dict[str, ObjectModel[o]], None) for o in _SHOP_OBJECT_TYPE_NAMES}
)

class Command(BaseModel):
    command: str
    options: List[str]
    values: List[str]

class ShopModel(BaseModel):
    time: Optional[TimeResolution]
    model: Optional[ObjectTypeModel]
    connections: Optional[List[Connection]]
    commands: Optional[List[Command]]


# Logging

class LoggingEndpoint(BaseModel):
    endpoint: str
    
def serialize_model_object_attribute(shop_session: ShopSession, object_type: str, object_name: str, attribute_name: str, compressTxy: bool) -> AttributeValue:

    # attribute_type = new_attribute_type_name_from_old(attribute.info()['datatype'])
    attribute_type = new_attribute_type_name_from_old(attribute_map[object_type][attribute_name]['datatype'])
    # attribute_name = attribute._attr_name
    info = attribute_map[object_type][attribute_name]

    attribute_y_unit = info['yUnit'] if 'yUnit' in info else 'unknown'
    attribute_x_unit = info['xUnit'] if 'xUnit' in info else 'unknown'

    value = shop_session.model[object_type][object_name][attribute_name].get()

    if value is None:
        return None

    if attribute_type == ObjectAttributeTypeEnum.boolean:
        return bool(value)

    if attribute_type == ObjectAttributeTypeEnum.integer:
        return int(value)

    if attribute_type == ObjectAttributeTypeEnum.float:
        return float(value)

    if attribute_type == ObjectAttributeTypeEnum.string:
        return str(value)

    if attribute_type == ObjectAttributeTypeEnum.datetime:
        return str(value)

    if attribute_type == ObjectAttributeTypeEnum.float_array:
        return np.array(value, dtype=float).tolist()

    if attribute_type == ObjectAttributeTypeEnum.integer_array:
        return np.array(value, dtype=int).tolist()

    if attribute_type == ObjectAttributeTypeEnum.string_array:
        return np.array(value, dtype=str).tolist()

    if attribute_type == ObjectAttributeTypeEnum.TimeSeries:

        if isinstance(value, pd.Series) or isinstance(value, pd.DataFrame):
            if compressTxy:
                value = remove_consecutive_duplicates(value)
            if isinstance(value, pd.Series):
                # values = {t: [v] for t, v in zip(value.index.values, value.values)}
                timestamps = value.index.values.tolist()
                values = value.values.reshape(1, value.values.size).tolist()

            if isinstance(value, pd.DataFrame):
                # values = {t: v for t, v in zip(value.index.values, value.values.tolist())}
                timestamps = value.index.value.tolist()
                values = value.values.transpose().tolist()

            return TimeSeries(
                name = value.name,
                unit = attribute_y_unit,
                timestamps = timestamps,
                values = values
            )

    if attribute_type == ObjectAttributeTypeEnum.Curve:

        if isinstance(value, pd.Series):
            return Curve(
                x_unit = attribute_x_unit,
                y_unit = attribute_y_unit,
                x_values = value.index.values.tolist(),
                y_values = value.values.tolist()
            )

    if attribute_type == ObjectAttributeTypeEnum.MapTimeCurve:
        return f'{attribute_type}: {type(value)}'

    if attribute_type == ObjectAttributeTypeEnum.MapFloatCurve:

        if type(value) == list and isinstance(value[0], pd.Series):

            return { ser.name: # reference value is stored in series.name
                Curve(
                    x_unit = attribute_x_unit,
                    y_unit = attribute_y_unit,
                    x_values = ser.index.values.tolist(),
                    y_values = ser.values.tolist()
                ) for ser in value
            }

    raise HTTPException(500, f"{attribute_type}: cannot parse <{type(value)}>")


def serialize_model_object_instance(shop_session: ShopSession, object_type: str, object_name: str) -> ObjectInstance:

    # attribute_names = list(o._attr_names)

    return ObjectInstance(
        # object_type = o.get_type(),
        # object_name = o.get_name(),
        attributes = {
            attribute_name: serialize_model_object_attribute(shop_session, object_type, object_name, attribute_name, False) for attribute_name in attribute_map[object_type]
        }
    )

class CommandArguments(BaseModel):
    options: List[str] = []
    values: List[str] = []

attribute_map = dict()
for ot in _SHOP_OBJECT_TYPE_NAMES:
    attribute_map[ot] = dict()
    for at in _shop_session.shop_api.GetObjectTypeAttributeNames(ot):
        attribute_map[ot][at] = get_attribute_info(_shop_session.shop_api, ot, at)
