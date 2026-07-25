# Integração hardware → cloud

## Caminho do dado (dispositivo real, produção)

1. Sensor TDLAS → HAL local → `task_sample` lê a cada N segundos. Cada
   sensor físico mede um único gás (CH4 **ou** CO2, fixo por dispositivo —
   ver `docs/protocol-spec.md`), refletido no campo `gas_type` do payload.
2. `task_alert` avalia a regra local (janela sustentada — 500ppm/2min para
   CH4, 5000ppm/2min para CO2, mesmos defaults do backend) → seta o bit0 do
   campo `flags` se disparar. Essa regra roda **duplicada** — uma vez no
   firmware (alarme local mesmo sem rede) e outra no backend (fonte de
   verdade pro dashboard/relatório). Isso é intencional: o dispositivo em
   campo precisa soar alarme mesmo se LoRaWAN e 4G caírem ao mesmo tempo.
3. `task_transmit` monta `SensorReading`, serializa via nanopb (~19-25
   bytes, até 38 bytes no pior caso — ver `SensorReading_size` gerado).
4. Envio via LoRaWAN (rádio principal). Se falhar após N tentativas,
   fallback para celular (Cat M1/NB-IoT).

Esqueleto de código (C/FreeRTOS) desta lógica vive no repositório separado
`methane-co2-tracker-firmware` — ver seção própria abaixo.

## Pipeline real implementado no backend (Fases 2-6)

Esta seção documenta o que **de fato** existe hoje no `backend/`, não
apenas o desenho original de arquitetura — importante distinguir dos
pontos em aberto listados adiante.

1. **Ingestão** (`app/ingestion/mqtt_consumer.py`): decodifica os bytes
   Protobuf recebidos, valida com Pydantic (rejeita `concentration_ppm`
   fora de faixa, `battery_pct` fora de 0-100, timestamp implausível/RTC
   não sincronizado), insere em `readings` (TimescaleDB, hypertable).
   Mensagem malformada é descartada e logada, nunca derruba o consumer.
2. **Alerta sustentado** (`app/alerts/rules.py`): reavalia a janela do
   banco a cada leitura nova (sem estado em memória), por `sensor_id` +
   `gas_type` — mesma semântica documentada acima para o firmware, agora
   como fonte de verdade do lado cloud.
3. **Notificação de alerta** (`app/alerts/notify.py`): e-mail + webhook
   quando um alerta abre, com `Alert.notified_at` marcado se pelo menos um
   canal entregou.
4. **Detecção de anomalia** (`app/anomaly/detector.py`): Isolation Forest
   por sensor+gás, treinado sob demanda sobre o histórico recente
   (`concentration_ppm`, `temperature_c`, `battery_pct`), complementando a
   regra de limiar fixo — pensado para pegar desvios de comportamento que
   não cruzam o threshold de segurança.
5. **Notificação de anomalia** (`app/anomaly/notify.py`): dispara só no
   início de um novo episódio de anomalia (não repete leitura a leitura),
   canal de webhook separado do alerta de segurança.
6. **API REST + dashboard** (`app/api/`, `frontend/`): consulta paginada de
   leituras/alertas/dispositivos, e relatório de compliance ANP/EPA sob
   demanda (`GET /reports/compliance`), com botão dedicado no dashboard.

Autenticação da API está em transição de uma API key fixa compartilhada
para login individual por usuário (JWT) — trabalho iniciado mas não
concluído nesta rodada; não impacta o firmware (a autenticação da API é
consumida só pelo dashboard e por integrações externas, não pelo caminho
sensor→MQTT→backend).

## No MVP local (sem gateway físico)

O simulador de software (`simulator/`) publica os MESMOS bytes Protobuf
direto no Mosquitto local, no tópico `sensors/{sensor_id_short}/readings`.
Não existe Network Server real nesta fase — o objetivo é provar que o
backend aceita o formato binário real antes de qualquer instalação em
campo.

## Em produção (com gateway físico)

```
Sensor --LoRaWAN--> Gateway (Dragino/RAK)
       --> Network Server (ChirpStack self-hosted OU AWS IoT Core for LoRaWAN)
       --extrai FRMPayload--> MQTT/HTTP
       --> Backend decodifica Protobuf --> valida Pydantic --> insere em `readings`
```

## Firmware do dispositivo de campo

Vive no repositório separado `methane-co2-tracker-firmware` (STM32L4 +
FreeRTOS, conforme `README.md` deste repo). Estado atual: **esqueleto de
código, não firmware compilável** — a lógica das 3 tasks (amostragem,
alerta local, transmissão com fallback) está escrita e comentada, e o
código Protobuf/nanopb (`generated/sensor_reading.pb.{c,h}`) foi gerado de
verdade a partir do `.proto` compartilhado, mas falta o HAL real do sensor,
o runtime C do nanopb, e as stacks LoRaWAN/celular — todos fora do escopo
desta entrega por exigirem hardware físico e/ou bibliotecas de terceiros
vendorizadas. Verificado por revisão de código, não por build/flash real.

## Ponto em aberto (risco de arquitetura para a Fase 2, não decidir agora)

"AWS IoT Core" sozinho **não** fala LoRaWAN nativamente — exige o serviço
gerenciado "AWS IoT Core for LoRaWAN" (que só aceita gateways da lista de
compatibilidade deles) OU hospedar um Network Server próprio (ChirpStack) e
fazer bridge MQTT para o AWS IoT Core. Isso é decisão de Fase 2, mas impacta
diretamente qual modelo de gateway comprar — sinalizando aqui para não
comprar um gateway incompatível antes dessa decisão estar fechada.

**Nota (2026-07-25): este ponto continua em aberto** — as Fases 2-6
implementaram o pipeline de software inteiro contra o Mosquitto local do
MVP (sem gateway físico nem Network Server real), então esta decisão de
arquitetura de produção não foi forçada a ser tomada ainda. Continua sendo
a decisão mais importante a fechar antes de comprar hardware de gateway.
