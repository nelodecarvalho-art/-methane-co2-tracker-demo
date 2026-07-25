# Diagramas de blocos — Methane & CO2 Tracker

| Documento | Diagramas de blocos — sistema e dispositivo de campo |
|---|---|
| Projeto | Methane & CO2 Tracker |
| Revisão | 01 |
| Data | 2026-07-25 |
| Repositórios relacionados | `methane-co2-tracker` (software), `methane-co2-tracker-firmware` (firmware) |

## Nota sobre a norma aplicada

Não existe uma norma ABNT específica para diagrama de blocos de sistemas
eletrônicos embarcados equivalente à IEC 60617 (a NBR 5444, às vezes citada
nesse contexto, trata de símbolos para **instalações elétricas prediais** —
tomadas, interruptores, eletrodutos — não de blocos funcionais de um
sistema embarcado). Os diagramas abaixo seguem:

- **Convenções gerais de apresentação de desenho técnico** que de fato são
  normatizadas pela ABNT independente do assunto (NBR 10068 — folha de
  desenho; NBR 8402 — lettering), refletidas aqui no bloco de identificação
  no topo do documento e na legenda explícita de convenções de linha
  abaixo.
- **Símbolos IEC 60617** onde um símbolo elétrico pontual é usado (terra,
  bateria) — é a referência internacional que o Brasil também adota para
  esse tipo de símbolo.
- Não são esquemáticos elétricos em nível de componente (sem resistores,
  pinout de MCU) — isso exigiria dados de projeto eletrônico real (KiCad),
  que não existem ainda nesta fase do MVP.

## Legenda (convenções de linha usadas nos dois diagramas)

- Linha sólida `───` : conexão física/com fio, ou fluxo de dados sempre
  presente.
- Linha tracejada `┄┄` : enlace sem fio (rádio).
- Linha pontilhada `┈┈` : caminho de fallback, usado só quando o caminho
  principal falha.

## 1. Diagrama de blocos — sistema (campo → nuvem → cliente)

```mermaid
flowchart LR
    subgraph CAMPO["Campo (área classificada)"]
        S_CH4["Sensor TDLAS CH4"]
        S_CO2["Sensor TDLAS CO2"]
        DEV["Dispositivo de campo<br/>(STM32L4 + FreeRTOS)"]
        S_CH4 --> DEV
        S_CO2 --> DEV
    end

    subgraph CONEC["Conectividade"]
        GW["Gateway LoRaWAN<br/>(outdoor, IP67)"]
        CEL["Rede celular<br/>(Cat M1/NB-IoT, fallback)"]
    end

    subgraph NUVEM["Cloud (methane-co2-tracker)"]
        NS["Network Server<br/>(ChirpStack ou AWS IoT Core for LoRaWAN)"]
        MQTT["Broker MQTT"]
        ING["Ingestão<br/>(decode Protobuf + valida + insere)"]
        DB[("TimescaleDB")]
        ALERT["Regra de alerta<br/>sustentado"]
        ANOM["Detecção de<br/>anomalia (Isolation Forest)"]
        NOTIFY["Notificação<br/>(e-mail/webhook)"]
        API["API REST<br/>(autenticada)"]
        RPT["Relatório de<br/>compliance (PDF)"]
    end

    subgraph CLIENTE["Cliente (operadora O&G)"]
        DASH["Dashboard<br/>(React)"]
    end

    DEV -.LoRaWAN.-> GW --> NS --> MQTT
    DEV -.Cat M1/NB-IoT<br/>(fallback).-> MQTT
    MQTT --> ING --> DB
    ING --> ALERT --> NOTIFY
    ING --> ANOM --> NOTIFY
    DB --> API --> DASH
    DB --> RPT --> DASH
```

## 2. Diagrama de blocos — dispositivo de campo

```mermaid
flowchart TB
    subgraph POWER["Alimentação"]
        BAT["Bateria + regulador"]
    end

    subgraph SENSOR["Sensoriamento"]
        TDLAS["Sensor TDLAS<br/>(CH4 ou CO2, fixo por dispositivo)"]
    end

    subgraph MCU_BLOCK["Processamento (STM32L4 + FreeRTOS)"]
        MCU["MCU STM32L4"]
        RTC["RTC<br/>(sincronização de tempo)"]
        TSAMPLE["task_sample"]
        TALERT["task_alert<br/>(janela sustentada local)"]
        TTX["task_transmit<br/>(serialização nanopb)"]
        MCU --- RTC
        TSAMPLE --> TALERT --> TTX
    end

    subgraph RADIO["Comunicação"]
        LORA["Rádio LoRaWAN<br/>(principal)"]
        CELL["Módulo celular<br/>(Quectel BG95, fallback)"]
    end

    BAT --> MCU
    BAT --> TDLAS
    BAT --> LORA
    BAT --> CELL

    TDLAS -- "I2C/UART/analógico<br/>(driver específico do sensor)" --> TSAMPLE
    TTX -.LoRaWAN.-> LORA
    TTX -.fallback.-> CELL

    ENCLOSURE["Gabinete Ex d<br/>(certificado, conjunto montado)"]
    MCU_BLOCK -.dentro do.-> ENCLOSURE
    RADIO -.dentro do.-> ENCLOSURE
```

## Como estes diagramas se relacionam com o código

- O diagrama 1 corresponde ao pipeline descrito em
  `docs/hardware-cloud-integration.md`.
- O diagrama 2 corresponde às tasks FreeRTOS do esqueleto de firmware em
  `methane-co2-tracker-firmware/src/` (`task_sample.c`, `task_alert.c`,
  `task_transmit.c`) e ao HAL de rádio (`radio_hal.c`).
- O bloco "Gabinete Ex d" no diagrama 2 corresponde ao item de
  certificação de conjunto em `docs/atex-certification-checklist.md`.
