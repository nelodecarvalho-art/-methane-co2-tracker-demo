# Especificação do protocolo de dados (sensor → cloud)

## Decisão de formato

**Protobuf + nanopb**, não CBOR nem JSON. O schema é fixo e pequeno — não
precisamos da flexibilidade self-describing do CBOR. nanopb é o caminho mais
trilhado em firmware embarcado LoRaWAN: gera código C direto do `.proto`, e o
mesmo arquivo gera o decoder Python do backend. Schema único, sem parser
manual duplicado nas duas pontas.

## Schema

```protobuf
syntax = "proto3";

enum GasType {
  CH4 = 0;
  CO2 = 1;
}

message SensorReading {
  uint32 sensor_id          = 1;  // ID numérico curto (2 bytes), mapeado pro
                                   // sensor_id string no backend via tabela
                                   // de mapeamento em `sensors`
  uint32 timestamp          = 2;  // unix epoch, segundos
  GasType gas_type          = 3;  // qual gás este sensor mede
  uint32 concentration_ppm  = 4;  // ppm bruto, sem escala
  sint32 temperature_c_x10  = 5;  // temperatura * 10 (ex: 235 = 23.5°C),
                                   // zigzag encoding pra negativos
  uint32 battery_pct        = 6;  // 0-100
  uint32 flags               = 7; // bitfield: bit0=alerta local disparado,
                                   // bit1=bateria baixa, bit2=falha de sensor
}
```

O campo `gas_type` foi adicionado nesta fase para suportar o segundo gás do
produto (CO2), além do CH4 original. Cada sensor físico mede um único gás
(`gas_type` é fixo por dispositivo), mas o schema do backend passa a
comportar leituras e alertas segregados por gás desde já — evita retrabalho
de schema quando o sensor de CO2 entrar no piloto.

Este arquivo `.proto` é a fonte única de verdade e deve ser idêntico nos dois
repositórios (`methane-co2-tracker/proto/` e
`methane-co2-tracker-firmware/proto/`).

## Orçamento de payload

LoRaWAN limita o payload de aplicação a ~51-222 bytes dependendo do spreading
factor (SF12 é o pior caso, ~51 bytes). O schema acima serializa em
aproximadamente 19-25 bytes, com margem confortável mesmo no pior caso de SF,
sem contar o overhead do MAC layer do próprio LoRaWAN (tratado separadamente
pelo rádio).

## Sensor ID numérico

O payload do rádio carrega `sensor_id` como `uint32` (na prática usamos só 2
bytes de faixa útil) em vez do `sensor_id` string usado no backend/dashboard.
A tabela `sensors` mantém o mapeamento `sensor_id_short → sensor_id`, e o
consumidor MQTT do backend traduz na ingestão.

## Impacto no pipeline de software

- **Ingestão MQTT**: o consumidor decodifica os bytes Protobuf recebidos
  ANTES de validar com Pydantic (decode protobuf → dict → validação Pydantic
  → insert).
- **Simulador**: publica os mesmos bytes Protobuf serializados via nanopb,
  não JSON solto — o backend nasce testado contra o formato real do firmware.
