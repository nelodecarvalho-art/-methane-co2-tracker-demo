"""
Script standalone (sem pytest). Não depende de banco nem broker — só do
módulo gerado a partir de proto/sensor_reading.proto. Roda:
python tests/test_proto_roundtrip.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.generated import sensor_reading_pb2 as pb  # noqa: E402


def main() -> None:
    msg = pb.SensorReading(
        sensor_id=65000,
        timestamp=1753290000,
        gas_type=pb.CH4,
        concentration_ppm=612,
        temperature_c_x10=-55,
        battery_pct=42,
        flags=0b010,
    )
    data = msg.SerializeToString()
    assert len(data) <= 25, f"payload passou do orçamento LoRaWAN: {len(data)} bytes"

    decoded = pb.SensorReading()
    decoded.ParseFromString(data)

    assert decoded.sensor_id == 65000
    assert decoded.gas_type == pb.CH4
    assert pb.GasType.Name(decoded.gas_type) == "CH4"
    assert decoded.concentration_ppm == 612
    assert decoded.temperature_c_x10 == -55  # zigzag encoding de negativo
    assert decoded.battery_pct == 42
    assert decoded.flags == 0b010

    msg_co2 = pb.SensorReading(sensor_id=1, timestamp=0, gas_type=pb.CO2, concentration_ppm=100)
    decoded_co2 = pb.SensorReading()
    decoded_co2.ParseFromString(msg_co2.SerializeToString())
    assert pb.GasType.Name(decoded_co2.gas_type) == "CO2"

    print(f"OK: roundtrip protobuf ({len(data)} bytes), CH4 e CO2 distinguidos corretamente")


if __name__ == "__main__":
    main()
