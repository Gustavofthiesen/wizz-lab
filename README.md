<div align="center">

# Wizz Lab

**Validação de estratégias sistemáticas, em código aberto.**

*Processo antes de performance. Evidência antes de confiança.*

[![Python](https://img.shields.io/badge/python-3.10%2B-2F5D50)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-B66A3C)](LICENSE)
[![Métricas](https://img.shields.io/badge/m%C3%A9tricas-153-102A2A)](docs/TRILHA.md)

</div>

---

Este repositório é o companheiro de código do **Manual de Validação de Estratégias
Sistemáticas** da Wizz: 153 métricas que existem para responder uma pergunta só —

> Como distinguir um backtest convincente de uma estratégia realmente robusta?

Não é uma biblioteca de backtest. É o que se faz **depois** que o backtest ficou pronto e
bonito, e antes de acreditar nele.

## Comece por aqui

Quatro notebooks, nesta ordem. Nenhum deles exige instalar nada — abra no Colab e rode.

| | Notebook | A pergunta | |
|---|---|---|---|
| **1** | **O que é um resultado?** <br> 26 métricas, zero estatística inferencial | Retorno é o que aconteceu. Risco é o que quase aconteceu. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Gustavofthiesen/wizz-lab/blob/main/notebooks/01_iniciante.ipynb) |
| **2** | **Esse resultado é confiável?** <br> Forma, incerteza e custo | Uma estimativa não é um fato. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Gustavofthiesen/wizz-lab/blob/main/notebooks/02_intermediario.ipynb) |
| **3** | **Como eu me enganei sem perceber?** <br> Seleção, snooping e diagnóstico do sinal | Este nível é sobre o pesquisador, não sobre a estratégia. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Gustavofthiesen/wizz-lab/blob/main/notebooks/03_avancado.ipynb) |
| **4** | **Validando do zero** <br> Os seis gates, em ordem | Inclusive quando a resposta é "reprovado". | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Gustavofthiesen/wizz-lab/blob/main/notebooks/04_scorecard.ipynb) |

A classificação completa das 153 métricas por nível está em **[docs/TRILHA.md](docs/TRILHA.md)**.

## Instalação

```bash
pip install git+https://github.com/Gustavofthiesen/wizz-lab.git
```

Ou, para mexer no código:

```bash
git clone https://github.com/Gustavofthiesen/wizz-lab.git
cd wizz-lab
pip install -e .
```

## Em trinta segundos

```python
from wizzlab import data, metrics, scorecard

est = data.gerar_estrategia()          # estratégia simulada, semente fixa
r = est.trades.r_multiple.values

metrics.trade.resumo(r)                # capítulo 1 inteiro
metrics.risco.resumo(est.diario)       # risco e sobrevivência
metrics.evidencia.resumo(r)            # quanto disso pode ser sorte

gates = scorecard.avaliar(r, est.diario, integridade={"lookahead": True, ...})
scorecard.veredito(gates)
```

## Os seis gates

A ordem não é decorativa. Integridade e edge líquido são **eliminatórios**: um FAIL ali
invalida tudo o que vem depois, e o score composto vai a zero.

| Gate | Pergunta | Elimina? |
|---|---|---|
| **0** | Sem lookahead, repaint, survivorship ou fills impossíveis? | **Sim** |
| **1** | Existe expectancy positiva depois de custos conservadores? | **Sim** |
| **2** | Quanto disso pode ser sorte? | Não |
| **3** | Sobrevive fora da amostra e à perturbação? | Não |
| **4** | Dá para aguentar o pior caminho plausível? | Não |
| **5** | Sobrevive ao mercado real? | Não |

## O que tem dentro

```
wizzlab/
├── brand.py            tokens da marca: cor, tipografia, bloco de transparência
├── theme.py            tema matplotlib — todo gráfico já nasce no padrão
├── charts.py           as figuras do Apêndice B do manual
├── cards.py            gerador de cards 1080×1350 para o Instagram
├── data.py             geradores didáticos, reprodutíveis por semente
├── scorecard.py        os seis gates, combinados sem fingir independência
├── palette_check.py    validador de paleta (contraste, CVD, croma)
└── metrics/
    ├── trade.py            1–14    economia do trade
    ├── risco.py            15–42   qualidade, drawdown, sobrevivência
    ├── evidencia.py        43–62   incerteza, bootstrap, Monte Carlo
    ├── generalizacao.py    63–81   OOS, walk-forward, PBO, robustez
    ├── sinal.py            82–107  diagnóstico do indicador, estabilidade
    └── execucao.py         108–153 custos, liquidez, integridade, governança
```

## Três coisas que este repositório leva a sério

**1. Dados simulados, e isso é uma escolha pedagógica.** Quando você define o processo
gerador, sabe qual é a resposta certa e pode conferir se a métrica a encontra. O gerador
padrão tem expectancy verdadeira de ~+0,22R e, em 420 trades, **não atinge significância**
— que é o tamanho de amostra que a maioria dos backtests tem. Nenhum dado de carteira real
entra aqui.

**2. O score composto tem um aviso colado nele.** Ele resume dimensões que não são
independentes, e resumir é o que faz perder a informação que importa. Serve para
acompanhar a própria evolução. Nunca para convencer alguém.

**3. A paleta foi medida, não escolhida no olho.** O manual de marca proíbe cores
saturadas, o que limita quantas séries dá para distinguir só por cor. A consequência está
implementada: **duas séries por cor, no máximo**, sempre com rótulo direto, e sálvia
reservado para grade e metadado. `palette_check.py` roda as verificações (banda de
luminosidade, piso de croma, separação para daltonismo, contraste) e documenta o desvio
que a marca impõe.

```bash
python -m wizzlab.palette_check "#2F5D50,#B66A3C" --surface "#F3EFE5" --pairs all
```

## Aviso

Material **educacional** e de pesquisa quantitativa. Não constitui recomendação
individualizada, oferta ou promessa de retorno. Premissas podem estar erradas e resultados
passados não garantem resultados futuros.

Algumas métricas — Sterling, Burke, MAR, Gain-to-Pain, eficiência de entrada e saída — têm
convenções diferentes entre autores e plataformas. As fórmulas usadas aqui estão nas
docstrings. Declare a sua ao comparar com outra fonte.

## Referências

Lo (2002) · Bailey & López de Prado (2012, 2014) · Bailey, Borwein, López de Prado & Zhu
(2017) · White (2000) · Hansen (2005) · Politis & Romano (1994) · Martin & McCann · Van
Tharp

---

<div align="center">

**WIZZ** · Valuation & Alocação

*Uma estratégia não precisa parecer infalível. Precisa ser rastreável, coerente e
intelectualmente honesta.*

</div>
