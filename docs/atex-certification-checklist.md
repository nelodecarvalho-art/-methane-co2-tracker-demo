# Checklist de certificação ATEX/IECEx

⚠️ Ponto central: a certificação precisa ser do **conjunto montado**
(sensor + gabinete + cabeamento), não apenas do sensor isolado. Isso muda
custo e prazo do piloto e é tratado aqui como risco explícito de
cronograma/orçamento, não como detalhe técnico enterrado.

- [ ] Definir a **zona de classificação** da área de instalação (Zona 0/1/2,
      IEC 60079-10) — determina a categoria de proteção exigida (Ex ia, Ex
      d, Ex e).
- [ ] Confirmar o certificado ATEX/IECEx do **modelo específico** do sensor
      (não da linha de produtos) — a versão de firmware do sensor entra no
      escopo do certificado.
- [ ] ⚠️ **Sensor de CO2 precisa da mesma certificação que o de CH4** — o
      produto agora suporta os dois gases (ver `docs/protocol-spec.md`),
      mas a exigência de certificação Ex é determinada pela **classificação
      da área de instalação** (risco de atmosfera explosiva do ambiente,
      tipicamente por hidrocarbonetos), não pelo gás que o sensor mede. Um
      sensor de CO2 instalado na mesma zona classificada de uma planta de
      O&G precisa de certificação ATEX/IECEx tanto quanto o sensor de CH4 —
      "CO2 não é inflamável" é um raciocínio comum, mas errado, para
      dispensar a certificação do equipamento nessa área.
- [ ] **Gabinete (enclosure)** do gateway/eletrônica precisa de certificação
      própria — comprar pronto de fabricante certificado (Ex d), nunca
      fabricar sob medida.
- [ ] **Cabeamento e prensa-cabos (cable glands)** certificados Ex — erro
      comum: usar cabo ou gland comum e invalidar a certificação do
      conjunto inteiro.
- [ ] Certificação do **conjunto montado**: sensor + gabinete + cabo
      certificados individualmente NÃO bastam — a integração física pode
      exigir avaliação própria por um organismo certificador (INMETRO no
      Brasil, ou notified body IECEx internacional).
- [ ] ⚠️ **Prazo**: certificação de conjunto tipicamente leva 4-12+ semanas
      dependendo do organismo — este é um risco de cronograma maior que o
      desenvolvimento de software inteiro do MVP.
- [ ] ⚠️ **Custo**: orçar a certificação de conjunto separadamente do custo
      dos componentes — é o item mais frequentemente subestimado no
      orçamento do piloto.
- [ ] **Mitigação**: se o cliente piloto exigir Zona 1 e a certificação de
      conjunto não estiver pronta no prazo, negociar instalação inicial em
      Zona 2 ou área não-classificada como prova de conceito, migrando para
      a zona crítica depois da certificação. Isso precisa estar registrado
      no Termo de Piloto assinado com o cliente, não descoberto depois.
