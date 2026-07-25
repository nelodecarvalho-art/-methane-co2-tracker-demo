from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GasType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CH4: _ClassVar[GasType]
    CO2: _ClassVar[GasType]
CH4: GasType
CO2: GasType

class SensorReading(_message.Message):
    __slots__ = ("sensor_id", "timestamp", "gas_type", "concentration_ppm", "temperature_c_x10", "battery_pct", "flags")
    SENSOR_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    GAS_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONCENTRATION_PPM_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_C_X10_FIELD_NUMBER: _ClassVar[int]
    BATTERY_PCT_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    sensor_id: int
    timestamp: int
    gas_type: GasType
    concentration_ppm: int
    temperature_c_x10: int
    battery_pct: int
    flags: int
    def __init__(self, sensor_id: _Optional[int] = ..., timestamp: _Optional[int] = ..., gas_type: _Optional[_Union[GasType, str]] = ..., concentration_ppm: _Optional[int] = ..., temperature_c_x10: _Optional[int] = ..., battery_pct: _Optional[int] = ..., flags: _Optional[int] = ...) -> None: ...
