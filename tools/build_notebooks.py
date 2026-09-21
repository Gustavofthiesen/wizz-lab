"""Gera os notebooks da trilha a partir deste script.

Os notebooks são artefatos de build, não fonte. Editar aqui e rodar
``python tools/build_notebooks.py`` mantém os quatro consistentes entre si --
mesma abertura, mesmo aviso educacional, mesma célula de setup para o Colab.
"""
from __future__ import annotations

import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "notebooks"
REPO = "https://github.com/Gustavofthiesen/wizz-lab"


def md(texto: str) -> dict:
    return {"cell_type": "markdown", "metadata": {},
            "source": texto.strip("\n").splitlines(keepends=True)}


def code(texto: str) -> dict:
    corpo = texto.strip("\n")
    # Uma célula que só atribui `fig, ax = ...` não exibe nada no notebook.
    # Fechar com `fig` faz o Jupyter renderizar a figura como saída da célula.
    if "fig, ax = charts." in corpo and not corpo.rstrip().endswith("fig"):
        corpo += "\nfig"
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": corpo.splitlines(keepends=True)}


SETUP = code(f"""
%matplotlib inline

# No Colab, instala o pacote direto do GitHub. Localmente, não faz nada.
import importlib.util, subprocess, sys

if importlib.util.find_spec("wizzlab") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "git+{REPO}.git"], check=True)

from wizzlab import brand, data, metrics, scorecard
from wizzlab.theme import aplicar_tema
from wizzlab import charts

aplicar_tema()
print("Wizz Lab pronto · paleta:", brand.SERIE_PRINCIPAL, brand.SERIE_COMPARACAO)
""")

RODAPE = md("""
---

### Bloco de transparência

**Natureza:** educacional · **Dados:** simulados e reprodutíveis por semente ·
**Código:** aberto em [wizz-lab](%s)

Este material apresenta um processo de estudo, com finalidade educacional. Não
constitui recomendação individualizada, oferta ou promessa de retorno. Premissas podem
estar erradas e resultados passados não garantem resultados futuros.
""" % REPO)


def cabecalho(titulo: str, nivel: str, pergunta: str, conteudo: str) -> dict:
    return md(f"""
# {titulo}

**Nível {nivel}** · Trilha Wizz Lab

> {pergunta}

{conteudo}

---
""")


# =============================================================================
NB1 = [
    cabecalho(
        "O que é um resultado?", "1 — Iniciante",
        "Retorno é o que aconteceu. Risco é o que poderia ter acontecido e quase aconteceu.",
        """
Este notebook percorre as 26 métricas do nível iniciante. Nenhuma delas usa estatística
inferencial — é aritmética honesta.

A ideia que precisa ficar ao final: **retorno sozinho não é resultado.**
"""),
    SETUP,
    md("""
## 1. Uma estratégia para estudar

Todos os dados aqui são simulados, e isso é uma vantagem pedagógica, não uma limitação:
como nós escolhemos o processo gerador, sabemos qual é a resposta certa e podemos
conferir se a métrica de fato a encontra.

Por construção, esta estratégia tem **win rate de 42% e payoff de 1,9**.
"""),
    code("""
est = data.gerar_estrategia(semente=42)
r = est.trades.r_multiple.values      # resultado de cada trade, em R
est
"""),
    md("""
## 2. Win rate: a métrica mais mal usada do mercado

Win rate mede **frequência**, não qualidade. Uma estratégia pode ganhar dinheiro
acertando 30% das vezes, e perder acertando 80%.

O que decide não é o acerto isolado — é o acerto **comparado ao payoff**.
"""),
    code("""
wr = metrics.trade.win_rate(r)
payoff = metrics.trade.payoff_ratio(r)
be = metrics.trade.break_even_win_rate(r)

print(f"Win rate observado ....... {wr:.1%}")
print(f"Payoff (ganho/perda) ..... {payoff:.2f}x")
print(f"Win rate de equilíbrio ... {be:.1%}")
print(f"Margem de edge ........... {wr - be:+.1%}")
"""),
    md("""
Acertar 42% das vezes parece ruim. Com payoff de 1,4x, o equilíbrio está em ~41% — então
42% é apenas *um pouco* melhor que empatar.

**Essa margem de poucos pontos percentuais é exatamente a que desaparece com custos.**
Guarde este número: vamos voltar a ele no nível 2.
"""),
    code("""
metrics.trade.resumo(r).round(3)
"""),
    md("""
## 3. Média e mediana: quem sustenta o resultado?

A distância entre média e mediana é um diagnóstico direto. Se a média é muito maior que a
mediana, poucos trades excepcionais estão carregando o conjunto.
"""),
    code("""
fig, ax = charts.distribuicao_trades(r, fonte="Dados simulados · wizz-lab")
"""),
    md("""
A mediana é negativa e a média é positiva. Isso **não é necessariamente ruim**: é o perfil
clássico de um sistema que corta perdas e deixa ganhos correrem. Mas é uma escolha, e
precisa ser consciente — significa depender da cauda direita.
"""),
    md("""
## 4. O preço que a estratégia cobrou

Agora a outra metade do resultado. A curva de capital mostra o destino; o drawdown mostra
o caminho.
"""),
    code("""
bench = data.gerar_benchmark(est)
fig, ax = charts.curva_capital(est.diario, bench,
                               fonte="Dados simulados · wizz-lab")
"""),
    code("""
fig, ax = charts.drawdown(est.diario, fonte="Dados simulados · wizz-lab")
"""),
    code("""
print(f"Queda máxima ............. {metrics.risco.max_drawdown(est.diario):.1%}")
print(f"Queda média .............. {metrics.risco.average_drawdown(est.diario):.1%}")
print(f"Tempo abaixo do pico ..... {metrics.risco.time_under_water(est.diario):.0%} do período")

episodios = metrics.risco.episodios_drawdown(est.diario)
episodios.head(5)
"""),
    md("""
**Profundidade e duração são riscos diferentes.** Uma queda de 15% que dura três anos
costuma ser mais difícil de aguentar que uma de 25% que dura dois meses — e só a segunda
aparece bem em qualquer ranking de performance.
"""),
    md("""
## 5. Juntando as duas metades

Os ratios de risco-retorno existem para responder uma pergunta só: **quanto retorno por
unidade de incômodo?** O que muda entre eles é a definição de incômodo.

- **Sharpe** — incômodo é oscilação (para os dois lados)
- **Sortino** — incômodo é oscilação só para baixo
- **Calmar** — incômodo é a queda máxima
"""),
    code("""
metrics.risco.resumo(est.diario).round(3)
"""),
    md("""
### A armadilha do Sharpe

Sharpe é tratado como nota de prova, e não é. Ele supõe que **volatilidade mede risco** —
o que deixa de valer quando a distribuição tem cauda esquerda pesada.

Sharpe alto com assimetria muito negativa é um alerta, não um elogio. Veremos como medir
isso no nível 2.
"""),
    md("""
## 6. Comparar com o quê?

Um retorno sem referência não significa nada. O manual de marca é explícito: comparar
sempre **no mesmo período** e com referência adequada.
"""),
    code("""
metrics.execucao.beta_e_alfa(est.diario.values, bench.values).round(4)
"""),
    md("""
O `beta` diz quanto do resultado é simplesmente estar comprado. O `excesso_por_periodo` é
o que sobra depois disso — e o `t_excesso` já antecipa a pergunta do nível 2: **esse
excesso é grande o suficiente frente ao erro de medição?**
"""),
    md("""
## 7. A operação no tempo

O diagnóstico comportamental mais direto, e o que não precisa de estatística nenhuma.
"""),
    code("""
print("Trades por ano:", round(metrics.execucao.trades_por_ano(est.trades), 1))
print()
print(metrics.execucao.holding_period(est.trades).round(1).to_string())
print()
print(metrics.execucao.winner_vs_loser_holding(est.trades).round(1).to_string())
"""),
    md("""
**Se as perdas ficassem abertas mais tempo que os ganhos**, o sistema estaria realizando
lucro cedo e carregando prejuízo esperando voltar. É o viés de disposição, visível em
duas linhas de código.

---

## O que levar deste nível

1. Win rate sozinho não diz nada. Leia sempre com payoff e break-even.
2. Média e mediana contam histórias diferentes sobre quem sustenta o resultado.
3. Profundidade e duração de queda são riscos distintos.
4. Sharpe supõe que volatilidade é risco. Nem sempre é.
5. Retorno sem benchmark e sem período declarado não é informação.

**No nível 2:** todos esses números são estimativas com incerteza em volta — e quase
nenhum sobrevive inteiro depois dos custos.
"""),
    RODAPE,
]

# =============================================================================
NB2 = [
    cabecalho(
        "Esse resultado é confiável?", "2 — Intermediário",
        "Uma estimativa não é um fato. Todo número do nível 1 tem um intervalo em volta.",
        """
Três ideias novas: a **forma** da distribuição, a **incerteza** da estimativa e o
**custo**.
"""),
    SETUP,
    code("""
est = data.gerar_estrategia(semente=42)
r = est.trades.r_multiple.values
print(f"Expectancy observada: {metrics.trade.expectancy(r):+.3f}R em {len(r)} trades")
"""),
    md("""
## 1. O edge é um intervalo, não um ponto

Aquele `+0,08R por trade` do nível 1 é uma estimativa feita sobre uma amostra finita.
Reamostrando os próprios trades com reposição (*bootstrap*), vemos que faixa de valores
os dados realmente suportam.
"""),
    code("""
fig, ax = charts.intervalo_bootstrap(r, fonte="Dados simulados · wizz-lab")
"""),
    code("""
lo, hi = metrics.evidencia.bootstrap_ci(r)
print(f"Expectancy observada .. {metrics.trade.expectancy(r):+.3f}R")
print(f"IC 95% ................ [{lo:+.3f}R ; {hi:+.3f}R]")
print(f"P(edge > 0) ........... {metrics.evidencia.prob_expectancy_positiva(r):.1%}")
print(f"t-stat ................ {metrics.evidencia.t_stat(r):.2f}")
"""),
    md("""
> **Aqui está a lição central do notebook.** Esta estratégia tem, por construção, uma
> expectancy verdadeira de aproximadamente **+0,22R** — um edge real e economicamente
> relevante. Ainda assim, com 420 trades, o intervalo de confiança **cruza o zero**.
>
> Não é defeito do gerador. É o tamanho de amostra que a maioria dos backtests tem.

Aumente a amostra e veja o mesmo processo virar significativo:
"""),
    code("""
grande = data.gerar_estrategia(n_trades=3000, semente=42)
rg = grande.trades.r_multiple.values
lo2, hi2 = metrics.evidencia.bootstrap_ci(rg)

print(f"420 trades  → t = {metrics.evidencia.t_stat(r):5.2f}   IC [{lo:+.3f} ; {hi:+.3f}]")
print(f"3000 trades → t = {metrics.evidencia.t_stat(rg):5.2f}   IC [{lo2:+.3f} ; {hi2:+.3f}]")
"""),
    md("""
Mesmo processo gerador. Mesma expectancy verdadeira. **A diferença é só quanta evidência
existe** — e é por isso que "a estratégia funciona" e "eu consigo demonstrar que a
estratégia funciona" são afirmações diferentes.
"""),
    md("""
## 2. A forma da distribuição

Média e desvio não descrevem uma distribuição assimétrica. Faltam a assimetria e as
caudas.
"""),
    code("""
import pandas as pd
pd.Series({
    "Skewness": metrics.trade.skewness(r),
    "Excess kurtosis": metrics.trade.excess_kurtosis(r),
    "Tail ratio": metrics.trade.tail_ratio(r),
    "IQR": metrics.trade.iqr(r),
    "MAD": metrics.trade.mad(r),
}).round(3)
"""),
    md("""
Skew positivo = cauda direita = o perfil de quem aceita muitas perdas pequenas em troca
de poucos ganhos grandes.

O padrão **perigoso** é o inverso: Sharpe alto com skew fortemente negativo. Significa
ganhos pequenos e constantes com uma perda enorme que ainda não aconteceu no período
medido.
"""),
    md("""
## 3. Risco de cauda: onde a cauda começa e o que há dentro dela
"""),
    code("""
pd.Series({
    "VaR 5% (diário)": metrics.risco.var_historico(est.diario),
    "Expected Shortfall 5%": metrics.risco.expected_shortfall(est.diario),
    "Maior sequência de perdas": metrics.risco.max_streak(r),
    "Kelly fraction": metrics.risco.kelly_fraction(r),
    "Risk of ruin (perder 50%)": metrics.risco.risk_of_ruin(r, fracao_por_trade=0.01),
}).round(4)
"""),
    md("""
**VaR e Expected Shortfall formam um par que ensina sozinho.** O VaR diz onde a cauda
ruim começa; o ES diz qual é a perda média *dentro* dela. Quem reporta só o primeiro está
escondendo o segundo.

Sobre Kelly: é um teto teórico, não uma recomendação. Ele supõe que a distribuição
estimada está certa — e ela nunca está. Kelly cheio sobre parâmetros estimados produz
drawdowns intoleráveis.
"""),
    md("""
## 4. Monte Carlo: o histórico foi só um dos caminhos possíveis
"""),
    code("""
fig, ax = charts.monte_carlo(r, fonte="Dados simulados · wizz-lab")
"""),
    code("""
mdd_obs = metrics.risco.max_drawdown(est.diario)
fig, ax = charts.distribuicao_mdd(r, mdd_observado=mdd_obs,
                                  fonte="Dados simulados · wizz-lab")
"""),
    code("""
metrics.risco.monte_carlo_mdd(r).round(3)
"""),
    md("""
> **A figura que muda decisão de sizing.** O drawdown observado fica bem à direita da
> distribuição — ou seja, o histórico foi sortudo. Quem dimensiona posição pelo MDD
> observado está dimensionando pela sorte.
>
> O número que importa para o sizing é o **P95**, não o observado.
""" ),
    md("""
## 5. Custo: o assassino silencioso

Lembra da margem de 3 pontos percentuais sobre o break-even, do nível 1?
"""),
    code("""
metrics.execucao.slippage_sensitivity(r, custos=(0.0, 0.05, 0.10, 0.20, 0.40)).round(3)
"""),
    code("""
print(f"Custo que zera o edge ..... {metrics.execucao.break_even_cost(r):.3f}R")
print(f"Margem sobre custo de 0,05R {metrics.execucao.cost_safety_margin(r, 0.05):.2f}x")
"""),
    md("""
**O que observar não é o nível de cada linha — é a inclinação.** Uma estratégia cujo edge
cai pela metade com 0,05R de custo extra não existe fora do backtest.

Abaixo de 2x de margem eu não dormiria tranquilo: qualquer alargamento de spread ou
mudança de corretagem come a folga.
"""),
    md("""
## 6. Fora da amostra, pela primeira vez

Todo número até aqui foi calculado sobre os mesmos dados que escolheram as regras. Hora de
separar.
"""),
    code("""
print(f"Retenção OOS/IS ........... {metrics.generalizacao.oos_is_ratio(r):.2f}")
print(f"Walk-forward efficiency ... {metrics.generalizacao.walk_forward_efficiency(r):.2f}")
print(f"Janelas OOS positivas ..... {metrics.generalizacao.positive_oos_windows(r):.0%}")
print()
metrics.generalizacao.walk_forward(r, n_janelas=6).round(4)
"""),
    md("""
Nunca divida uma série temporal aleatoriamente: isso vaza o futuro para o treino. A
divisão é sempre **na ordem do tempo**.
"""),
    md("""
## 7. Robustez: o ótimo é um platô ou um pico?
"""),
    code("""
import numpy as np
# Superfície simulada: um platô largo e suave é o que se quer ver.
eixo_a, eixo_b = np.arange(24), np.arange(20)
superficie = np.add.outer(np.exp(-np.linspace(-2, 2, 20) ** 2 / 2.0),
                          np.exp(-np.linspace(-2, 2, 24) ** 2 / 1.4))
fig, ax = charts.superficie_parametros(superficie, eixo_a, eixo_b,
                                       rotulo_x="janela do indicador",
                                       rotulo_y="limiar de entrada",
                                       fonte="Superfície simulada · wizz-lab")
"""),
    code("""
resultados = pd.Series(superficie.mean(axis=0), index=eixo_a)
print(metrics.generalizacao.parameter_stability(resultados).round(3).to_string())
print()
print("Largura do platô (>=90% do ótimo):",
      f"{metrics.generalizacao.parameter_plateau_width(resultados):.0%}")
"""),
    md("""
**Regiões largas e suaves convencem; picos estreitos, não.** Um ótimo isolado cercado de
resultados ruins é quase sempre ruído que foi escolhido depois do fato.
"""),
    md("""
## 8. Concentração: quantas apostas existem de verdade?
"""),
    code("""
fig, ax = charts.concentracao_pnl(r, fonte="Dados simulados · wizz-lab")
"""),
    code("""
print(metrics.sinal.pnl_concentration(r).round(3).to_string())
print()
print(metrics.sinal.remove_best_trades(r, n=5).to_string())
print()
print("Nº efetivo de ativos (breadth):",
      round(metrics.sinal.breadth(r, est.trades.ativo), 2))
"""),
    md("""
Se remover cinco trades de 420 zera o edge, a estratégia depende de **eventos**, não de um
processo. E dez ativos dos quais um responde por 80% do lucro não são dez apostas.

---

## O que levar deste nível

1. Toda métrica é uma estimativa. Reporte o intervalo, não o ponto.
2. Um edge real pode não ser demonstrável com a amostra que você tem.
3. VaR diz onde a cauda começa; ES diz o que há dentro dela.
4. Dimensione pelo MDD simulado P95, não pelo observado.
5. Na sensibilidade a custo, olhe a inclinação, não o nível.
6. Platô largo convence; pico estreito não.

**No nível 3:** tudo isso ainda supõe que você testou uma estratégia. E se você testou
duzentas e mostrou a melhor?
"""),
    RODAPE,
]

# =============================================================================
NB3 = [
    cabecalho(
        "Como eu me enganei sem perceber?", "3 — Avançado",
        "Este nível inteiro é sobre o pesquisador, não sobre a estratégia.",
        """
Ele mede o efeito de ter testado muitas coisas, de ter olhado o mesmo histórico muitas
vezes e de ter parado de procurar quando o resultado ficou bonito.
"""),
    SETUP,
    code("""
import numpy as np, pandas as pd
est = data.gerar_estrategia(semente=42)
r = est.trades.r_multiple.values
"""),
    md("""
## 1. Quantas observações você tem de verdade?

Quase toda fórmula de erro-padrão supõe independência. Se os resultados forem
autocorrelacionados, os intervalos ficam estreitos demais — e você se convence sem motivo.
"""),
    code("""
print(f"N bruto ................. {len(r)}")
print(f"N efetivo ............... {metrics.evidencia.effective_sample_size(r):.0f}")
print(f"t-stat ingênuo .......... {metrics.evidencia.t_stat(r):.2f}")
print(f"t-stat Newey-West (HAC) . {metrics.evidencia.newey_west_t(r):.2f}")
q, p = metrics.evidencia.ljung_box(r)
print(f"Ljung-Box Q = {q:.2f}, p = {p:.3f}")
"""),
    md("""
Nestes dados simulados a autocorrelação é fraca, então os dois t batem. **Em dados reais
raramente batem** — e quando o t despenca ao corrigir, o t ingênuo estava contando a mesma
informação várias vezes.

O bootstrap também precisa respeitar a dependência:
"""),
    code("""
for nome, fn in [("iid", metrics.evidencia.iid_bootstrap),
                 ("moving block", metrics.evidencia.moving_block_bootstrap),
                 ("stationary", metrics.evidencia.stationary_bootstrap)]:
    v = fn(r, n_boot=3000)
    print(f"{nome:14} → IC 95% [{np.quantile(v, .025):+.3f} ; {np.quantile(v, .975):+.3f}]")
"""),
    md("""
## 2. Sharpe, corrigido de verdade

O Sharpe bruto ignora assimetria, curtose e — sobretudo — quantas vezes você tentou.
"""),
    code("""
sr_diario = metrics.risco.sharpe(est.diario) / np.sqrt(252)
n = len(est.diario)
skew = metrics.trade.skewness(est.diario)
kurt = metrics.trade.excess_kurtosis(est.diario) + 3

psr = metrics.evidencia.probabilistic_sharpe(sr_diario, n, skew, kurt)
mintrl = metrics.evidencia.min_track_record_length(sr_diario, skew, kurt)

print(f"Sharpe anualizado ......... {metrics.risco.sharpe(est.diario):.2f}")
print(f"PSR (P[Sharpe real > 0]) .. {psr:.1%}")
print(f"MinTRL .................... {mintrl:,.0f} pregões  (~{mintrl/252:.1f} anos)")
"""),
    md("""
**MinTRL é o antídoto mais direto contra track record curto.** Ele responde: quanto
histórico seria preciso para sustentar este Sharpe com 95% de confiança?

Agora o Deflated Sharpe — que desconta o fato de você ter testado várias configurações:
"""),
    code("""
for n_trials in (1, 10, 50, 200):
    dsr = metrics.evidencia.deflated_sharpe(sr_diario, n, max(n_trials, 2),
                                            var_sharpes=0.0004, skew=skew, kurt=kurt)
    print(f"{n_trials:4d} tentativas → DSR = {dsr:.1%}")
"""),
    md("""
O mesmo Sharpe. A mesma estratégia. **O que muda é quantas vezes você procurou** — e isso
muda a conclusão.
"""),
    md("""
## 3. PBO: a métrica mais desconfortável do manual

Ela não avalia a estratégia. Avalia o **processo de seleção**.

Vamos gerar 40 configurações que são **puro ruído** — nenhuma tem edge — e perguntar o que
acontece se escolhermos a melhor pelo backtest.
"""),
    code("""
rng = np.random.default_rng(0)
ruido_puro = rng.normal(0, 1, size=(600, 40))   # 600 períodos, 40 configurações

melhor = int(np.argmax(ruido_puro.mean(axis=0)))
print(f"Melhor configuração no IS: #{melhor}, "
      f"retorno médio {ruido_puro[:, melhor].mean():+.4f}")
print(f"PBO (CSCV): {metrics.generalizacao.pbo_cscv(ruido_puro):.2f}")
"""),
    md("""
Testando 40 coisas sem valor nenhum, alguma parece boa. O PBO próximo de 0,5 diz
exatamente isso: **escolher pelo backtest não é melhor que sortear.**

E o Reality Check confirma pelo outro lado:
"""),
    code("""
print(f"White's Reality Check, p = {metrics.generalizacao.reality_check(ruido_puro):.3f}")
print(f"Hansen SPA, p ............. {metrics.generalizacao.hansen_spa(ruido_puro):.3f}")
"""),
    md("""
p alto = a melhor regra encontrada é compatível com o que se acharia testando N regras sem
valor nenhum.

> **O corolário prático:** registre quantas configurações você testou. Sem esse número,
> nenhuma dessas correções funciona — e é por isso que o manual trata *Research Trials
> Count* como métrica, não como burocracia.
"""),
    md("""
## 4. O indicador por dentro

Até aqui avaliamos a estratégia pronta. Agora o sinal que a alimenta — são coisas
diferentes, e separá-las evita consertar a peça errada.
"""),
    code("""
sinal_df = data.gerar_sinal(n=3000, ic_verdadeiro=0.045, semente=11)

print(f"IC (Pearson) .......... {metrics.sinal.information_coefficient(sinal_df.score, sinal_df.retorno_futuro):.4f}")
print(f"Rank IC (Spearman) .... {metrics.sinal.rank_ic(sinal_df.score, sinal_df.retorno_futuro):.4f}")
print(f"Monotonicidade ........ {metrics.sinal.signal_monotonicity(sinal_df.score, sinal_df.retorno_futuro):+.2f}")
"""),
    code("""
fig, ax = charts.quantis_sinal(sinal_df.score, sinal_df.retorno_futuro,
                               fonte="Sinal simulado com IC = 0,045 · wizz-lab")
"""),
    md("""
**Calibragem que evita vergonha:** em ações, IC de 0,02 a 0,05 já é um sinal de valor.
Quem mostra IC de 0,40 deve procurar o vazamento de informação antes de procurar a
explicação econômica.

E note quanta amostra foi preciso (3000 observações) para que um IC de 0,045 produzisse
uma progressão de quantis visível.
"""),
    code("""
decay = pd.Series({1: 0.048, 3: 0.041, 5: 0.030, 10: 0.018, 21: 0.006, 42: -0.002})
fig, ax = charts.signal_decay(decay, fonte="Sinal simulado · wizz-lab")
"""),
    md("""
O horizonte de maior retorno condicional indica a **meia-vida do sinal**. Um pico isolado
em um horizonte estranho merece suspeita, não comemoração.
"""),
    md("""
## 5. A pergunta que quase ninguém faz

O indicador novo acrescenta algo **além** dos filtros que já existem? A maioria dos
indicadores "novos" é uma combinação linear dos antigos.
"""),
    code("""
rng = np.random.default_rng(3)
antigo_a = sinal_df.score.values
antigo_b = rng.normal(0, 1, len(sinal_df))
# Um "novo" indicador que é 85% o antigo A disfarçado:
novo = 0.85 * antigo_a + 0.15 * rng.normal(0, 1, len(sinal_df))

metrics.sinal.incremental_signal_value(
    novo, [antigo_a, antigo_b], sinal_df.retorno_futuro.values).round(4)
"""),
    md("""
IC bruto respeitável, IC incremental perto de zero. O indicador "novo" não trouxe
informação nova — trouxe a informação antiga com outro nome.
"""),
    md("""
## 6. Estabilidade: o edge está morrendo?
"""),
    code("""
fig, ax = charts.rolling(est.diario, janela=252,
                         titulo="O edge persiste ou é episódico?",
                         subtitulo="Retorno médio diário em janela de 252 pregões",
                         fonte="Dados simulados · wizz-lab")
"""),
    code("""
print(metrics.sinal.edge_decay(est.diario).round(6).to_string())
print()
print(metrics.sinal.rolling_stability(est.diario).round(5).to_string())
print()
print("Dependência do melhor regime:",
      f"{metrics.sinal.regime_dependency_score(est.trades.r_multiple, est.trades.regime):.1%}")
"""),
    md("""
Se o P&L depende demais de um regime, você não tem uma estratégia — tem uma aposta em um
regime. O que não é necessariamente errado, desde que esteja declarado.

---

## O que levar deste nível

1. N bruto não é N efetivo. Corrija por dependência antes de acreditar no t.
2. MinTRL põe um número em "esse track record é curto demais".
3. O DSR desconta quantas vezes você tentou — então **conte as tentativas**.
4. PBO acima de 0,5: escolher pelo backtest é pior que sortear.
5. IC de 0,02–0,05 já é sinal. IC de 0,40 é vazamento.
6. Pergunte sempre o valor **incremental** de um indicador novo.

**No notebook 4:** tudo isso junto, em ordem, como scorecard.
"""),
    RODAPE,
]

# =============================================================================
NB4 = [
    cabecalho(
        "Validando uma estratégia do zero", "4 — Prática",
        "Processo antes de performance. Evidência antes de confiança.",
        """
Os seis gates do manual, aplicados em ordem a uma estratégia — inclusive quando a resposta
é "reprovado".
"""),
    SETUP,
    md("""
## A ordem importa

Antes de olhar Sharpe, Calmar ou CAGR, integridade e edge líquido são gates
**eliminatórios**.

| Gate | O que responde | Elimina? |
|---|---|---|
| 0 | Integridade do backtest | **Sim** |
| 1 | Edge econômico líquido | **Sim** |
| 2 | Evidência estatística | Não |
| 3 | Generalização | Não |
| 4 | Sobrevivência | Não |
| 5 | Execução | Não |
"""),
    code("""
import pandas as pd
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 60)

est = data.gerar_estrategia(semente=42)
r = est.trades.r_multiple.values
"""),
    md("""
## Gate 0 — as auditorias que você precisa ter feito

Estas não são fórmulas: são verificações. Cada `True` abaixo é uma afirmação sua sobre o
próprio backtest, e o gate só faz sentido se você foi honesto ao preenchê-lo.

**Não auditado conta como reprovado** — de propósito.
"""),
    code("""
auditorias = {
    "lookahead": True,          # nenhuma decisão usou informação futura
    "repainting": True,         # o indicador histórico não muda
    "same_bar": True,           # ambiguidade stop/alvo resolvida conservadoramente
    "intrabar": True,           # caminhos intrabar testados
    "timestamp": True,          # fusos e sessões conferidos
    "corporate_action": True,   # ajustes e rolagens verificados
    "survivorship": True,       # universo inclui quem desapareceu
    "data_snooping": False,     # <- ainda não registramos as tentativas
}
metrics.execucao.auditoria_integridade(auditorias)
"""),
    md("""
## Rodando os seis gates
"""),
    code("""
gates = scorecard.avaliar(
    r_multiples=r,
    retornos_diarios=est.diario,
    custo_esperado=0.05,
    integridade=auditorias,
    mdd_tolerado=-0.30,
)
scorecard.tabela(gates)
"""),
    code("""
scorecard.veredito(gates)
"""),
    code("""
fig, ax = charts.gates(gates, fonte="Dados simulados · wizz-lab")
"""),
    md("""
## Lendo o veredito

O Gate 0 reprovou por uma razão só: não registramos quantas configurações foram testadas.
Isso basta para invalidar tudo que vem depois — e é assim que deve ser. Um backtest cujo
processo de pesquisa não foi rastreado não tem como ser defendido.

Note também que o **score composto vai a zero** quando um gate eliminatório reprova:
"""),
    code("""
print("Score composto:", scorecard.composite_reliability_score(gates))
"""),
    md("""
> **Por que zero e não uma média ponderada.** Porque uma média deixaria o Gate 4 excelente
> compensar o Gate 0 reprovado — e não compensa. O manual é explícito ao pedir que um
> score composto não finja independência entre dimensões.
>
> Este número serve para acompanhar a própria evolução no tempo. **Nunca para convencer
> alguém.**
"""),
    md("""
## Corrigindo e rodando de novo

Vamos supor que você registrou as tentativas (foram 12, todas de uma família só) e pode
marcar a auditoria como feita.
"""),
    code("""
registro = [{"familia": "janela do indicador", "valor": v} for v in range(1, 13)]
print(metrics.generalizacao.research_trials(registro).to_string())

auditorias["data_snooping"] = True
gates = scorecard.avaliar(r, est.diario, custo_esperado=0.05,
                          integridade=auditorias, mdd_tolerado=-0.30)
scorecard.veredito(gates)
"""),
    md("""
Gate 0 passa — e agora o Gate 1 vira o bloqueio. A margem de segurança de custo está
abaixo de 2x e o profit factor abaixo de 1,20.

**Esse é o desfecho mais comum de uma validação séria, e não é um fracasso.** É a
informação de que a estratégia, como está, não tem folga para o mundo real. As saídas são
reduzir custo, aumentar o edge por trade ou reduzir o giro — não afrouxar o critério.
"""),
    md("""
## O checklist final do manual

Quando eu começaria a confiar? Não é preciso que a estratégia seja perfeita. É preciso que
as explicações alternativas tenham sido tratadas de forma explícita.
"""),
    code("""
checklist = {
    "Sem lookahead, repaint, survivorship e ambiguidade de execução": True,
    "Expectancy líquida positiva após custos conservadores": True,
    "Bootstrap mostra que o edge não é um ponto frágil": False,
    "N efetivo suficiente e dependência tratada": True,
    "OOS e walk-forward preservam parcela útil do edge": False,
    "PBO/DSR e trials não sugerem seleção excessiva": True,
    "Parâmetros formam platôs e resistem a perturbações": True,
    "O indicador mostra informação por quantis, IC ou forward returns": True,
    "Monte Carlo produz MDD e streaks compatíveis com o sizing": False,
    "Custos, fills, turnover e capacidade viáveis": False,
    "Live/forward test dentro das distribuições previstas": False,
}
print(f"Aprovação: {metrics.generalizacao.robustness_pass_rate(checklist):.0%}")
for item, ok in checklist.items():
    print(f"  [{'x' if ok else ' '}] {item}")
"""),
    md("""
---

## O princípio final

> Uma estratégia não precisa parecer infalível. Precisa ser rastreável, coerente e
> intelectualmente honesta.

O que este notebook faz não é aprovar ou reprovar. É **deixar registrado** o que foi
testado, o que passou e o que não passou — para que a conversa seja sobre evidência, e não
sobre convicção.
"""),
    RODAPE,
]


def escrever(nome: str, celulas: list[dict]) -> None:
    nb = {
        "cells": celulas,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
            "colab": {"provenance": [], "toc_visible": True},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    caminho = DESTINO / nome
    caminho.write_text(json.dumps(nb, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    print(f"escrito: {caminho.relative_to(RAIZ)}  ({len(celulas)} células)")


if __name__ == "__main__":
    DESTINO.mkdir(exist_ok=True)
    escrever("01_iniciante.ipynb", NB1)
    escrever("02_intermediario.ipynb", NB2)
    escrever("03_avancado.ipynb", NB3)
    escrever("04_scorecard.ipynb", NB4)
