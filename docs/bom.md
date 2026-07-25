# BOM (Bill of Materials) — draft

⚠️ Todos os valores abaixo são **estimativas de mercado obtidas por busca**,
não cotações formais verificadas. A ação "orçar 3 sensores" do plano de
90 dias continua obrigatória antes de fechar o orçamento do piloto.

| Item | Modelo/Fornecedor | Certificação | Custo estimado | Lead time típico |
|---|---|---|---|---|
| Sensor TDLAS CH4 | NevadaNano MPS (Zona 0, sem calibração por 15 anos) ou Cubic Gasboard-2501 (Ex ia IIC T4 Ga) | ATEX/IECEx no próprio sensor | Não publicado — cotação formal obrigatória | Sensores certificados costumam ter lead time mais longo que eletrônica comum — confirmar na cotação |
| Sensor TDLAS CO2 | Cubic GasTDL-3100 (também mede CO/O2 — usar só o canal CO2) | **Exd II CT6** (invólucro à prova de explosão) — nota: conceito de proteção diferente do Ex ia do sensor de CH4 acima; confirmar compatibilidade com o gabinete/cabeamento Ex escolhido antes de misturar os dois tipos de proteção no mesmo painel | Não publicado — cotação formal obrigatória | Analisador de processo, tende a lead time mais longo que sensor de ponto único — confirmar na cotação |
| Gateway LoRaWAN outdoor | RAK7249 (outdoor) ou Dragino LPS8 — **não** o LG308 (indoor) | Gabinete IP67 do próprio gateway (não é certificação de área classificada) | RAK7249 listado a partir de ~US$499 (fonte: eBay, não é cotação oficial) | Normalmente em estoque, 2-4 semanas |
| Placa de firmware p/ prototipagem | STM32 Nucleo LoRa bundle (P-NUCLEO-LRWAN2) | N/A (bancada, não vai a campo) | ~US$99 o bundle | Estoque em Digikey/Mouser |
| Módulo celular fallback | Quectel BG95-M3 (Cat M1/NB2 + GNSS) | N/A | Não encontrado preço de produção | Eval board ~3 semanas; confirmar com distribuidor |
| Gabinete Ex d | Fabricante certificado (a definir) | Ex d — comprado pronto, nunca fabricado sob medida | Altamente variável — precisa cotação | 4-8 semanas |
| Cabeamento + prensa-cabos Ex | Junto ao fornecedor do gabinete, idealmente | Ex certificado | Item de linha, não pode ser esquecido do orçamento | Junto ao gabinete |

## Fontes

- [NevadaNano MPS Methane Gas Sensor](https://nevadanano.com/products/mps-methane-gas-sensor/)
- [ATEX Certification is Secured by NevadaNano](https://nevadanano.com/nevada-nano-earns-their-atex-certification/)
- [Cubic Gasboard-2501 TDLAS CH4 Sensor](https://www.cubic-methane-detection.com/products/tdlas-ch4-sensor/)
- [Cubic Achieves International Explosion-Proof Certification for TDLAS Methane Sensor Gasboard-2501](https://www.cubic-methane-detection.com/cubic-achieves-international-explosion-proof-certification-for-tdlas-methane-sensor-gasboard-2501.html)
- [Cubic GasTDL-3100 TDLAS Analyzer (CO2/O2/CO)](https://www.directindustry.com/prod/cubic-instruments-wuhan-ltd/product-187991-2382105.html)
- [Dragino LG308 Indoor LoRaWAN Gateway](https://www.dragino.com/products/lora-lorawan-gateway/item/140-lg308.html)
- [STMicro Nucleo LoRa Development Board Bundles](https://www.hackster.io/news/stmicro-launches-low-cost-ready-to-run-stm32-nucleo-lora-development-board-bundles-d35b64d7b21f)
- [Quectel BG95 Series](https://www.quectel.com/product/lpwa-bg95-cat-m1-cat-nb2-egprs-series/)
