# Methane & CO2 Tracker

SaaS de detecção de vazamento de metano/CO2 para operações de Óleo & Gás, com
foco em compliance regulatório (ANP/EPA) e metas ESG.

## Status

Backend em produção no Render: ingestão MQTT, regra de alerta por limiar
sustentado, detecção de anomalia por ML (Isolation Forest), notificações por
e-mail/webhook (alerta e anomalia, canais separados) e relatório de
compliance em PDF sob demanda. Frontend (dashboard React) cobre login,
gráfico de leituras, lista de alertas e geração do relatório de compliance.

Frente de hardware: esqueleto de firmware (STM32L4/FreeRTOS, repositório
separado `methane-co2-tracker-firmware`) implementado e revisado por código,
mas ainda não compilado/testado em hardware real — falta toolchain ARM e
stacks LoRaWAN/celular. Checklist de certificação ATEX/IECEx e BOM
atualizados.

Ver `relatorios/` para os relatórios de progresso entregues ao cliente por
fase, e `docs/` para specs de protocolo, integração hardware↔cloud,
checklist de certificação ATEX/IECEx e BOM.

## Estrutura

- `backend/` — API FastAPI, ingestão MQTT, regra de alerta, detecção de
  anomalia, geração de relatório PDF.
- `frontend/` — Dashboard React.
- `simulator/` — Simulador de sensores publicando via MQTT (payload Protobuf,
  compatível com o firmware real).
- `docs/` — Specs de protocolo, integração hardware↔cloud, certificação, BOM.
- Firmware embarcado (STM32L4/FreeRTOS) vive em repositório separado:
  `methane-co2-tracker-firmware`.

## Rodando localmente

```
cp .env.example .env   # preencher com valores reais, .env não é versionado
docker-compose up
```

(Backend já tem Dockerfile. Deploy do frontend ainda não documentado aqui.)
