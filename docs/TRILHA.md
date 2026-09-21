# Trilha dos 153 indicadores

As 153 métricas do *Manual de Validação de Estratégias Sistemáticas* organizadas por
**nível de leitura**, não por capítulo.

A diferença importa. O manual é ordenado pela sequência de uma validação real
(integridade → edge → evidência → OOS → risco → execução), que é a ordem certa para
**auditar**. Esta trilha é ordenada pela sequência em que um leitor consegue
**entender** — que é outra coisa.

Os três níveis respondem a três perguntas diferentes:

| Nível | Pergunta | Métricas | Post |
|---|---|---|---|
| **Iniciante** | O que é um resultado? | 26 | Wizz Concept |
| **Intermediário** | Esse resultado é confiável? | 71 | Wizz Data / Research |
| **Avançado** | Como eu me enganei sem perceber? | 56 | Wizz Research |

> **Regra de progressão.** Ninguém precisa das 153. Um investidor individual que
> domine o nível iniciante inteiro e três ou quatro coisas do intermediário já
> decide melhor que a maioria. O nível avançado existe para quem vai *construir*
> uma estratégia sistemática, não para quem vai escolher entre fundos.

---

## Nível 1 — Iniciante

**A pergunta:** o que é um resultado, e como se lê um sem se enganar?

Este nível não tem nenhuma estatística inferencial. É aritmética honesta. O objetivo
é sair daqui sabendo que *retorno não é resultado* — resultado é retorno junto com o
risco que foi preciso correr para obtê-lo.

### 1.1 A economia de uma operação

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 3 | Win Rate | Com que frequência os trades terminam positivos? |
| 4 | Loss Rate | E com que frequência terminam negativos? |
| 5 | Payoff Ratio | Quanto o ganho médio compensa a perda média? |
| 6 | Break-even Win Rate | Qual acerto mínimo evita prejuízo? |
| 1 | Expectancy por trade | Quanto se espera ganhar por operação? |
| 7 | Profit Factor | Quanto lucro bruto por unidade de perda bruta? |
| 8 | Average Winner / Loser | Qual a magnitude típica de cada lado? |
| 9 | Median Trade | O trade típico é lucrativo, ou a média depende de extremos? |
| 10 | Largest Winner / Loser | Quanto os extremos influenciam o perfil? |

**Por que nesta ordem.** Win rate vem primeiro porque é o que todo mundo já acha que
sabe — e é justamente onde mora o erro mais comum. Colocar payoff e break-even logo
em seguida desarma o erro antes que ele vire hábito: *acerto e qualidade são coisas
diferentes*. Expectancy só aparece depois, porque ela é a síntese dos dois anteriores.

### 1.2 O preço que se paga

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 28 | Maximum Drawdown | Qual a maior queda entre um pico e o fundo seguinte? |
| 29 | Average Drawdown | Qual a profundidade média das quedas? |
| 32 | Time Under Water | Que fração do tempo se passa abaixo do pico? |
| 31 | Drawdown Duration | Quanto tempo dura uma queda? |
| 33 | Recovery Time | Quanto demora para recuperar? |
| 36 | Worst Trade / Day / Week / Month | Quais foram as piores perdas em cada horizonte? |

**A ideia que precisa ficar.** Profundidade e duração são riscos diferentes. Uma queda
de 15% que dura três anos costuma ser mais difícil de aguentar que uma de 25% que dura
dois meses — e só a segunda aparece bem em qualquer ranking.

### 1.3 Juntando retorno e risco

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| — | CAGR | Quanto o capital cresceu ao ano, de forma composta? |
| — | Volatilidade | Quanto o resultado oscila? |
| 15 | Sharpe Ratio | Quanto retorno por unidade de oscilação total? |
| 16 | Sortino Ratio | E por unidade de oscilação **para baixo**? |
| 19 | Calmar Ratio | Quanto retorno por unidade de queda máxima? |
| 150 | Benchmark-relative | A estratégia agrega algo além de estar no mercado? |
| 151 | Beta / Market Exposure | Quanto do resultado é simplesmente estar comprado? |

**Onde o iniciante tropeça.** Sharpe é tratado como nota de prova. Ele não é: supõe que
volatilidade mede risco, o que deixa de valer quando a distribuição tem cauda esquerda
pesada. Sharpe alto com assimetria muito negativa é alerta, não elogio — mas isso só
faz sentido depois de ver *skewness*, que é nível 2.

### 1.4 A operação no tempo

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 112 | Exposure | Quanto tempo se fica exposto? |
| 114 | Trades per Year | Quantas operações por ano? |
| 115 | Average Holding Period | Quanto tempo uma posição fica aberta? |
| 116 | Winner vs Loser Holding Time | Ganhos e perdas duram tempos diferentes? |

**Por que isto é nível 1.** Porque é onde mora o diagnóstico comportamental mais direto:
se as perdas ficam abertas mais tempo que os ganhos, o sistema realiza lucro cedo e
carrega prejuízo esperando voltar. Isso é legível sem estatística nenhuma.

---

## Nível 2 — Intermediário

**A pergunta:** esse resultado é confiável?

Aqui entram três ideias novas: **a forma da distribuição** (não basta a média), **a
incerteza da estimativa** (o número tem um intervalo em volta) e **o custo** (o edge
bruto quase nunca sobrevive inteiro).

### 2.1 A forma da distribuição

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 11 | Skewness | A cauda é maior para ganhos ou para perdas? |
| 12 | Kurtosis / Excess Kurtosis | Com que frequência aparecem extremos? |
| 13 | Tail Ratio | A cauda boa é maior que a ruim? |
| 14 | IQR e MAD | Qual a dispersão robusta, sem depender de extremos? |
| 2 | Expectancy em R-multiples | O edge é comparável entre tamanhos de posição? |

### 2.2 Risco de cauda e sobrevivência

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 34 | VaR | Qual perda-limite é excedida em X% dos períodos? |
| 35 | Expected Shortfall / CVaR | Quando entra na cauda ruim, qual a perda média? |
| 30 | Median Drawdown | Qual a queda do episódio mediano? |
| 40 | Maximum Consecutive Losses | Qual a maior sequência de perdas? |
| 41 | Maximum Consecutive Wins | Os ganhos também vêm em blocos? |
| 42 | Drawdown Recovery Profile | Como a recuperação muda com o tamanho da queda? |
| 24 | Ulcer Index | Quão profundas **e** persistentes são as quedas? |
| 39 | Kelly Fraction | Que fração do capital maximiza crescimento? |
| 38 | Risk of Ruin | Qual a chance de chegar a um capital inviável? |

**Par que ensina sozinho.** VaR e Expected Shortfall. O VaR diz onde a cauda começa; o
ES diz o que acontece dentro dela. Quem reporta só o primeiro está escondendo o segundo.

### 2.3 Os outros ratios

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 17 | Omega Ratio | Ganho acima do limiar supera a perda abaixo? |
| 18 | Gain-to-Pain | Quanto ganho por unidade de retorno negativo? |
| 20 | MAR Ratio | Retorno anualizado sobre a queda máxima do histórico |
| 21 | Sterling Ratio | Calmar com margem de segurança |
| 22 | Burke Ratio | Retorno sobre o *conjunto* de quedas, não só a pior |
| 23 | Recovery Factor | Lucro líquido sobre a pior queda |
| 25 | Martin Ratio / UPI | Retorno por unidade de Ulcer Index |
| 26 | Return on Exposure | Retorno por unidade de tempo exposto |
| 27 | SQN | Expectancy é grande frente à dispersão e ao N? |

**Aviso de método que vale um post inteiro.** Sterling, Burke, MAR, Gain-to-Pain e as
métricas de eficiência têm **convenções diferentes** entre autores e plataformas. Dois
relatórios podem mostrar "Sterling 0,8" e "Sterling 1,4" para a mesma estratégia sem
que nenhum esteja errado. Por isso o manual insiste: declare a fórmula no relatório.

### 2.4 A primeira dose de incerteza

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 43 | T-statistic da Expectancy | O ganho médio é grande frente ao erro de estimação? |
| 44 | Confidence Interval | Que faixa de edge é compatível com os dados? |
| 45 | Probability E > 0 | Que fração das reamostragens dá edge positivo? |
| 53 | Bootstrap Standard Error | Quão variável é a métrica sob reamostragem? |
| 54 | IID Trade Bootstrap | E se os trades fossem sorteados de novo? |

**O salto conceitual do nível 2.** Deixar de tratar uma estimativa como fato. "+0,08R por
trade" vira "os dados suportam algo entre −0,06R e +0,24R". É uma afirmação bem
diferente — e a honesta.

### 2.5 Monte Carlo

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 57 | Monte Carlo Equity Distribution | Que curvas de capital eram plausíveis? |
| 58 | Monte Carlo MDD P50/P95/P99 | Qual queda é típica, e qual é plausível na cauda? |
| 59 | Monte Carlo Terminal Equity | Qual a distribuição do capital final? |
| 60 | Monte Carlo Max Losing Streak | Que sequência de perdas é plausível? |
| 61 | Monte Carlo Probability of Loss | Qual a chance de terminar no prejuízo? |

**A figura que muda decisão.** O MDD observado quase sempre fica bem à direita da
distribuição simulada — ou seja, o histórico foi sortudo. Quem dimensiona posição pelo
MDD observado está dimensionando pela sorte.

### 2.6 Fora da amostra, pela primeira vez

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 63 | Out-of-Sample Performance | Funciona em dados que não escolheram as regras? |
| 64 | OOS/IS Ratio | Quanto do desempenho sobrevive? |
| 65 | OOS Degradation | Quanto se perdeu? |
| 66 | Walk-Forward Efficiency | Mantém qualidade ao recalibrar sequencialmente? |
| 67 | Positive OOS Windows % | Em quantas janelas o edge segue positivo? |

### 2.7 Robustez de parâmetros

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 73 | Parameter Stability | Valores vizinhos também funcionam? |
| 74 | Parameter Surface Smoothness | A superfície é suave ou cheia de picos? |
| 75 | Neighborhood Robustness | O ótimo é bom demais comparado aos vizinhos? |
| 76 | Parameter Plateau Width | Que parcela do espaço fica perto do ótimo? |
| 77 | Parameter Drift | O ótimo muda muito entre janelas? |
| 78 | Lag Robustness | O edge sobrevive a um dia de atraso? |
| 79 | Price Perturbation | E a uma pequena piora no preço executado? |
| 80 | Rule Perturbation | E a uma pequena mudança na lógica? |
| 81 | Data Perturbation | E a outra convenção de ajuste de dados? |

**Regra visual.** Regiões largas e suaves convencem; picos estreitos, não. Um ótimo
isolado cercado de resultados ruins é quase sempre ruído escolhido depois do fato.

### 2.8 Custo, o assassino silencioso

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 108 | Slippage Sensitivity | Quanto piora quando o preço executado piora? |
| 109 | Break-even Transaction Cost | Que custo zera a expectancy? |
| 110 | Cost Safety Margin | Quantas vezes o custo suportável excede o esperado? |
| 111 | Turnover | Quanto capital é girado? |
| 113 | Capital Utilization | Quanto do capital fica comprometido? |
| 146 | Gross vs Net Performance | Quanto da performance as fricções consomem? |
| 147 | Fee Sensitivity | Mudança de corretagem muda a viabilidade? |
| 148 | Spread Sensitivity | A estratégia suporta spreads maiores? |
| 149 | Funding / Financing Drag | Custo de carregamento altera o edge? |

**O que observar não é o nível, é a inclinação.** Uma estratégia cujo edge cai pela
metade com 0,05R de custo extra não existe fora do backtest.

### 2.9 Geometria do trade

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 117 | MAE | Quanto o trade andou contra antes de sair? |
| 118 | MFE | Quanto chegou a ganhar antes de sair? |
| 119 | MFE Capture Ratio | Quanto do movimento favorável foi monetizado? |
| 120 | MAE Efficiency / Stop Efficiency | O stop está longe demais? |
| 121 | Entry Efficiency | A entrada ocorre em região favorável? |
| 122 | Exit Efficiency | A saída captura fração adequada do movimento? |

> **Armadilha.** A nuvem MAE×MFE serve para **levantar hipóteses**, nunca para desenhar
> retroativamente o stop perfeito. Esse é o caminho mais curto para o overfitting, e ele
> parece análise.

### 2.10 Concentração e regime

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 103 | PnL Concentration | Quanto do lucro vem dos melhores trades? |
| 104 | Remove Best Trades Test | A estratégia sobrevive sem eles? |
| 105 | Remove Worst Trades Test | As perdas são anômalas ou recorrentes? |
| 106 | HHI de Contribuição | Quão concentrado está o P&L? |
| 107 | Breadth | Quantas apostas independentes existem de verdade? |
| 94 | Regime Performance | Em que ambiente ganha e em qual perde? |
| 96 | Positive Months / Quarters / Years | O resultado está distribuído no calendário? |
| 97–100 | Rolling Expectancy / PF / Sharpe / Stability | O edge persiste em janela móvel? |
| 152 | Correlation to Other Strategies | Diversifica ou repete o mesmo risco? |
| 153 | Drawdown Overlap | As estratégias sofrem ao mesmo tempo? |

### 2.11 Integridade — o que dá para auditar sem ser especialista

| # | Auditoria | A pergunta em uma linha |
|---|---|---|
| 130 | Lookahead Audit | Alguma decisão usou informação que não existia? |
| 131 | Repainting Audit | O indicador histórico muda depois? |
| 136 | Survivorship Bias Audit | O universo inclui quem desapareceu? |

---

## Nível 3 — Avançado

**A pergunta:** como eu me enganei sem perceber?

Este nível inteiro é sobre **o pesquisador**, não sobre a estratégia. Ele mede o efeito
de ter testado muitas coisas, de ter olhado o mesmo histórico muitas vezes e de ter
parado de procurar quando o resultado ficou bonito.

### 3.1 Inferência corrigida

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 49 | Effective Sample Size | Quantas observações independentes existem de fato? |
| 50 | Autocorrelation | Resultados consecutivos são dependentes? |
| 51 | Ljung-Box Test | Há autocorrelação conjunta em vários lags? |
| 52 | Newey-West / HAC | A significância sobrevive à correção? |
| 55 | Moving Block Bootstrap | Como reamostrar preservando dependência local? |
| 56 | Stationary Bootstrap | E sem fixar o comprimento do bloco? |
| 62 | Monte Carlo Sensitivity | A conclusão depende do método de simulação? |

**Por que isto é avançado.** Porque exige aceitar que 420 trades correlacionados podem
valer como 90 independentes — e que quase toda fórmula de erro-padrão que você usou até
aqui supôs o contrário.

### 3.2 Sharpe, corrigido de verdade

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 46 | Probabilistic Sharpe Ratio | Qual a chance de o Sharpe verdadeiro superar um alvo? |
| 47 | Minimum Track Record Length | Quanto histórico seria preciso para sustentar isso? |
| 48 | Deflated Sharpe Ratio | O Sharpe resiste a quantos testes foram feitos? |

**O antídoto mais direto contra track record curto.** Um Sharpe de 1,5 em seis meses
pode exigir anos para ser distinguível de zero. MinTRL põe um número nisso.

### 3.3 Seleção e data snooping

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 68 | Probability of Backtest Overfitting | A escolha do IS cai no lado ruim do OOS? |
| 69 | CSCV | O procedimento combinatório que calcula o PBO |
| 70 | White's Reality Check | A melhor regra supera o benchmark após snooping? |
| 71 | Hansen SPA Test | Versão menos conservadora do mesmo teste |
| 72 | Research Trials Count | Quantas chances reais houve de acertar por acaso? |
| 137 | Data-Snooping Audit | Quantas decisões olharam o mesmo histórico? |

> **A métrica mais desconfortável do manual inteiro é o PBO.** Ela não avalia a
> estratégia: avalia o *processo de seleção*. PBO acima de 0,5 significa que escolher
> pelo backtest é pior que escolher no sorteio.

### 3.4 O indicador por dentro

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 82 | Signal Precision | Quando sinaliza, com que frequência acerta? |
| 83 | Signal Recall | Que fração dos eventos captura? |
| 84 | Signal Lift | Quanto melhora sobre a taxa-base? |
| 85 | Conditional Forward Return | Que retorno ocorre depois do sinal? |
| 86 | Signal Decay | Por quanto tempo a informação dura? |
| 87 | Information Coefficient | O score se relaciona com o retorno futuro? |
| 88 | Rank IC | E a ordenação? |
| 89 | IC Information Ratio | O IC é estável no tempo? |
| 90 | Signal Monotonicity | Quantis mais fortes rendem progressivamente mais? |
| 91 | Quantile Analysis | Como a distribuição muda entre quantis? |
| 92 | Signal Coverage | Com que frequência há oportunidade negociável? |
| 93 | Incremental Signal Value | Acrescenta algo além dos filtros existentes? |

**Calibragem que evita vergonha.** Em ações, IC de 0,02 a 0,05 já é um sinal de valor.
Quem mostra IC de 0,40 deve procurar o vazamento de informação antes de procurar a
explicação econômica.

**A pergunta que quase ninguém faz** é a 93. A maioria dos indicadores "novos" é uma
combinação linear dos antigos.

### 3.5 Estabilidade estrutural

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 95 | Regime Dependency Score | Quanto do P&L depende do melhor regime? |
| 101 | Edge Decay | Há deterioração sistemática do edge? |
| 102 | Structural Break Tests | A relação mudou de forma discreta? |

### 3.6 Microestrutura e capacidade

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 123 | Fill Probability | Qual a chance de a ordem limite executar? |
| 124 | Slippage Distribution | Como o slippage varia, além da média? |
| 125 | Participation Rate | Quanto a ordem representa do volume? |
| 126 | Capacity | Quanto capital o sistema absorve? |
| 127 | Capacity-adjusted Return | O que sobra com custos que crescem com o capital? |

**A inversão de seleção que derruba backtests com ordem limite:** você é executado
justamente quando o mercado vai contra.

### 3.7 Integridade avançada

| # | Auditoria | A pergunta em uma linha |
|---|---|---|
| 132 | Same-Bar Ambiguity | Stop e alvo na mesma barra: qual veio primeiro? |
| 133 | Intrabar Path Sensitivity | O resultado muda ao reconstruir o caminho? |
| 134 | Timestamp / Session Integrity | Horários e fusos batem com o mercado real? |
| 135 | Corporate Action / Roll Integrity | Ajustes criam retorno artificial? |

### 3.8 Transferência

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 128 | Cross-Asset Robustness | A lógica transfere sem reotimização agressiva? |
| 129 | Cross-Market Transfer Ratio | Quanto se preserva em outros mercados? |

### 3.9 Governança: do backtest para a conta real

| # | Métrica | A pergunta em uma linha |
|---|---|---|
| 138 | Net Expectancy after All Costs | Depois de tudo, ainda existe edge? |
| 139 | Robustness Pass Rate | Quantos testes *pré-definidos* foram superados? |
| 140 | Reliability Gate | Existe falha que invalida todo o resto? |
| 141 | Composite Reliability Score | Como resumir sem fingir independência? |
| 142 | Live vs Backtest Slippage Gap | A execução real está pior que a modelada? |
| 143 | Live vs Backtest Expectancy Gap | O resultado ao vivo está dentro do previsto? |
| 144 | Model CI Breach Rate | Com que frequência o live sai do intervalo? |
| 145 | Kill-Switch Threshold | Quando reduzir ou suspender? |

> **O ponto final da trilha.** A 141 tem uma armadilha embutida, e o próprio manual a
> sinaliza: um score composto resume dimensões que não são independentes, e resumir é
> exatamente o que faz perder a informação que importa. Use a tabela por gate. O número
> único serve para acompanhar a própria evolução no tempo — nunca para convencer alguém.

---

## Como isso vira post

Cada linha das tabelas acima já é uma pergunta — que é o formato de título que o manual
de marca pede. A conversão é quase direta:

- **Nível 1 → Wizz Concept.** Uma métrica por post, com um gráfico e uma armadilha.
- **Nível 2 → Wizz Data.** Um número da carteira real ou simulada, com a métrica
  explicando o que ele significa.
- **Nível 3 → Wizz Research.** Um teste conduzido, com o resultado que apareceu —
  inclusive quando o resultado for "não deu nada".

O mapa completo de posts, com data e série, está na base **Planejamento Editorial —
Wizz**, no Notion.

---

*Material educacional. Não constitui recomendação individualizada, oferta ou promessa de
retorno.*
