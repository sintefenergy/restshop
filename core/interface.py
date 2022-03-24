from typing import *
from datetime import datetime
import pandas as pd
import numpy as np
from fastapi import HTTPException
from pyshop import ShopSession
from .schemas import TimeSeries, Curve, Connection, RelationDirectionEnum, RelationTypeEnum


def set_txy(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: Union[TimeSeries, int, float]):
    if type(value) == float or type(value) == int:
        start_time = shop.get_time_resolution()['starttime']
        value = TimeSeries(
            timestamps=[start_time],
            values=[[value]]
        )
    try:
        time_series: TimeSeries = value
        index, values = time_series.timestamps, np.transpose(time_series.values)
        df = pd.DataFrame(index=index, data=values)
        shop.model[object_type][object_name][attribute_name].set(df)
    except Exception as e:
        raise HTTPException(500, f'trouble setting txy {object_type} {object_name} {attribute_name} -- Internal Exception: {e}')

def set_xy(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: Curve):
    try:
        curve: Curve = value
        ser = pd.Series(index=curve.x_values, data=curve.y_values)
        shop.model[object_type][object_name][attribute_name].set(ser)
    except Exception as e:
        raise HTTPException(500, f'trouble setting xy {object_type} {object_name} {attribute_name} -- Internal Exception: {e}')

def set_xy_array(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: OrderedDict[float, Curve]):
    try:
        curves: OrderedDict[float, Curve] = value
        ser_list = []
        for ref, curve in curves.items():
            ser_list += [pd.Series(index=curve.x_values, data=curve.y_values, name=ref)]
        shop.model[object_type][object_name][attribute_name].set(ser_list)
    except Exception as e:
        raise HTTPException(500, f'trouble setting xy_array {object_type} {object_name} {attribute_name} -- Internal Exception: {e}')

def set_xyt(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: OrderedDict[datetime, Curve]):
    try:
        curves: OrderedDict[datetime, Curve] = value
        ser_list = []
        for ref, curve in curves.items():
            ser_list += [pd.Series(index=curve.x_values, data=curve.y_values, name=ref)]
        shop.model[object_type][object_name][attribute_name].set(ser_list)
    except Exception as e:
        raise HTTPException(500, f'trouble setting xyt {object_type} {object_name} {attribute_name} -- Internal Exception: {e}')

def set_int(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: Union[TimeSeries, int, float]):
    shop.model[object_type][object_name][attribute_name].set(int(value))

def set_double(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: Union[TimeSeries, int, float]):
    shop.model[object_type][object_name][attribute_name].set(float(value))

def set_default(shop: ShopSession, object_type: str, object_name: str, attribute_name: str, value: Union[TimeSeries, int, float]):
    try:
        shop.model[object_type][object_name][attribute_name].set(value)
    except Exception as e:
        raise HTTPException(500, f'trouble setting xyt {str(type(value))} {object_type} {object_name} {attribute_name} -- Internal Exception: {e}')

def set_datatype(datatype: str) -> Callable:
    switcher = {
        'txy': set_txy,
        'xy': set_xy,
        'xy_array': set_xy_array,
        'xyn': set_xy_array,
        'int': set_int,
        'double': set_double
    }
    return switcher.get(datatype, set_default)

def get_model_connections(shop: ShopSession) -> List[Connection]:
    connections = []

    for object_type in shop.model._all_types:
        generator = shop.model[object_type]
        for object_name in generator.get_object_names():
            from_object = generator[object_name]
            for relation_direction in RelationDirectionEnum:
                for relation_type in RelationTypeEnum:
                    for r in from_object.get_relations(
                        direction=relation_direction,
                        relation_type=relation_type
                    ):
                        connections.append(
                            Connection(
                                from_=object_name,
                                from_type=object_type,
                                to=r.get_name(),
                                to_type=r.get_type(),
                                relation_type=relation_type,
                                relation_direction=relation_direction,
                            )
                        )

    return connections