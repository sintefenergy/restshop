import json

from datetime import datetime
from typing import Optional, List

from fastapi import Depends, FastAPI, HTTPException, Body, Query, Response, Header

from pydantic import BaseModel, Field

# from fastapi.openapi.models import SchemaBase
from starlette.responses import RedirectResponse

import core
from core.sessions import SessionManager
from core.schemas import ShopCommandEnum, ObjectTypeEnum, OrderedDict, RelationDirectionEnum, RelationTypeEnum, ApiCommandEnum, \
        Session, CommandStatus, ApiCommands, ApiCommandArgs, ApiCommandDescription, Series, Model, ObjectType, ObjectAttribute, \
        ObjectInstance, TimeSeries, Curve, Connection, CommandArguments, LoggingEndpoint, ObjectID, \
        Series_from_pd, new_attribute_type_name_from_old, serialize_model_object_instance

from pyshop.shopcore.shop_rest import NumpyArrayEncoder

import pandas as pd
import numpy as np

import requests

def shop_session(user_name: str, session_id: str):
    return SessionManager.get_shop_session(user_name, session_id)

api_description = """ """


app = FastAPI(
    title="REST SHOP",
    description=api_description,
    version=core.__version__,
    openapi_tags=[
        {
            'name': 'Authentication',
            'description': 'Not required during development - Used to authenticate user.',
        },
        {
            'name': 'Session',
            'description': 'All model objects and operations are tied to a Session'
        },
        {
            'name': 'Time Resolution',
            'description': 'Specify the time resolution for the optimization problem',
        },
        {
            'name': 'Model',
            'description': 'The model of a given Session. Use this endpoint to create, read, update, destroy model objects',
        },
        {
            'name': 'Connections',
            'description': 'Configure connections between model objects',
        },
        {
            'name': 'Simulation',
            'description': 'Interact with the simulation using SHOP commands',
        },
        {
            'name': 'Logging',
            'description': 'Configure logging',
        },
        {
            'name': 'Topology',
            'description': 'Get model topology as graphviz filestring',
        }
    ]
)

def http_raise_internal(msg: str, e: Exception):
    raise HTTPException(500, f'{msg} -- Internal Exception: {e}')

def get_session_id(session_id: int = Header(1)) -> int:
    return session_id

def check_that_time_resolution_is_set(session_id: int = Depends(get_session_id)):
    session = SessionManager.get_user_session(test_user)
    is_set = session.shop_sessions_time_resolution_is_set[session_id]
    if is_set == False:
        # In case time resolutions has been set through internal, check again
        try:
            session.shop_sessions[session_id].get_time_resolution()
            session.shop_sessions_time_resolution_is_set[session_id] = True
        except:
            raise HTTPException(400, 'First you must set the time_resolution of the session')
    

test_user = 'test_user'
SessionManager.add_user_session('test_user', None)
# SessionManager.add_shop_session(test_user, 'default_session') # Create default session at startup of rest API


# so that the first thing the client sees is /docs
@app.get("/", include_in_schema=False)
async def root_documentation():
    return RedirectResponse("/docs")

# ------- session

@app.post("/session", tags=['Session'])
async def create_session(s: Session = Body(Session(session_name='unnamed'), example={'session_name': 'unnamed', 'log_file': ''})):
    shop = SessionManager.add_shop_session(test_user, session_name=s.session_name, log_file=s.log_file)
    return Session(session_id = shop._id, session_name=shop._name, log_file=shop._log_file)

@app.get("/sessions", response_model=List[Session], tags=['Session'])
async def get_sessions():
    return [
        Session(
            session_id = s._id,
            session_name = s._name,
            log_file = s._log_file
        ) for _, s in SessionManager.get_shop_sessions(test_user).items()
    ]


@app.get("/session", response_model=Session, tags=['Session'])
async def get_session(session_id: int = Query(1)):
    if session_id in SessionManager.get_shop_sessions(test_user):
        s = shop_session(test_user, session_id)
        return Session(session_id = s._id, session_name = s._name)
    else:
        raise HTTPException(404, f'Session with id {{{session_id}}} not found')

@app.delete("/session", tags=['Session'])
async def delete_session(session_id: int = Query(1)):
    if session_id in SessionManager.get_shop_sessions(test_user):
        if(SessionManager.remove_shop_session(test_user, session_id)):
            return None
        else:
            raise HTTPException(404, f'Could not delete session with id {{{session_id}}}')
    else:
        HTTPException(404, f'Session with id {{{session_id}}} not found')

# --------- time_resolution

class TimeResolution(BaseModel):
    start_time: datetime = Field(description="optimization start time")
    end_time: datetime = Field(description="optimization end time")
    time_unit: str = Field('hour', description="optimization time unit")
    time_resolution: Optional[Series] = None


@app.put("/time_resolution", tags=["Time Resolution"])
async def set_time_resolution(
    time_resolution: TimeResolution = Body(
        ...,
        example={
            "start_time": "2021-05-02T00:00:00.00Z",
            "end_time": "2021-05-03T00:00:00.00Z",
            "time_unit": "hour"
        }
    ),
    session_id = Depends(get_session_id)):

    # validate
    start = pd.Timestamp(time_resolution.start_time)
    end = pd.Timestamp(time_resolution.end_time)

    if (end <= start):
        raise HTTPException(400, 'end_time must be strictly greater than start_time')

    if (time_resolution.time_resolution):
        tr: Series = time_resolution.time_resolution
        shop_session(test_user, session_id).set_time_resolution(
            starttime=start,
            endtime=end,
            timeunit=time_resolution.time_unit,
            timeresolution=pd.Series(index=tr.index, data=tr.values)
        )
    else:
        shop_session(test_user, session_id).set_time_resolution(
            starttime=start,
            endtime=end,
            timeunit=time_resolution.time_unit
        )


    # store the fact that time_resolution has been set
    us = SessionManager.get_user_session(test_user)
    us.shop_sessions_time_resolution_is_set[session_id] = True
    return None


@app.get("/time_resolution", response_model=TimeResolution, dependencies=[Depends(check_that_time_resolution_is_set)], tags=["Time Resolution"])
async def get_time_resolution(session_id = Depends(get_session_id)):

    try:
        tr = shop_session(test_user, session_id).get_time_resolution()
    except HTTPException as e:
        raise e
    except Exception as e:
        http_raise_internal(    "Something whent wrong, maybe time_resolution has not been set yet", e)

    return TimeResolution(
        start_time=tr['starttime'],
        end_time=tr['endtime'],
        time_unit=tr['timeunit'],
        time_resolution=Series_from_pd(tr['timeresolution'])
    )

# ------ model

@app.get("/model", response_model=Model, response_model_exclude_unset=True, tags=['Model'])
async def get_model_object_types(session_id = Depends(get_session_id)):
    types = list(shop_session(test_user, session_id).model._all_types)
    return Model(object_types = types)

# ------ object_type

@app.get("/model/{object_type}/information", response_model=ObjectType, response_model_exclude_unset=True, tags=['Model'])
async def get_model_object_type_information(
    object_type: ObjectTypeEnum,
    attribute_filter: str = Query('*', description='filter attributes by regex'),
    verbose: bool = Query(False, description='toggles additional attribute information, e.g is_input, is_output, etc ...'),
    session_id = Depends(get_session_id)
):

    if attribute_filter != '*':
        raise HTTPException(500, 'setting attribute_filter != * is not support yet')

    ot = SessionManager.get_model_object_generator(test_user, session_id, object_type)
    instances = list(ot.get_object_names())
    sess = shop_session(test_user, session_id)
    attribute_names: List[str] = list(sess.shop_api.GetObjectTypeAttributeNames(object_type))
    attribute_types: List[str] = list(sess.shop_api.GetObjectTypeAttributeDatatypes(object_type))

    if not verbose:
        attributes = {
            n: new_attribute_type_name_from_old(t)
            for n, t in zip(attribute_names, attribute_types)
        }
    else:

        # TODO: Create this kind of dictionary once at startup, since this might be expensive?
        attr_info = {
            attr_name: {
                info_key: sess.shop_api.GetAttributeInfo(object_type, attr_name, info_key)
                for info_key in sess.shop_api.GetValidAttributeInfoKeys()
            } for attr_name in attribute_names
        }

        attributes = {
            n: ObjectAttribute(
                attribute_name = n,
                attribute_type = new_attribute_type_name_from_old(t),
                is_input = attr_info[n]['isInput'],
                is_output = attr_info[n]['isOutput'],
                legacy_datatype = attr_info[n]['datatype'],
                x_unit = attr_info[n]['xUnit'],
                y_unit = attr_info[n]['yUnit'],
                license_name = attr_info[n]['licenseName'],
                full_name = attr_info[n]['fullName'],
                data_func_name = attr_info[n]['dataFuncName'],
                description = attr_info[n]['description'],
                documentation_url = attr_info[n]['documentationUrl'],
                example_url_prefix = attr_info[n]['exampleUrlPrefix'],
                example = attr_info[n]['example']
            )
            for n, t in zip(attribute_names, attribute_types)
        }

    return ObjectType(
        object_type = object_type,
        instances = instances, 
        attributes = attributes,
    )

# ------ object_name

@app.put("/model/{object_type}",
    response_model=ObjectInstance,
    dependencies=[Depends(check_that_time_resolution_is_set)],
    response_model_exclude_unset=True, tags=['Model'])
async def create_or_modify_existing_model_object_instance(
    object_type: ObjectTypeEnum,
    object_name: str = Query('example_reservoir'),
    object_instance: ObjectInstance = Body(
        None,
        example={
            'attributes': {
                'vol_head': {
                    'x_values': [10.0, 20.0, 30.0],
                    'y_values': [42.0, 43.0, 45.0]
                },
                'water_value_input': {
                    '0.0': {
                        'x_values': [10.0, 9.0, 8.0],
                        'y_values': [42.0, 20.0, 10.0]
                    }
                },
                'inflow': {
                    #'values': {'2020-01-01T00:00:00': [ 42.0 ] }
                    'timestamps': ['2020-01-01T00:00:00Z', '2020-01-01T05:00:00Z' ],
                    'values': [[42.0, 50.0]]
                }
            }
        }
    ),
    session_id = Depends(get_session_id)
    ):
    
    session = shop_session(test_user, session_id)
    try:
        object_generator = session.model[object_type]
    except Exception as e:
        raise HTTPException(500, f'model does not implement object_type {{{object_type}}}') 

    for cmd in session.get_executed_commands():
        print("-----", cmd)
        if 'start sim' in cmd:
            session._sim_has_started = True
            break
    
    if session._sim_has_started:
        raise HTTPException(500, f'simulation has already been started, make a new session first')

    if object_name not in object_generator.get_object_names():
        try:
            object_generator.add_object(object_name)
        except Exception as e:
            raise HTTPException(500, f'object_name {{{object_name}}} is in conflict with existing instance')

    model_object = session.model[object_type][object_name]

    if object_instance and object_instance.attributes:
        for (k,v) in object_instance.attributes.items():

            try:
                datatype = model_object[k].info()['datatype']
            except Exception as e:
                http_raise_internal(f'unknown object_attribute {k} for object_type {object_type}', e)

            if datatype == 'txy':

                # convert scalar values to TimeSeries
                if type(v) == float or type(v) == int:
                    start_time = shop_session(test_user, session_id).get_time_resolution()['starttime']
                    v = TimeSeries(
                        timestamps=[start_time],
                        values=[[v]]
                    )
                try:
                    time_series: TimeSeries = v
                    # index, values = zip(*time_series.values.items())
                    index, values = time_series.timestamps, np.transpose(time_series.values)
                    df = pd.DataFrame(index=index, data=values)
                    model_object[k].set(df)
                except Exception as e:
                    http_raise_internal(f'trouble setting {{{datatype}}} ', e)

            elif datatype == 'xy':
                try:
                    curve: Curve = v
                    ser = pd.Series(index=curve.x_values, data=curve.y_values)
                    model_object[k].set(ser)
                except Exception as e:
                    http_raise_internal(f'trouble setting {{{datatype}}} ', e)

            elif datatype in ['xy_array', 'xyn']:
                try:
                    curves: OrderedDict[float, Curve] = v
                    ser_list = []
                    for ref, curve in curves.items():
                        ser_list += [pd.Series(index=curve.x_values, data=curve.y_values, name=ref)]
                    model_object[k].set(ser_list)
                except Exception as e:
                    http_raise_internal(f'trouble setting {{{datatype}}} ', e)

            elif datatype == 'xyt':
                try:
                    curves: OrderedDict[datetime, Curve] = v
                    ser_list = []
                    for ref, curve in curves.items():
                        ser_list += [pd.Series(index=curve.x_values, data=curve.y_values, name=ref)]
                    model_object[k].set(ser_list)
                except Exception as e:
                    http_raise_internal(f'trouble setting {{{datatype}}} ', e)
                
            elif datatype == 'double':
                model_object[k].set(float(v))

            elif datatype == 'int':
                model_object[k].set(int(v))

            else:
                try:
                    model_object[k].set(v)
                except Exception as e:
                    http_raise_internal(f'trouble setting {{{datatype}}} ', e)

    o = SessionManager.get_model_object_instance(test_user, session_id, object_type, object_name)
    return serialize_model_object_instance(o)

@app.get("/model/{object_type}", response_model=ObjectInstance, dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Model'])
async def get_model_object_instance(
    object_type: ObjectTypeEnum,
    object_name: str = Query('example_reservoir'),
    attribute_filter: str = Query('*', description='filter attributes by regex'),
    session_id = Depends(get_session_id)
    ):

    if attribute_filter != '*':
        raise HTTPException(500, 'setting attribute_filter != * is not support yet')

    o = SessionManager.get_model_object_instance(test_user, session_id, object_type, object_name)
    return serialize_model_object_instance(o)


# ------ connection


@app.get("/connections", response_model=List[Connection], dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Connections'])
async def get_connections(session_id = Depends(get_session_id)):

    connections = []

    for object_type in shop_session(test_user, session_id).model._all_types:
        generator = SessionManager.get_model_object_generator(test_user, session_id, object_type)
        for object_name in generator.get_object_names():
            from_object = generator[object_name]
            for relation_direction in RelationDirectionEnum:
                for relation_type in RelationTypeEnum:
                    for r in from_object.get_relations(
                        direction=relation_direction,
                        relation_type=relation_type
                    ):
                        to_object = serialize_model_object_instance(r)
                        connections += [Connection(
                            from_object=ObjectID(object_type=object_type, object_name=object_name),
                            to_object=ObjectID(object_type=r.get_type(), object_name=r.get_name()),
                            relation_type=relation_type,
                            relation_direction=relation_direction,
                        )]

    return connections

@app.put("/connections", dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Connections'])
async def add_connections(connections: List[Connection], session_id = Depends(get_session_id)):

    for connection in connections:

        fo_type, fo_name = connection.from_object.object_type, connection.from_object.object_name
        to_type, to_name = connection.to_object.object_type, connection.to_object.object_name
        relation_type = connection.relation_type if connection.relation_type != 'default' else ''

        fo = SessionManager.get_model_object_instance(test_user, session_id, fo_type, fo_name)
        to = SessionManager.get_model_object_instance(test_user, session_id, to_type, to_name)

        fo.connect_to(to, connection_type=relation_type)

@app.put("/connect/{from_type}/{from_name}/{to_type}/{to_name}", dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Connections'])
async def add_connection(
    from_type: ObjectTypeEnum, from_name: str,
    to_type: ObjectTypeEnum, to_name: str,
    connection_type: RelationTypeEnum=Query(RelationTypeEnum.default),
    session_id = Depends(get_session_id)):

    connection_type = connection_type if connection_type != 'default' else ''

    fo = SessionManager.get_model_object_instance(test_user, session_id, from_type, from_name)
    to = SessionManager.get_model_object_instance(test_user, session_id, to_type, to_name)
    fo.connect_to(to, connection_type=connection_type)

# ------ shop commands

@app.post("/simulation/{command}", response_model=CommandStatus, dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Simulation'])
async def post_simulation_command(command: ShopCommandEnum, args: CommandArguments = None, session_id = Depends(get_session_id)):

    sess = shop_session(test_user, session_id)
    sess._command = command
    try:
        status: bool = sess._execute_command(args.options, args.values) # does this return anything
    except Exception as e:
        http_raise_internal('failed to execute simulation command', e)
    return CommandStatus(
        message=('ok' if status else 'something went wrong ...'),
        status=status
    )

# ------- logging

logging_desc = """
Specify where SHOP should send log messages.

The messages are sent to the endpoint one by one in the body of POST requests. They are JSON formatted and contain three fields.

Example:

```json
{
"id": "42",
"level": "INFO",
"message": "SHOP is thinking about your problem"
}
```
"""

@app.post("/logging/endpoint", response_model=LoggingEndpoint, tags=['Logging'], description=logging_desc)
async def register_logging_endpoint(endpoint: LoggingEndpoint = Body(LoggingEndpoint(endpoint='http://host.docker.internal:5000/log/message')),session_id = Depends(get_session_id)):

    sessions = SessionManager.get_shop_sessions(test_user)
    if session_id in sessions:
        session_name = sessions[session_id]._name
    else:
        raise HTTPException(404, f'Session with id {{{session_id}}} not found')

    try:
        req = requests.post(
            f'{endpoint.endpoint}',
            data=json.dumps({
                'id':session_name,
                'level': 'INFO',
                'message':'Connection established'
            })
        )
    except Exception as e:
        http_raise_internal('failed to ping log endpoint', e)

    SessionManager.logging_endpoint = endpoint.endpoint
    return endpoint

# ------ topology
@app.get("/topology", dependencies=[Depends(check_that_time_resolution_is_set)], tags=['Topology'])
async def get_topology(session_id = Depends(get_session_id)):
    try:
        return Response(content=shop_session(test_user, session_id).model.build_connection_tree().source, media_type="text/plain")
    except:
        return CommandStatus(message = 'Failed to generate graphviz topology', status=False)

# ------ internal methods


@app.get("/internal", response_model=ApiCommands, tags=['__internals'])
async def get_available_internal_methods(session_id = Depends(get_session_id)):
    command_types = shop_session(test_user, session_id).shop_api.__dir__()
    command_types = list(filter(lambda x: x[0] != '_', command_types))
    return ApiCommands(command_types = command_types)

@app.get("/internal/{command}", response_model=ApiCommandDescription, tags=['__internals'])
async def get_internal_method_description(command: ApiCommandEnum, session_id = Depends(get_session_id)):
    doc = getattr(shop_session(test_user, session_id).shop_api, command).__doc__
    return ApiCommandDescription(description = str(doc))

@app.post("/internal/{command}", response_model=CommandStatus, tags=['__internals'])
async def call_internal_method(command: ApiCommandEnum, cmdargs: ApiCommandArgs = ApiCommandArgs(args=(), kwargs={}), session_id = Depends(get_session_id)):
    try:
        res = getattr(shop_session(test_user, session_id).shop_api, command)(*cmdargs.args, **cmdargs.kwargs)
        if command == 'GetTxySeriesY':
            res = np.transpose(res)
        return Response(content=json.dumps(res, cls=NumpyArrayEncoder), media_type="json/application")
    except:
        return CommandStatus(message = 'Invalid function or arguments', status=False)


# ------- test_async

# timer_states = []

# async def start_timer():
#     n = len(timer_states)
#     timer_states.append(10)
#     for i in range(10):
#         await asyncio.sleep(1.0)
#         timer_states[n] -= 1

# @app.post("/loop")
# async def start_loop():
#     asyncio.create_task(start_timer())
#     return timer_states

# @app.get("/loop")
# async def get_loops():
#     return timer_states

# ------- example

# @app.get("/users/me/", response_model=User, tags=['__fast api example'])
# async def read_users_me(current_user: User = Depends(get_current_active_user)):
#     return current_user


# @app.get("/users/me/items/",  tags=['__fast api example'])
# async def read_own_items(current_user: User = Depends(get_current_active_user)):
#     return [{"item_id": "Foo", "owner": current_user.username}]


# @app.post("/items/",  tags=['__fast api example'])
# async def create_item(item: Item):
#     return item