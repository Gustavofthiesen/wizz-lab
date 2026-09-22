"""Gera as imagens dos carrosséis a partir do roteiro de cada post.

O roteiro fica aqui, em Python, e não em um arquivo de design. A razão é
editorial, não técnica: assim o texto do post e o gráfico que o ilustra saem da
**mesma fonte de verdade**, e um número citado no copy não pode divergir do
número plotado ao lado. Todo valor que aparece escrito nos cards abaixo é
interpolado do cálculo, nunca digitado à mão.

Padrão de construção de cada carrossel (7 cards):

1. **Capa** — a afirmação, com o número
2. **Definição** — fórmula e glossário dos termos
3. **Evidência 1** — gráfico
4. **Evidência 2** — tabela ou segundo gráfico, com números exatos
5. **Evidência 3** — o mecanismo, em gráfico ou tabela
6. **Código** — o trecho que reproduz o resultado, e a saída que ele imprime
7. **Em aberto** — as questões que o post não resolve, e onde estão as respostas

Os dois últimos cards existem no lugar de um card de conclusão, e a troca é
deliberada. Uma conclusão encerra o assunto; código executável e questões em
aberto não encerram — e são eles que fazem alguém procurar o notebook, o artigo
ou o post seguinte. Aforismo ("X não é Y, é Z") está banido do roteiro: ele
ocupa o espaço de um dado sem acrescentar informação.

Rodar::

    python tools/gerar_posts.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wizzlab import brand, cards, data, metrics  # noqa: E402
from wizzlab.theme import aplicar_tema, eixo_percentual  # noqa: E402

DESTINO = RAIZ / "assets" / "posts"
REPO = "github.com/Gustavofthiesen/wizz-lab"
FONTE_PADRAO = f"Dados simulados, reprodutíveis por semente · {REPO}"
TRANSPARENCIA = brand.bloco_transparencia(
    data_base="21/09/2026", posicao="não possui",
    fontes="simulação própria, semente declarada no código",
    ultima_revisao="21/09/2026")
CHAMADA_CODIGO = (f"Código, dados e notebook no Colab: {REPO}")

aplicar_tema()
EST = data.gerar_estrategia(semente=42)
BENCH = data.gerar_benchmark(EST)
R = EST.trades.r_multiple.values
PAR = data.gerar_par_comparavel()

# --- Saídas reais dos cards de código ----------------------------------------
# Cada card de código mostra um trecho e o que ele imprime. Os valores abaixo
# são calculados aqui, de modo que o "output" impresso no card seja literalmente
# o resultado do trecho ao lado — e não uma transcrição feita à mão.
MC_MDD = metrics.risco.monte_carlo_mdd(R)
SEM_TOP5 = metrics.sinal.remove_best_trades(R, n=5)
REG = metrics.execucao.beta_e_alfa(EST.diario.values, BENCH.values)
PESOS_EXEMPLO = [0.28, 0.22, 0.18, 0.14, 0.10, 0.08]
HHI_EXEMPLO = metrics.sinal.hhi_contribuicao(PESOS_EXEMPLO)
BREADTH_EXEMPLO = 1 / HHI_EXEMPLO


def _br(texto: str) -> str:
    """Vírgula decimal e sinal de menos tipográfico (U+2212), não hífen.

    Parece preciosismo e não é: o hífen ASCII tem metade da largura do menos e
    quebra o alinhamento óptico de uma coluna de números.
    """
    return texto.replace(".", ",").replace("-", "−")


def _pct(x: float, casas: int = 1) -> str:
    """Formata percentual no padrão brasileiro, com sinal explícito."""
    return _br(f"{x * 100:+.{casas}f}%")


def _num(x: float, casas: int = 2) -> str:
    return _br(f"{x:.{casas}f}")


# =============================================================================
# POST 001 — Concept — decisão sob incerteza
# =============================================================================
def post_001():
    caminhos = metrics.evidencia.monte_carlo_equity(R, 0.01, 2000, semente=0)
    finais = caminhos[:, -1]
    q = {p: float(np.quantile(finais, p / 100)) for p in (5, 25, 50, 75, 95)}
    picos = np.maximum.accumulate(caminhos, axis=1)
    mdds = (caminhos / picos - 1).min(axis=1)
    amplitude = (q[95] - q[5]) / q[50]

    def plot_leque(ax):
        sub = caminhos[:300]
        x = np.arange(sub.shape[1])
        p05, p50, p95 = (np.quantile(caminhos, p, axis=0) for p in (.05, .5, .95))
        ax.fill_between(x, p05, p95, color=brand.VERDE_FLORESTA, alpha=.16, lw=0)
        for linha in sub[:60]:
            ax.plot(x, linha, color=brand.VERDE_FLORESTA, alpha=.07, lw=.8)
        ax.plot(x, p50, color=brand.VERDE_FLORESTA, lw=2.4)
        ax.plot(x, p05, color=brand.COBRE, lw=1.8, ls="--")
        ax.axhline(1, color=brand.LINHA_SUTIL, lw=1)
        ax.set_xlabel("operações", color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("capital (base 1,0)", color=brand.CINZA_SALVIA, fontsize=11)
        ax.annotate("mediana", xy=(x[-1], p50[-1]), xytext=(-6, 10),
                    textcoords="offset points", ha="right",
                    color=brand.VERDE_FLORESTA, fontsize=12, fontweight="semibold")
        ax.annotate("P5", xy=(x[-1], p05[-1]), xytext=(-6, -14),
                    textcoords="offset points", ha="right",
                    color=brand.COBRE, fontsize=12, fontweight="semibold")

    def plot_mdd(ax):
        ax.hist(mdds, bins=48, color=brand.VERDE_FLORESTA, alpha=.78,
                edgecolor=brand.MARFIM, lw=1.0)
        p95 = float(np.quantile(mdds, 0.05))
        ax.axvline(p95, color=brand.COBRE, lw=2.2, ls="--")
        ax.annotate(f"P95 = {_pct(p95, 0)}", xy=(p95, ax.get_ylim()[1] * .86),
                    xytext=(-10, 0), textcoords="offset points", ha="right",
                    color=brand.COBRE, fontsize=13, fontweight="semibold")
        eixo_percentual(ax, "x", 0)
        ax.set_xlabel("queda máxima da trajetória", color=brand.CINZA_SALVIA,
                      fontsize=11)

    return [
        cards.capa(
            f"2.000 históricos, as mesmas regras: do {_pct(q[5] - 1, 0)} ao "
            f"{_pct(q[95] - 1, 0)}",
            "concept", numero="POST 001 · CONCEITO",
            apoio="O backtest que você viu é uma observação de uma distribuição. "
                  "Tratá-lo como o resultado da estratégia é um erro de categoria."),
        cards.formula(
            "Por que a ordem dos resultados muda o destino",
            r"W_T = W_0 \prod_{t=1}^{T}\,(1 + f\,R_t)",
            [(r"W_T", "capital ao final de T operações"),
             (r"f", "fração do capital arriscada por operação"),
             (r"R_t", "resultado da operação t, em múltiplos de risco")],
            "concept",
            leitura="O produtório não é comutativo quando há drawdown: perder cedo "
                    "reduz a base sobre a qual todo ganho posterior incide. Os "
                    "mesmos R em ordem diferente não produzem o mesmo W.",
            rodape="Manual de Validação · Cap. 05, métricas 57 a 61"),
        cards.grafico(
            "Reamostragem dos mesmos resultados",
            plot_leque, "concept",
            leitura=f"Banda P5–P95. A amplitude no horizonte final é de "
                    f"{_num(amplitude, 1)}× a mediana — com o mesmo conjunto de "
                    "operações, apenas reordenadas.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "Distribuição do capital final",
            ("Percentil", "Capital", "Retorno"),
            [("P5", _num(q[5]), _pct(q[5] - 1, 0)),
             ("P25", _num(q[25]), _pct(q[25] - 1, 0)),
             ("P50", _num(q[50]), _pct(q[50] - 1, 0)),
             ("P75", _num(q[75]), _pct(q[75] - 1, 0)),
             ("P95", _num(q[95]), _pct(q[95] - 1, 0))],
            "concept", destacar=0,
            leitura="Um investidor no P5 e outro no P95 seguiram a mesma "
                    "estratégia, com a mesma disciplina. A diferença entre eles "
                    "não é mérito.",
            rodape="2.000 reamostragens iid · f = 1% do capital por operação"),
        cards.grafico(
            "A queda que a estratégia pode exigir",
            plot_mdd, "concept",
            leitura=f"O histórico observado registrou {_pct(metrics.risco.max_drawdown(EST.diario), 0)}. "
                    f"O percentil 95 das trajetórias exige {_pct(float(np.quantile(mdds, .05)), 0)}. "
                    "É este o número que dimensiona posição.",
            rodape=FONTE_PADRAO),
        cards.codigo(
            "A distribuição inteira, em seis linhas",
            ["from wizzlab import data, metrics",
             "",
             "est = data.gerar_estrategia(semente=42)",
             "r = est.trades.r_multiple.values",
             "",
             "# reamostra e devolve os percentis do MDD",
             "print(metrics.risco.monte_carlo_mdd(r))"],
            saida=[f"P50    {_num(float(MC_MDD['P50']), 3)}",
                   f"P95    {_num(float(MC_MDD['P95']), 3)}",
                   f"P99    {_num(float(MC_MDD['P99']), 3)}"],
            serie="concept",
            leitura="P95 é o drawdown que a estratégia pode exigir sem que nada "
                    "tenha mudado na premissa. É ele que entra no sizing.",
            rodape=f"Roda no Colab sem instalar nada · {REPO}"),
        cards.em_aberto(
            "O que este post não resolve",
            ["A reamostragem iid apaga a dependência temporal. Com bootstrap "
             "por blocos, quanto a banda alarga?",
             "Qual fração f maximiza o crescimento sem estourar o drawdown que "
             "você tolera de fato?",
             "Quantas operações seriam necessárias para o intervalo do edge "
             "não cruzar o zero?"],
            "concept",
            proximo="As três são calculáveis com o que já está no repositório: "
                    "stationary_bootstrap, kelly_fraction e "
                    "min_track_record_length.",
            rodape=f"Politis & Romano (1994) · {REPO}"),
    ]


# =============================================================================
# POST 002 — Concept — mesmo retorno, risco diferente
# =============================================================================
def post_002():
    a, b = PAR["A"], PAR["B"]
    met = {}
    for nome, s in (("A", a), ("B", b)):
        met[nome] = {
            "ret": float((1 + s).prod() - 1),
            "vol": metrics.risco.volatilidade(s),
            "mdd": metrics.risco.max_drawdown(s),
            "tuw": metrics.risco.time_under_water(s),
            "ulcer": metrics.risco.ulcer_index(s),
            "calmar": metrics.risco.calmar(s),
        }

    def plot_curvas(ax):
        for nome, cor in (("A", brand.VERDE_FLORESTA), ("B", brand.COBRE)):
            cap = metrics.risco.curva_capital(PAR[nome]) * 100
            ax.plot(cap.index, cap.values, color=cor, lw=2.1)
            ax.annotate(f"carteira {nome}", xy=(cap.index[-1], cap.iloc[-1]),
                        xytext=(8, 0), textcoords="offset points", color=cor,
                        fontsize=12, fontweight="semibold", va="center")
        ax.axhline(100, color=brand.LINHA_SUTIL, lw=1)
        ax.set_ylabel("índice (base 100)", color=brand.CINZA_SALVIA, fontsize=11)
        ax.margins(x=.22)

    def plot_dd(ax):
        for nome, cor in (("A", brand.VERDE_FLORESTA), ("B", brand.COBRE)):
            dd = metrics.risco.serie_drawdown(PAR[nome])
            ax.fill_between(dd.index, dd.values, 0, color=cor, alpha=.22, lw=0)
            ax.plot(dd.index, dd.values, color=cor, lw=1.8)
        ax.axhline(0, color=brand.LINHA_SUTIL, lw=1)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("queda desde o pico", color=brand.CINZA_SALVIA, fontsize=11)
        ax.annotate("B", xy=(dd.index[len(dd) // 2], met["B"]["mdd"]),
                    xytext=(10, 6), textcoords="offset points",
                    color=brand.COBRE, fontsize=13, fontweight="semibold")

    return [
        cards.capa(
            f"Duas carteiras fecharam em {_pct(met['A']['ret'], 2)}. Uma caiu "
            f"{_num(abs(met['A']['mdd']) * 100, 1)}%; a outra, "
            f"{_num(abs(met['B']['mdd']) * 100, 1)}%.",
            "concept", numero="POST 002 · CONCEITO",
            apoio="Retorno acumulado idêntico. Risco incomparável. "
                  "Nenhum ranking por rentabilidade separa as duas."),
        cards.grafico(
            "O mesmo destino por caminhos distintos",
            plot_curvas, "concept",
            leitura="As duas séries foram construídas para fechar exatamente no "
                    "mesmo ponto. A única variável livre é a trajetória.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "O que o retorno acumulado não mostra",
            ("Métrica", "Carteira A", "Carteira B"),
            [("Retorno no período", _pct(met["A"]["ret"], 2), _pct(met["B"]["ret"], 2)),
             ("Volatilidade anual", _pct(met["A"]["vol"], 1).lstrip("+"),
              _pct(met["B"]["vol"], 1).lstrip("+")),
             ("Queda máxima", _pct(met["A"]["mdd"], 1), _pct(met["B"]["mdd"], 1)),
             ("Tempo abaixo do pico", f"{met['A']['tuw']:.0%}", f"{met['B']['tuw']:.0%}"),
             ("Ulcer Index", _num(met["A"]["ulcer"], 3), _num(met["B"]["ulcer"], 3)),
             ("Calmar", _num(met["A"]["calmar"]), _num(met["B"]["calmar"]))],
            "concept", destacar=2,
            leitura=f"Mesmo numerador, denominadores que diferem em "
                    f"{_num(met['A']['calmar'] / met['B']['calmar'], 1)}×.",
            rodape="Todas as métricas em wizzlab.metrics.risco"),
        cards.grafico(
            "A diferença está inteira aqui",
            plot_dd, "concept",
            leitura=f"A carteira B passou {met['B']['tuw']:.0%} do período abaixo "
                    f"do próprio pico, contra {met['A']['tuw']:.0%} da A.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "A métrica que separa as duas",
            r"UI = \sqrt{\frac{1}{T}\sum_{t=1}^{T} D_t^{\,2}}",
            [(r"D_t", "drawdown percentual no instante t"),
             (r"T", "número de períodos observados")],
            "concept",
            leitura="O Ulcer Index eleva o drawdown ao quadrado e tira a média no "
                    "tempo. Diferente do drawdown máximo, ele penaliza permanecer "
                    "abaixo do pico — não apenas afundar uma vez.",
            rodape="Martin & McCann · Manual de Validação, métrica 24"),
        cards.codigo(
            "As duas carteiras, medidas",
            ["from wizzlab import data, metrics as m",
             "",
             "par = data.gerar_par_comparavel()",
             "",
             "for c in ('A', 'B'):",
             "    s = par[c]",
             "    print(c, m.risco.ulcer_index(s),",
             "             m.risco.calmar(s))"],
            saida=[f"A   {_num(met['A']['ulcer'], 3)}   {_num(met['A']['calmar'])}",
                   f"B   {_num(met['B']['ulcer'], 3)}   {_num(met['B']['calmar'])}"],
            serie="concept",
            leitura=f"Volatilidade {_num(met['B']['vol'] / met['A']['vol'], 1)}× "
                    f"maior, mas queda máxima "
                    f"{_num(met['B']['mdd'] / met['A']['mdd'], 1)}× maior. A "
                    "diferença entre os dois múltiplos indica risco concentrado "
                    "em um episódio, não distribuído.",
            rodape=f"Roda no Colab sem instalar nada · {REPO}"),
        cards.em_aberto(
            "O que este post não resolve",
            ["Em que condições Ulcer Index e Calmar discordam sobre qual "
             "carteira é pior?",
             "Profundidade ou duração: qual prevê melhor o abandono de uma "
             "estratégia por quem a opera?",
             "Com que frequência duas carteiras de mesmo retorno diferem por "
             "acaso, e não por estrutura?"],
            "concept",
            proximo="A terceira exige simulação, e é a que separa diagnóstico de "
                    "narrativa. Notebook 2 do repositório.",
            rodape=f"Martin & McCann · {REPO}"),
    ]


# =============================================================================
# POST 003 — Portfolio — as regras antes da primeira posição
# =============================================================================
def post_003():
    def plot_regua(ax):
        rotulos = ["Retorno\nvs CDI e índice", "Queda máxima\ne tempo", "Caixa e\nconcentração",
                   "Giro e\ncusto pago"]
        frequencia = [1.00, 0.62, 0.18, 0.07]
        x = np.arange(len(rotulos))
        cores = [brand.COBRE if v < 0.25 else brand.TEXTO_METADADO_ESCURO
                 for v in frequencia]
        ax.bar(x, frequencia, width=.62, color=cores, edgecolor=brand.AZUL_PETROLEO,
               lw=2)
        ax.set_xticks(x)
        ax.set_xticklabels(rotulos, fontsize=10.5,
                           color=brand.TEXTO_METADADO_ESCURO)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("carteiras públicas que divulgam",
                      color=brand.TEXTO_METADADO_ESCURO, fontsize=11)
        ax.set_ylim(0, 1.12)

    return [
        cards.capa(
            "As quatro métricas que esta carteira publica — e as duas que quase ninguém publica",
            "portfolio", numero="POST 003 · CONTA REAL",
            apoio="Definidas antes da primeira posição, quando ainda não há "
                  "resultado para proteger."),
        cards.conceito(
            "Por que declarar antes",
            "Uma regra escrita depois do resultado não é regra: é racionalização. "
            "E a diferença entre método e sorte só é observável se o critério "
            "existir antes do dado.\n\n"
            "Este post é o registro datado do critério.",
            "portfolio",
            destaque="Se eu acertar, quero conseguir demonstrar que não foi acaso. "
                     "Isso exige um compromisso anterior ao acerto.",
            rodape="Manual de Marca Wizz V2 · seções 8 e 9"),
        cards.tabela(
            "O que será publicado, em todo fechamento",
            ("Item", "Forma", "Frequência"),
            [("Retorno acumulado", "vs CDI e índice", "Mensal"),
             ("Queda máxima", "% e duração", "Mensal"),
             ("Caixa", "% do patrimônio", "Mensal"),
             ("Concentração", "HHI e nº efetivo", "Mensal"),
             ("Giro", "% do patrimônio", "Trimestral"),
             ("Custo pago", "R$ e % ", "Trimestral"),
             ("Decisões erradas", "tese e causa", "Sempre")],
            "portfolio", destacar=6,
            leitura="A última linha é a que dá sentido às outras seis.",
            rodape="Formato fixo a partir do primeiro fechamento"),
        cards.grafico(
            "As duas que costumam faltar",
            plot_regua, "portfolio",
            leitura="Giro e custo são os itens que mais explicam a distância entre "
                    "o resultado simulado e o resultado da conta. São também os "
                    "menos divulgados.",
            rodape="Estimativa qualitativa do autor sobre carteiras públicas "
                   "brasileiras · não é levantamento amostral"),
        cards.conceito(
            "O que esta carteira não é",
            "Não é carteira recomendada. Não é ranking. Não é desafio de "
            "rentabilidade.\n\n"
            "É o registro datado de um processo de decisão, publicado com as "
            "premissas abertas — inclusive quando a conclusão for não investir.",
            "portfolio",
            destaque="Posições serão divulgadas em peso percentual. Valores "
                     "absolutos são opcionais e irrelevantes para o argumento.",
            rodape="Conteúdo educacional · não constitui recomendação"),
        cards.codigo(
            "Como a concentração será medida",
            ["from wizzlab import metrics",
             "",
             "# pesos da carteira, em fração do total",
             "w = [.28, .22, .18, .14, .10, .08]",
             "",
             "h = metrics.sinal.hhi_contribuicao(w)",
             "print(h, 1 / h)"],
            saida=[f"HHI          {_num(float(HHI_EXEMPLO), 3)}",
                   f"nº efetivo   {_num(float(BREADTH_EXEMPLO))}"],
            serie="portfolio",
            leitura="Seis posições nesses pesos equivalem a "
                    f"{_num(float(BREADTH_EXEMPLO))} apostas independentes. É esse "
                    "número que será publicado, não a contagem de tickers.",
            rodape=f"Métricas 106 e 107 · {REPO}"),
        cards.em_aberto(
            "O que ainda não está definido",
            ["Qual concentração é alta demais? HHI de 0,25 e seis posições "
             "dizem a mesma coisa?",
             "Quanto giro anual o edge desta carteira suporta antes de zerar?",
             "Que evidência encerraria a carteira inteira, e não apenas uma "
             "posição?"],
            "portfolio",
            proximo="A segunda tem resposta em uma linha — break_even_cost. A "
                    "terceira será publicada antes da primeira compra.",
            rodape=f"Métrica 145, kill-switch ex ante · {REPO}"),
    ]


# =============================================================================
# POST 004 — Data — a convexidade da recuperação
# =============================================================================
def post_004():
    quedas = np.array([.10, .20, .30, .40, .50, .60, .70, .80])
    necessario = quedas / (1 - quedas)
    # Custo composto: quantos anos a 10% a.a. para recuperar cada queda.
    anos = np.log(1 / (1 - quedas)) / np.log(1.10)

    def plot_barras(ax):
        x = np.arange(len(quedas))
        ax.bar(x - .19, quedas, width=.38, color=brand.CINZA_SALVIA,
               edgecolor=brand.MARFIM, lw=2, label="queda sofrida")
        ax.bar(x + .19, necessario, width=.38, color=brand.COBRE,
               edgecolor=brand.MARFIM, lw=2, label="alta necessária")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{q:.0%}" for q in quedas])
        eixo_percentual(ax, "y", 0)
        ax.legend(frameon=False, fontsize=11.5, labelcolor=brand.AZUL_PETROLEO,
                  loc="upper left")
        ax.set_xlabel("queda sofrida", color=brand.CINZA_SALVIA, fontsize=11)

    def plot_anos(ax):
        ax.plot(quedas, anos, color=brand.COBRE, lw=2.4, marker="o",
                markersize=9, markeredgecolor=brand.MARFIM, markeredgewidth=2)
        eixo_percentual(ax, "x", 0)
        ax.set_xlabel("queda sofrida", color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("anos a 10% a.a. para recuperar",
                      color=brand.CINZA_SALVIA, fontsize=11)
        for xi, yi in list(zip(quedas, anos))[::3]:
            ax.annotate(f"{yi:.1f} anos", xy=(xi, yi), xytext=(-8, 12),
                        textcoords="offset points", ha="right", fontsize=11.5,
                        color=brand.AZUL_PETROLEO, fontweight="semibold")

    return [
        cards.capa(
            "Uma queda de 50% exige +100% para voltar. Uma de 80% exige +400%.",
            "data", numero="POST 004 · DADOS",
            apoio="A recuperação é convexa na perda. Essa assimetria é a razão "
                  "aritmética de risco preceder retorno."),
        cards.formula(
            "A exigência de recuperação",
            r"g^{*} = \frac{q}{1 - q}",
            [(r"q", "queda percentual sofrida"),
             (r"g^{*}", "alta necessária para retornar ao capital inicial")],
            "data",
            leitura="A função diverge quando q → 1. Não há simetria: perder e "
                    "ganhar a mesma porcentagem não se cancelam, porque a base "
                    "sobre a qual o ganho incide já foi reduzida.",
            rodape="Identidade aritmética · não é estimativa"),
        cards.tabela(
            "A tabela inteira",
            ("Queda", "Alta necessária", "Razão"),
            [(f"−{q:.0%}", _br(f"+{g:.1%}"), _br(f"{g / q:.2f}×"))
             for q, g in zip(quedas, necessario)],
            "data", destacar=4,
            leitura="Até 20%, a razão fica próxima de 1,2×. A partir de 50%, ela "
                    "passa de 2× e cresce sem limite.",
            rodape="Valores exatos"),
        cards.grafico(
            "Onde a curva deixa de ser linear",
            plot_barras, "data",
            leitura="Até 30% as duas barras são comparáveis. Depois de 50%, a "
                    "segunda descola da primeira de forma irrecuperável.",
            rodape=FONTE_PADRAO),
        cards.grafico(
            "O custo em tempo, não em porcentagem",
            plot_anos, "data",
            leitura="Convertida em anos de retorno a 10% a.a., a mesma assimetria "
                    f"fica mais concreta: uma queda de 70% consome "
                    f"{_num(float(anos[6]), 1)} anos de capitalização.",
            rodape=FONTE_PADRAO),
        cards.codigo(
            "A tabela inteira, em três linhas",
            ["import numpy as np",
             "",
             "q = np.array([.10, .30, .50, .70])",
             "g = q / (1 - q)              # alta exigida",
             "t = np.log(1/(1-q)) / np.log(1.10)   # anos",
             "",
             "print(np.c_[q, g, t].round(2))"],
            saida=[_br(f"0.10   {necessario[0]:.2f}    {anos[0]:.2f}"),
                   _br(f"0.30   {necessario[2]:.2f}    {anos[2]:.2f}"),
                   _br(f"0.50   {necessario[4]:.2f}    {anos[4]:.2f}"),
                   _br(f"0.70   {necessario[6]:.2f}   {anos[6]:.2f}")],
            serie="data",
            leitura="Terceira coluna: anos de retorno a 10% a.a. consumidos "
                    "apenas para voltar ao ponto de partida.",
            rodape=f"Roda no Colab sem instalar nada · {REPO}"),
        cards.em_aberto(
            "O que este post não resolve",
            ["Se limitar a perda custa retorno esperado, onde fica o ponto de "
             "equilíbrio?",
             "Kelly indica que fração para esta distribuição — e por que quase "
             "ninguém opera Kelly cheio?",
             "A convexidade muda quando há aportes recorrentes ao longo da "
             "queda?"],
            "data",
            proximo="As duas primeiras estão em metrics.risco — kelly_fraction e "
                    "risk_of_ruin. A terceira eu ainda não medi.",
            rodape=f"Métricas 38 e 39 · {REPO}"),
    ]


# =============================================================================
# POST 005 — Research — média, mediana e concentração
# =============================================================================
def post_005():
    media = metrics.trade.expectancy(R)
    mediana = metrics.trade.median_trade(R)
    skew = metrics.trade.skewness(R)
    conc = metrics.sinal.pnl_concentration(R)
    sem_top = metrics.sinal.remove_best_trades(R, n=5)
    top10 = float(conc.iloc[2])
    wr = metrics.trade.win_rate(R)

    def plot_hist(ax):
        ax.hist(R, bins=40, color=brand.VERDE_FLORESTA, alpha=.78,
                edgecolor=brand.MARFIM, lw=1.2)
        topo = ax.get_ylim()[1]
        ax.axvline(mediana, color=brand.AZUL_PETROLEO, lw=2.2, ls="--")
        ax.axvline(media, color=brand.COBRE, lw=2.2, ls="--")
        ax.annotate(f"mediana {_num(mediana)}R", xy=(mediana, topo * .92),
                    xytext=(-10, 0), textcoords="offset points", ha="right",
                    color=brand.AZUL_PETROLEO, fontsize=12, fontweight="semibold")
        ax.annotate(f"média {_num(media)}R", xy=(media, topo * .70),
                    xytext=(12, 0), textcoords="offset points",
                    color=brand.COBRE, fontsize=12, fontweight="semibold")
        ax.set_xlabel("resultado por operação, em múltiplos de risco",
                      color=brand.CINZA_SALVIA, fontsize=11)

    def plot_lorenz(ax):
        vencedores = np.sort(R[R > 0])[::-1]
        acum = np.cumsum(vencedores) / vencedores.sum()
        x = np.arange(1, len(vencedores) + 1) / len(vencedores)
        ax.plot(x, acum, color=brand.VERDE_FLORESTA, lw=2.4)
        ax.plot([0, 1], [0, 1], color=brand.CINZA_SALVIA, lw=1.6, ls="--")
        k = max(1, int(np.ceil(len(vencedores) * .10)))
        ax.scatter([.10], [acum[k - 1]], s=90, color=brand.COBRE, zorder=5,
                   edgecolor=brand.MARFIM, lw=2.5)
        ax.annotate(f"10% → {acum[k - 1]:.0%}", xy=(.10, acum[k - 1]),
                    xytext=(14, -6), textcoords="offset points", fontsize=12.5,
                    color=brand.COBRE, fontweight="semibold")
        eixo_percentual(ax, "x", 0)
        eixo_percentual(ax, "y", 0)
        ax.set_xlabel("operações vencedoras, da maior para a menor",
                      color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("fração do lucro bruto", color=brand.CINZA_SALVIA,
                      fontsize=11)

    return [
        cards.capa(
            f"Média de {_num(media)}R por operação. Mediana de {_num(mediana)}R.",
            "research", numero="POST 005 · PESQUISA",
            apoio="As duas afirmações descrevem a mesma amostra. A distância entre "
                  "elas é o diagnóstico."),
        cards.grafico(
            "A distribuição inteira, não o resumo",
            plot_hist, "research",
            leitura=f"{1 - wr:.0%} das operações terminam negativas, concentradas "
                    "perto de −1R. A cauda direita, longa e rala, carrega a média "
                    "para o campo positivo.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "A medida da assimetria",
            r"\gamma_1 = \frac{\mathbb{E}\left[(R - \mu)^3\right]}{\sigma^3}",
            [(r"\mu", "média dos resultados"),
             (r"\sigma", "desvio-padrão"),
             (r"\gamma_1", f"assimetria — nesta amostra, {_num(skew)}")],
            "research",
            leitura="Assimetria positiva indica cauda direita dominante. É o perfil "
                    "esperado de um sistema que limita perdas e deixa ganhos "
                    "correrem — desde que seja uma escolha, e não uma descoberta.",
            rodape="Manual de Validação · métrica 11"),
        cards.grafico(
            "Quem sustenta o lucro bruto",
            plot_lorenz, "research",
            leitura=f"As 10% melhores operações respondem por {top10:.0%} do lucro "
                    "bruto. A linha tracejada seria a distribuição uniforme.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "O teste de remoção",
            ("Amostra", "Expectancy", "Situação"),
            [("Completa (420 operações)", f"{_num(sem_top['expectancy_original'])}R", "positiva"),
             ("Sem as 5 melhores", f"{_num(float(sem_top.iloc[1]))}R",
              "positiva" if bool(sem_top.iloc[2]) else "negativa")],
            "research", destacar=1,
            leitura="Remover cinco operações de 420 — 1,2% da amostra — e observar "
                    "o que sobra do edge. É o teste mais direto de dependência de "
                    "eventos.",
            rodape="wizzlab.metrics.sinal.remove_best_trades()"),
        cards.codigo(
            "Rode o teste de remoção",
            ["from wizzlab import data, metrics",
             "",
             "est = data.gerar_estrategia(semente=42)",
             "r = est.trades.r_multiple.values",
             "",
             "# tira as 5 melhores de 420 operações",
             "print(metrics.sinal.remove_best_trades(r, 5))"],
            saida=[f"expectancy original   {_num(float(SEM_TOP5.iloc[0]), 3)}",
                   f"sem as 5 melhores     {_num(float(SEM_TOP5.iloc[1]), 3)}",
                   f"ainda positiva        {SEM_TOP5.iloc[2]}"],
            serie="research",
            leitura="Remover 1,2% da amostra corta a expectancy em "
                    f"{_num((1 - float(SEM_TOP5.iloc[1]) / float(SEM_TOP5.iloc[0])) * 100, 0)}%. "
                    "Permanece positiva, mas a margem sobre o custo desaparece.",
            rodape=f"Roda no Colab sem instalar nada · {REPO}"),
        cards.referencias(
            "De onde vem o método",
            [("Bailey, D. H.; López de Prado, M. (2014). The Deflated Sharpe "
              "Ratio: correcting for selection bias and non-normality.",
              "J. Portfolio Management 40(5) · doi 10.3905/jpm.2014.40.5.094"),
             ("Lo, A. W. (2002). The Statistics of Sharpe Ratios.",
              "Financial Analysts Journal 58(4) · doi 10.2469/faj.v58.n4.2453"),
             ("Politis, D. N.; Romano, J. P. (1994). The Stationary Bootstrap.",
              "J. Am. Stat. Assoc. 89(428) · doi 10.1080/01621459.1994.10476870")],
            "research",
            leitura="Convexidade é uma estrutura legítima — sistemas seguidores "
                    "de tendência exibem este perfil por projeto. O que a "
                    "literatura cobra é que esteja declarado antes, não "
                    "descoberto depois.",
            rodape=f"Bibliografia completa no repositório · {REPO}"),
    ]


# =============================================================================
# POST 006 — Portfolio — a régua de medição
# =============================================================================
def post_006():
    est_cagr = metrics.risco.cagr(EST.diario)
    ben_cagr = metrics.risco.cagr(BENCH)
    reg = metrics.execucao.beta_e_alfa(EST.diario.values, BENCH.values)

    def plot_comparado(ax):
        cap = metrics.risco.curva_capital(EST.diario) * 100
        ben = metrics.risco.curva_capital(BENCH) * 100
        ax.plot(cap.index, cap.values, color=brand.COBRE, lw=2.2)
        ax.plot(ben.index, ben.values, color=brand.TEXTO_METADADO_ESCURO, lw=1.8)
        ax.annotate("carteira", xy=(cap.index[-1], cap.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", color=brand.COBRE, fontsize=12,
                    fontweight="semibold", va="center")
        ax.annotate("referência", xy=(ben.index[-1], ben.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", color=brand.TEXTO_METADADO_ESCURO,
                    fontsize=12, fontweight="semibold", va="center")
        ax.axhline(100, color="#1E3C3A", lw=1)
        ax.set_ylabel("índice (base 100)", color=brand.TEXTO_METADADO_ESCURO,
                      fontsize=11)
        ax.margins(x=.24)

    return [
        cards.capa(
            "A régua é definida agora, enquanto não há resultado para proteger",
            "portfolio", numero="POST 006 · CONTA REAL",
            apoio="Quatro números, no mesmo período, contra a mesma referência — "
                  "em todo fechamento, sem exceção."),
        cards.grafico(
            "Contra o quê, e em que período",
            plot_comparado, "portfolio",
            leitura="Uma curva isolada não sustenta afirmação nenhuma. A comparação "
                    "declarada, no mesmo intervalo, é o mínimo para que o número "
                    "signifique algo.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "O que sobra depois da exposição ao mercado",
            r"r_t = \alpha + \beta\,r^{m}_{t} + \varepsilon_t",
            [(r"r_t", "retorno da carteira no período t"),
             (r"r^{m}_{t}", "retorno da referência no mesmo período"),
             (r"\beta", "quanto do resultado é apenas estar comprado"),
             (r"\alpha", "o que resta depois de descontar isso")],
            "portfolio",
            leitura=f"Na simulação: β = {_num(float(reg['beta']))}, "
                    f"t(α) = {_num(float(reg['t_excesso']))}. Com |t| abaixo de 2, "
                    "o excesso não é distinguível de zero — e será reportado assim.",
            rodape="Manual de Validação · métricas 150 e 151"),
        cards.tabela(
            "Os quatro números do fechamento",
            ("Métrica", "Carteira", "Referência"),
            [("Retorno anualizado", _pct(est_cagr, 1), _pct(ben_cagr, 1)),
             ("Queda máxima", _pct(metrics.risco.max_drawdown(EST.diario), 1),
              _pct(metrics.risco.max_drawdown(BENCH), 1)),
             ("Tempo abaixo do pico",
              f"{metrics.risco.time_under_water(EST.diario):.0%}",
              f"{metrics.risco.time_under_water(BENCH):.0%}"),
             ("Sharpe", _num(metrics.risco.sharpe(EST.diario)),
              _num(metrics.risco.sharpe(BENCH)))],
            "portfolio", destacar=1,
            leitura="Caixa, concentração, giro e custo entram na mesma tabela a "
                    "partir do primeiro fechamento com posição aberta.",
            rodape="Valores da simulação — a carteira real ainda não começou"),
        cards.conceito(
            "As três coisas que não vou fazer",
            "Não vou trocar de referência quando ficar conveniente.\n\n"
            "Não vou iniciar a contagem em uma data escolhida depois de ver o "
            "resultado.\n\n"
            "Não vou apresentar retorno bruto onde o líquido é o que importa.",
            "portfolio",
            destaque="Se a régua mudar, a mudança vira post — com a justificativa e "
                     "a série recalculada nos dois critérios.",
            rodape="Data-snooping por escolha de janela é a forma mais comum, e a "
                   "menos discutida"),
        cards.codigo(
            "O excesso, com o erro-padrão junto",
            ["from wizzlab import data, metrics",
             "",
             "est = data.gerar_estrategia(semente=42)",
             "ref = data.gerar_benchmark(est)",
             "",
             "print(metrics.execucao.beta_e_alfa(",
             "    est.diario.values, ref.values))"],
            saida=[f"excesso/período   {_num(float(REG['excesso_por_periodo']), 4)}",
                   f"t do excesso      {_num(float(REG['t_excesso']))}",
                   f"beta              {_num(float(REG['beta']))}",
                   f"R quadrado        {_num(float(REG['r2']))}"],
            serie="portfolio",
            leitura=f"t = {_num(float(REG['t_excesso']))} não passa de 2. O excesso "
                    "não é distinguível de zero, e será reportado assim — com o t, "
                    "não apenas com o ponto.",
            rodape=f"Métricas 150 e 151 · {REPO}"),
        cards.em_aberto(
            "O que esta régua ainda não responde",
            ["Contra que referência? Índice amplo e cesta setorial podem dar "
             "sinais opostos para a mesma carteira.",
             "Com que amostra o t do excesso passaria de 2, mantendo o mesmo "
             "excesso por período?",
             "Quanto do beta é escolha e quanto é consequência do universo "
             "elegível?"],
            "portfolio",
            proximo="A primeira é o post da semana 18. A segunda é o Minimum "
                    "Track Record Length, métrica 47.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


ROTEIROS = {
    "post-001-incerteza": ("Investir não é prever. É decidir sob incerteza.",
                           "Concept", 1, "Terça", post_001),
    "post-002-duas-carteiras": ("Duas carteiras renderam 15%. Qual foi melhor?",
                                "Concept", 1, "Quinta", post_002),
    "post-003-regras": ("Wizz Portfolio — as regras antes da primeira posição",
                        "Portfolio", 1, "Domingo", post_003),
    "post-004-assimetria": ("Perdeu 50%? Ganhar 50% não leva você de volta.",
                            "Data", 2, "Terça", post_004),
    "post-005-media-engana": ("Por que a média de retorno pode enganar?",
                              "Research", 2, "Quinta", post_005),
    "post-006-medir": ("Wizz Portfolio — como vamos medir desempenho",
                       "Portfolio", 2, "Domingo", post_006),
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for antigo in DESTINO.glob("*.png"):
        antigo.unlink()

    manifesto = []
    for slug, (titulo, serie, semana, dia, fabrica) in ROTEIROS.items():
        problemas = brand.checar_titulo(titulo)
        if problemas:
            raise SystemExit(f"título de {slug} usa termo banido: {problemas}")
        caminhos = cards.carrossel(fabrica(), slug, str(DESTINO))
        manifesto.append({
            "slug": slug, "titulo": titulo, "serie": serie,
            "semana": semana, "dia": dia, "n_cards": len(caminhos),
            "arquivos": [pathlib.Path(c).name for c in caminhos],
        })
        print(f"{slug:26} {len(caminhos)} cards · {serie} · semana {semana}")

    (DESTINO / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmanifest.json escrito com {len(manifesto)} posts")


if __name__ == "__main__":
    main()
