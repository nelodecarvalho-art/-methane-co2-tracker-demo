# Methane & CO2 Tracker

SaaS de detecção de vazamento de metano/CO2 para operações de Óleo & Gás, com
foco em compliance ANP (Resolução 712) e EPA, e metas ESG.

## Status

MVP em construção — Fase 1 (software) e Fase 1 (hardware/firmware) em andamento.
Ver `docs/` para specs de protocolo, integração hardware↔cloud, checklist de
certificação ATEX/IECEx e BOM.

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

(Backend/frontend ainda não têm Dockerfile — isso vem nos próximos passos.)
