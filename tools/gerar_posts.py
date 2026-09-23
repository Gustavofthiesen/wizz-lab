"""Gera as imagens dos carrosséis a partir do roteiro de cada post.

O roteiro fica aqui, em Python, e não em um arquivo de design. A razão é
editorial: o texto do post e o gráfico que o ilustra saem da **mesma fonte de
verdade**, e um número citado no copy não pode divergir do número plotado ao
lado. Todo valor escrito nos cards é interpolado do cálculo.

Padrão de construção (7 cards):

1. **Capa** — o objeto medido e os valores principais
2. **Definição** — fórmula e glossário dos termos
3. **Evidência 1** — gráfico
4. **Evidência 2** — tabela ou segundo gráfico
5. **Evidência 3** — o mecanismo, em gráfico ou tabela
6. **Código** — o trecho que reproduz o resultado, com a saída que ele imprime
7. **Em aberto** — questões não cobertas, com o endereço das respostas

Registro do texto
-----------------
O alvo é a nota técnica, não o post persuasivo. Em concreto:

* **Título de card é rótulo descritivo**, e diz o que está ali. Não é gancho.
  "Distribuição do drawdown máximo", não "A queda que a estratégia pode exigir".
* **Legenda é legenda de figura**: declara o que está plotado, com n, semente e
  parâmetros. Não fecha com a conclusão — quem lê tira a própria.
* **Sem imperativo e sem segunda pessoa.** Nada de "rode", "olhe", "você".
* **Sem a construção "X não é Y, é Z"**, que é retórica ocupando espaço de dado.
* **Sem contraste montado para chocar.** O número fala; o enquadramento não
  precisa ajudar.

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
FONTE_PADRAO = f"Série simulada, semente 42 · {REPO}"

aplicar_tema()
EST = data.gerar_estrategia(semente=42)
BENCH = data.gerar_benchmark(EST)
R = EST.trades.r_multiple.values
PAR = data.gerar_par_comparavel()

# --- Saídas reais dos cards de código ----------------------------------------
# Cada card de código mostra um trecho e o que ele imprime. Os valores abaixo
# são calculados aqui, de modo que o "output" no card seja literalmente o
# resultado do trecho ao lado — e não uma transcrição feita à mão.
MC_MDD = metrics.risco.monte_carlo_mdd(R)
SEM_TOP5 = metrics.sinal.remove_best_trades(R, n=5)
REG = metrics.execucao.beta_e_alfa(EST.diario.values, BENCH.values)
PESOS_EXEMPLO = [0.28, 0.22, 0.18, 0.14, 0.10, 0.08]
HHI_EXEMPLO = metrics.sinal.hhi_contribuicao(PESOS_EXEMPLO)
BREADTH_EXEMPLO = 1 / HHI_EXEMPLO


def _br(texto: str) -> str:
    """Vírgula decimal e sinal de menos tipográfico (U+2212), não hífen."""
    return texto.replace(".", ",").replace("-", "−")


def _pct(x: float, casas: int = 1) -> str:
    return _br(f"{x * 100:+.{casas}f}%")


def _num(x: float, casas: int = 2) -> str:
    return _br(f"{x:.{casas}f}")


# =============================================================================
# POST 001 — Concept — reamostragem e dispersão de trajetórias
# =============================================================================
def post_001():
    caminhos = metrics.evidencia.monte_carlo_equity(R, 0.01, 2000, semente=0)
    finais = caminhos[:, -1]
    q = {p: float(np.quantile(finais, p / 100)) for p in (5, 25, 50, 75, 95)}
    picos = np.maximum.accumulate(caminhos, axis=1)
    mdds = (caminhos / picos - 1).min(axis=1)
    mdd_p95 = float(np.quantile(mdds, 0.05))

    def plot_leque(ax):
        x = np.arange(caminhos.shape[1])
        p05, p50, p95 = (np.quantile(caminhos, p, axis=0) for p in (.05, .5, .95))
        ax.fill_between(x, p05, p95, color=brand.VERDE_FLORESTA, alpha=.16, lw=0)
        for linha in caminhos[:60]:
            ax.plot(x, linha, color=brand.VERDE_FLORESTA, alpha=.07, lw=.8)
        ax.plot(x, p50, color=brand.VERDE_FLORESTA, lw=2.4)
        ax.plot(x, p05, color=brand.COBRE, lw=1.8, ls="--")
        ax.axhline(1, color=brand.LINHA_SUTIL, lw=1)
        ax.set_xlabel("operações", color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("capital (base 1,0)", color=brand.CINZA_SALVIA, fontsize=11)
        ax.annotate("P50", xy=(x[-1], p50[-1]), xytext=(-6, 10),
                    textcoords="offset points", ha="right",
                    color=brand.VERDE_FLORESTA, fontsize=12, fontweight="semibold")
        ax.annotate("P5", xy=(x[-1], p05[-1]), xytext=(-6, -14),
                    textcoords="offset points", ha="right",
                    color=brand.COBRE, fontsize=12, fontweight="semibold")

    def plot_mdd(ax):
        ax.hist(mdds, bins=48, color=brand.VERDE_FLORESTA, alpha=.78,
                edgecolor=brand.MARFIM, lw=1.0)
        ax.axvline(mdd_p95, color=brand.COBRE, lw=2.2, ls="--")
        ax.annotate(f"P5 = {_pct(mdd_p95, 0)}", xy=(mdd_p95, ax.get_ylim()[1] * .86),
                    xytext=(-10, 0), textcoords="offset points", ha="right",
                    color=brand.COBRE, fontsize=13, fontweight="semibold")
        eixo_percentual(ax, "x", 0)
        ax.set_xlabel("drawdown máximo da trajetória",
                      color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("nº de trajetórias", color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Dispersão do capital final sob reamostragem de trajetórias",
            "concept", numero="001 · MONTE CARLO",
            apoio=f"420 operações reamostradas em 2.000 trajetórias, f = 1% por "
                  f"operação. Capital final: P5 = {_num(q[5])}, "
                  f"P50 = {_num(q[50])}, P95 = {_num(q[95])}."),
        cards.formula(
            "Evolução multiplicativa do capital",
            r"W_T = W_0 \prod_{t=1}^{T}\,(1 + f\,R_t)",
            [(r"W_T", "capital ao final de T operações"),
             (r"f", "fração do capital arriscada por operação"),
             (r"R_t", "resultado da operação t, em múltiplos de risco")],
            "concept",
            leitura="O capital evolui por produtório. Como cada fator incide "
                    "sobre o saldo corrente, a ordem dos R altera W_T mesmo com "
                    "o conjunto de resultados fixo.",
            rodape="Manual de Validação · métricas 57 a 61"),
        cards.grafico(
            "Trajetórias de reamostragem, banda P5–P95",
            plot_leque, "concept",
            leitura="60 trajetórias sorteadas entre as 2.000, com a banda dos "
                    "percentis 5 e 95 e a mediana em destaque. Bootstrap iid "
                    "sobre os R-multiples, semente 0.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "Quantis do capital final",
            ("Percentil", "Capital", "Retorno"),
            [("P5", _num(q[5]), _pct(q[5] - 1, 0)),
             ("P25", _num(q[25]), _pct(q[25] - 1, 0)),
             ("P50", _num(q[50]), _pct(q[50] - 1, 0)),
             ("P75", _num(q[75]), _pct(q[75] - 1, 0)),
             ("P95", _num(q[95]), _pct(q[95] - 1, 0))],
            "concept",
            leitura="Capital em base 1,0 ao final de 420 operações. As cinco "
                    "linhas descrevem a mesma estratégia, com o mesmo conjunto "
                    "de resultados em ordens diferentes.",
            rodape="2.000 reamostragens iid · f = 1% do capital por operação"),
        cards.grafico(
            "Distribuição do drawdown máximo",
            plot_mdd, "concept",
            leitura=f"Drawdown máximo de cada uma das 2.000 trajetórias. "
                    f"Percentil 5 em {_pct(mdd_p95, 1)}; mediana em "
                    f"{_pct(float(np.quantile(mdds, 0.5)), 1)}. A série "
                    f"observada registrou "
                    f"{_pct(metrics.risco.max_drawdown(EST.diario), 1)}.",
            rodape=FONTE_PADRAO),
        cards.codigo(
            "Cálculo dos percentis do drawdown",
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
            leitura="Convenção do módulo: P95 nomeia o percentil de severidade, "
                    "que corresponde ao quantil 5 da distribuição de drawdowns.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "Questões não cobertas",
            ["O bootstrap iid apaga a dependência temporal. Sob reamostragem "
             "por blocos, qual é a largura da banda?",
             "Para um limite de drawdown declarado, qual é a fração f "
             "compatível com ele?",
             "Com que tamanho de amostra o intervalo do edge deixaria de "
             "conter o zero?"],
            "concept",
            proximo="Endereços no repositório: stationary_bootstrap, "
                    "kelly_fraction e min_track_record_length.",
            rodape=f"Politis & Romano (1994) · {REPO}"),
    ]


# =============================================================================
# POST 002 — Concept — retorno idêntico, perfis de risco distintos
# =============================================================================
def post_002():
    met = {}
    for nome in ("A", "B"):
        s = PAR[nome]
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
            ax.annotate(f"série {nome}", xy=(cap.index[-1], cap.iloc[-1]),
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
            ax.annotate(nome, xy=(dd.index[dd.values.argmin()], dd.min()),
                        xytext=(10, 6), textcoords="offset points", color=cor,
                        fontsize=13, fontweight="semibold")
        ax.axhline(0, color=brand.LINHA_SUTIL, lw=1)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("drawdown", color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Duas séries com retorno acumulado idêntico e risco distinto",
            "concept", numero="002 · MEDIDAS DE RISCO",
            apoio=f"{_pct(met['A']['ret'], 2)} no período em ambas, por "
                  f"construção. Drawdown máximo de {_pct(met['A']['mdd'], 1)} e "
                  f"{_pct(met['B']['mdd'], 1)}."),
        cards.grafico(
            "Retorno acumulado das duas séries",
            plot_curvas, "concept",
            leitura="As séries são geradas com a mesma deriva e volatilidades "
                    "diferentes, depois reescaladas para fechar no mesmo "
                    "retorno. A trajetória é a única variável livre.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "Métricas comparadas",
            ("Métrica", "Série A", "Série B"),
            [("Retorno no período", _pct(met["A"]["ret"], 2), _pct(met["B"]["ret"], 2)),
             ("Volatilidade anual", _pct(met["A"]["vol"], 1).lstrip("+"),
              _pct(met["B"]["vol"], 1).lstrip("+")),
             ("Drawdown máximo", _pct(met["A"]["mdd"], 1), _pct(met["B"]["mdd"], 1)),
             ("Tempo abaixo do pico", f"{met['A']['tuw']:.0%}", f"{met['B']['tuw']:.0%}"),
             ("Ulcer Index", _num(met["A"]["ulcer"], 3), _num(met["B"]["ulcer"], 3)),
             ("Calmar", _num(met["A"]["calmar"]), _num(met["B"]["calmar"]))],
            "concept",
            leitura=f"Razão entre as séries: volatilidade "
                    f"{_num(met['B']['vol'] / met['A']['vol'], 1)}×, drawdown "
                    f"máximo {_num(met['B']['mdd'] / met['A']['mdd'], 1)}×, "
                    f"Ulcer {_num(met['B']['ulcer'] / met['A']['ulcer'], 1)}×.",
            rodape="Definições em wizzlab.metrics.risco"),
        cards.grafico(
            "Drawdown das duas séries",
            plot_dd, "concept",
            leitura=f"Queda percentual desde o pico anterior, dia a dia. A série "
                    f"B permanece {met['B']['tuw']:.0%} do período abaixo do "
                    f"próprio pico; a série A, {met['A']['tuw']:.0%}.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "Ulcer Index",
            r"UI = \sqrt{\frac{1}{T}\sum_{t=1}^{T} D_t^{\,2}}",
            [(r"D_t", "drawdown percentual no instante t"),
             (r"T", "número de períodos observados")],
            "concept",
            leitura="A média dos quadrados no tempo pondera profundidade e "
                    "permanência. O drawdown máximo registra apenas o extremo "
                    "de um instante.",
            rodape="Martin & McCann · Manual de Validação, métrica 24"),
        cards.codigo(
            "Cálculo de Ulcer Index e Calmar",
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
            leitura="Calmar usa o drawdown máximo no denominador; Ulcer usa a "
                    "série inteira. A razão entre os dois indicadores difere "
                    "conforme o risco esteja concentrado ou distribuído.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "Questões não cobertas",
            ["Em que condições Ulcer Index e Calmar ordenam duas séries de "
             "forma oposta?",
             "Entre profundidade e duração, qual se associa mais ao abandono "
             "da estratégia por quem a opera?",
             "Qual é a frequência com que duas séries de mesmo retorno diferem "
             "por acaso amostral, e não por estrutura?"],
            "concept",
            proximo="A terceira exige simulação sob hipótese nula. Notebook 2 "
                    "do repositório.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


# =============================================================================
# POST 003 — Portfolio — critérios de medição, definidos ex ante
# =============================================================================
def post_003():
    def plot_divulgacao(ax):
        rotulos = ["Retorno\nvs índice", "Drawdown\ne duração", "Caixa e\nconcentração",
                   "Giro e\ncusto"]
        frequencia = [1.00, 0.62, 0.18, 0.07]
        x = np.arange(len(rotulos))
        cores = [brand.COBRE if v < 0.25 else brand.TEXTO_METADADO_ESCURO
                 for v in frequencia]
        ax.bar(x, frequencia, width=.62, color=cores,
               edgecolor=brand.AZUL_PETROLEO, lw=2)
        ax.set_xticks(x)
        ax.set_xticklabels(rotulos, fontsize=10.5,
                           color=brand.TEXTO_METADADO_ESCURO)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("fração que divulga",
                      color=brand.TEXTO_METADADO_ESCURO, fontsize=11)
        ax.set_ylim(0, 1.12)

    return [
        cards.capa(
            "Critérios de medição da carteira, definidos antes da primeira posição",
            "portfolio", numero="003 · CONTA REAL",
            apoio="Sete itens, com frequência declarada. Concentração medida "
                  "por HHI e número efetivo de posições."),
        cards.conceito(
            "Registro anterior ao resultado",
            "O critério publicado antes do dado permite distinguir método de "
            "acaso depois. Publicado após o dado, não permite — porque qualquer "
            "resultado adverso admite reinterpretação.\n\n"
            "A data deste post é o registro do critério.",
            "portfolio",
            rodape="Manual de Marca Wizz V2 · seções 8 e 9"),
        cards.tabela(
            "Itens publicados em cada fechamento",
            ("Item", "Forma", "Frequência"),
            [("Retorno acumulado", "vs CDI e índice", "Mensal"),
             ("Drawdown máximo", "% e duração", "Mensal"),
             ("Caixa", "% do patrimônio", "Mensal"),
             ("Concentração", "HHI e nº efetivo", "Mensal"),
             ("Giro", "% do patrimônio", "Trimestral"),
             ("Custo pago", "R$ e % ", "Trimestral"),
             ("Decisões revertidas", "tese e causa", "Quando ocorrerem")],
            "portfolio",
            leitura="A frequência faz parte do compromisso: um item divulgado "
                    "só quando favorece deixa de ser medida.",
            rodape="Formato fixo a partir do primeiro fechamento"),
        cards.grafico(
            "Frequência de divulgação em carteiras públicas",
            plot_divulgacao, "portfolio",
            leitura="Giro e custo são os itens que mais explicam a diferença "
                    "entre resultado simulado e resultado de conta, e os menos "
                    "divulgados nesta amostra.",
            rodape="Estimativa qualitativa do autor sobre carteiras públicas "
                   "brasileiras · não é levantamento amostral"),
        cards.conceito(
            "Escopo da publicação",
            "Posições em peso percentual; valores absolutos são opcionais.\n\n"
            "O material é o registro de um processo de decisão, com finalidade "
            "educacional. Não é carteira recomendada, ranking de performance "
            "nem chamada para replicação.",
            "portfolio",
            rodape="Conteúdo educacional · não constitui recomendação"),
        cards.codigo(
            "Cálculo da concentração",
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
            leitura=f"Nesses pesos, seis posições correspondem a "
                    f"{_num(float(BREADTH_EXEMPLO))} posições equivalentes. O "
                    "número efetivo é o que será publicado, ao lado da "
                    "contagem nominal.",
            rodape=f"Métricas 106 e 107 · {REPO}"),
        cards.em_aberto(
            "Definições pendentes",
            ["Qual é o limite de concentração aceitável, em HHI e em número "
             "efetivo?",
             "Qual giro anual o edge desta carteira comporta antes de zerar?",
             "Qual evidência encerraria a carteira inteira, e não apenas uma "
             "posição?"],
            "portfolio",
            proximo="A segunda é o break-even cost, métrica 109. A terceira "
                    "será publicada antes da primeira compra.",
            rodape=f"Métrica 145, kill-switch ex ante · {REPO}"),
    ]


# =============================================================================
# POST 004 — Data — convexidade da recuperação
# =============================================================================
def post_004():
    quedas = np.array([.10, .20, .30, .40, .50, .60, .70, .80])
    necessario = quedas / (1 - quedas)
    anos = np.log(1 / (1 - quedas)) / np.log(1.10)

    def plot_barras(ax):
        x = np.arange(len(quedas))
        ax.bar(x - .19, quedas, width=.38, color=brand.CINZA_SALVIA,
               edgecolor=brand.MARFIM, lw=2, label="queda")
        ax.bar(x + .19, necessario, width=.38, color=brand.COBRE,
               edgecolor=brand.MARFIM, lw=2, label="alta exigida")
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
        ax.set_ylabel("anos a 10% a.a.", color=brand.CINZA_SALVIA, fontsize=11)
        for xi, yi in list(zip(quedas, anos))[::3]:
            ax.annotate(_br(f"{yi:.1f}"), xy=(xi, yi), xytext=(-8, 12),
                        textcoords="offset points", ha="right", fontsize=11.5,
                        color=brand.AZUL_PETROLEO, fontweight="semibold")

    return [
        cards.capa(
            "Relação entre queda percentual e alta necessária para recuperação",
            "data", numero="004 · ARITMÉTICA",
            apoio="g* = q/(1−q). Para q = 0,50, g* = 1,00. Para q = 0,80, "
                  "g* = 4,00. A função diverge quando q tende a 1."),
        cards.formula(
            "Exigência de recuperação",
            r"g^{*} = \frac{q}{1 - q}",
            [(r"q", "queda percentual sofrida"),
             (r"g^{*}", "alta necessária para retornar ao capital inicial")],
            "data",
            leitura="A alta incide sobre a base já reduzida pela queda, o que "
                    "torna a relação convexa. Identidade aritmética, sem "
                    "premissa de distribuição.",
            rodape="Manual de Validação · leitura de drawdown, cap. 03"),
        cards.tabela(
            "Tabela de recuperação",
            ("Queda", "Alta exigida", "Razão"),
            [(f"−{q:.0%}", _br(f"+{g:.1%}"), _br(f"{g / q:.2f}×"))
             for q, g in zip(quedas, necessario)],
            "data",
            leitura="A razão entre alta exigida e queda sofrida parte de 1,11 "
                    "em q = 0,10 e chega a 5,00 em q = 0,80.",
            rodape="Valores exatos"),
        cards.grafico(
            "Queda sofrida e alta necessária",
            plot_barras, "data",
            leitura="As duas barras permanecem próximas até q = 0,30 e se "
                    "separam progressivamente a partir daí.",
            rodape="Identidade aritmética"),
        cards.grafico(
            "Tempo de recuperação a 10% a.a.",
            plot_anos, "data",
            leitura=f"A mesma relação expressa em anos de retorno composto a "
                    f"10% a.a. necessários para retornar ao capital inicial. "
                    f"Para q = 0,70, {_num(float(anos[6]), 1)} anos.",
            rodape="Rótulos em 10%, 40% e 70%"),
        cards.codigo(
            "Cálculo da tabela",
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
            leitura="Colunas: queda, alta exigida e anos a 10% a.a. A terceira "
                    "supõe retorno composto constante e nenhum aporte.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "Questões não cobertas",
            ["Limitar a perda reduz o retorno esperado por operação. Onde "
             "fica o ponto de equilíbrio entre os dois efeitos?",
             "Qual fração o critério de Kelly indica para esta distribuição?",
             "Como a relação se altera na presença de aportes recorrentes "
             "durante a queda?"],
            "data",
            proximo="As duas primeiras estão em metrics.risco: kelly_fraction "
                    "e risk_of_ruin. A terceira não foi medida.",
            rodape=f"Métricas 38 e 39 · {REPO}"),
    ]


# =============================================================================
# POST 005 — Research — média, mediana e concentração do lucro
# =============================================================================
def post_005():
    media = metrics.trade.expectancy(R)
    mediana = metrics.trade.median_trade(R)
    skew = metrics.trade.skewness(R)
    conc = metrics.sinal.pnl_concentration(R)
    top10 = float(conc.iloc[2])
    wr = metrics.trade.win_rate(R)
    queda_expectancy = 1 - float(SEM_TOP5.iloc[1]) / float(SEM_TOP5.iloc[0])

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
        ax.set_ylabel("nº de operações", color=brand.CINZA_SALVIA, fontsize=11)

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
        ax.set_xlabel("operações vencedoras, ordenadas de forma decrescente",
                      color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("fração do lucro bruto", color=brand.CINZA_SALVIA,
                      fontsize=11)

    return [
        cards.capa(
            "Média e mediana dos resultados em uma amostra de 420 operações",
            "research", numero="005 · DISTRIBUIÇÃO",
            apoio=f"Média {_num(media)}R, mediana {_num(mediana)}R, assimetria "
                  f"{_num(skew)}. As três estatísticas descrevem a mesma "
                  "amostra."),
        cards.grafico(
            "Distribuição dos resultados por operação",
            plot_hist, "research",
            leitura=f"420 operações, líquidas de custo. {1 - wr:.0%} terminam "
                    "negativas, concentradas próximo de −1R; a cauda direita "
                    "se estende até +7,4R.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "Coeficiente de assimetria",
            r"\gamma_1 = \frac{\mathbb{E}\left[(R - \mu)^3\right]}{\sigma^3}",
            [(r"\mu", "média dos resultados"),
             (r"\sigma", "desvio-padrão"),
             (r"\gamma_1", f"assimetria — nesta amostra, {_num(skew)}")],
            "research",
            leitura="O terceiro momento padronizado mede o desbalanço entre as "
                    "caudas. A estimativa é sensível a outliers e instável em "
                    "amostras pequenas.",
            rodape="Manual de Validação · métrica 11"),
        cards.grafico(
            "Concentração do lucro bruto",
            plot_lorenz, "research",
            leitura=f"Curva de Lorenz sobre as operações positivas. As 10% "
                    f"maiores respondem por {top10:.0%} do lucro bruto; a linha "
                    "tracejada corresponde à distribuição uniforme.",
            rodape=FONTE_PADRAO),
        cards.tabela(
            "Remoção das cinco melhores operações",
            ("Amostra", "Expectancy", "Variação"),
            [("Completa (420)", f"{_num(float(SEM_TOP5.iloc[0]), 3)}R", "—"),
             ("Sem as 5 maiores (415)", f"{_num(float(SEM_TOP5.iloc[1]), 3)}R",
              _pct(-queda_expectancy, 0))],
            "research",
            leitura="Retirada de 1,2% da amostra, correspondente às cinco "
                    "operações de maior resultado. A expectancy permanece "
                    "positiva.",
            rodape="Manual de Validação · métrica 104"),
        cards.codigo(
            "Cálculo do teste de remoção",
            ["from wizzlab import data, metrics",
             "",
             "est = data.gerar_estrategia(semente=42)",
             "r = est.trades.r_multiple.values",
             "",
             "# retira as 5 maiores de 420 operações",
             "print(metrics.sinal.remove_best_trades(r, 5))"],
            saida=[f"expectancy original   {_num(float(SEM_TOP5.iloc[0]), 3)}",
                   f"sem as 5 maiores      {_num(float(SEM_TOP5.iloc[1]), 3)}",
                   f"ainda positiva        {SEM_TOP5.iloc[2]}"],
            serie="research",
            leitura="O mesmo procedimento aplicado às cinco piores operações "
                    "está em remove_worst_trades, e distingue perda recorrente "
                    "de evento isolado.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.referencias(
            "Referências",
            [("Bailey, D. H.; López de Prado, M. (2014). The Deflated Sharpe "
              "Ratio: correcting for selection bias and non-normality.",
              "J. Portfolio Management 40(5) · doi 10.3905/jpm.2014.40.5.094"),
             ("Lo, A. W. (2002). The Statistics of Sharpe Ratios.",
              "Financial Analysts Journal 58(4) · doi 10.2469/faj.v58.n4.2453"),
             ("Politis, D. N.; Romano, J. P. (1994). The Stationary Bootstrap.",
              "J. Am. Stat. Assoc. 89(428) · doi 10.1080/01621459.1994.10476870")],
            "research",
            leitura="Assimetria positiva é a estrutura esperada em sistemas "
                    "seguidores de tendência. A literatura trata da distinção "
                    "entre estrutura declarada e estrutura identificada a "
                    "posteriori.",
            rodape=f"Bibliografia completa no repositório · {REPO}"),
    ]


# =============================================================================
# POST 006 — Portfolio — régua de medição
# =============================================================================
def post_006():
    est_cagr = metrics.risco.cagr(EST.diario)
    ben_cagr = metrics.risco.cagr(BENCH)

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
            "Régua de medição: quatro métricas, mesma referência, mesmo período",
            "portfolio", numero="006 · CONTA REAL",
            apoio=f"Decomposição α/β com erro-padrão. Na simulação, "
                  f"β = {_num(float(REG['beta']))} e "
                  f"t(α) = {_num(float(REG['t_excesso']))}."),
        cards.grafico(
            "Retorno acumulado e referência",
            plot_comparado, "portfolio",
            leitura="Ambas as séries em base 100, no mesmo intervalo. A "
                    "referência é gerada com beta 0,55 em relação à carteira, "
                    "mais ruído independente.",
            rodape=FONTE_PADRAO),
        cards.formula(
            "Decomposição do retorno",
            r"r_t = \alpha + \beta\,r^{m}_{t} + \varepsilon_t",
            [(r"r_t", "retorno da carteira no período t"),
             (r"r^{m}_{t}", "retorno da referência no mesmo período"),
             (r"\beta", "sensibilidade ao movimento da referência"),
             (r"\alpha", "componente não explicado pela referência")],
            "portfolio",
            leitura="Regressão por mínimos quadrados sobre retornos diários. O "
                    "erro-padrão de α determina se o componente é distinguível "
                    "de zero na amostra disponível.",
            rodape="Manual de Validação · métricas 150 e 151"),
        cards.tabela(
            "Métricas do fechamento",
            ("Métrica", "Carteira", "Referência"),
            [("Retorno anualizado", _pct(est_cagr, 1), _pct(ben_cagr, 1)),
             ("Drawdown máximo", _pct(metrics.risco.max_drawdown(EST.diario), 1),
              _pct(metrics.risco.max_drawdown(BENCH), 1)),
             ("Tempo abaixo do pico",
              f"{metrics.risco.time_under_water(EST.diario):.0%}",
              f"{metrics.risco.time_under_water(BENCH):.0%}"),
             ("Sharpe", _num(metrics.risco.sharpe(EST.diario)),
              _num(metrics.risco.sharpe(BENCH)))],
            "portfolio",
            leitura="Caixa, concentração, giro e custo entram na mesma tabela "
                    "a partir do primeiro fechamento com posição aberta.",
            rodape="Valores da simulação — a carteira real não iniciou"),
        cards.conceito(
            "Critérios de comparação",
            "A referência permanece fixa ao longo da série.\n\n"
            "O início da contagem é a data da primeira posição, definida antes "
            "de qualquer resultado.\n\n"
            "Os valores são líquidos de custo e imposto.\n\n"
            "Alteração em qualquer um dos três é publicada com a série "
            "recalculada nos dois critérios.",
            "portfolio",
            rodape="Escolha de janela e de benchmark são formas de "
                   "data-snooping documentadas no Manual, métrica 137"),
        cards.codigo(
            "Cálculo de α e β",
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
            leitura=f"t = {_num(float(REG['t_excesso']))}, abaixo do valor "
                    "crítico usual de 2. O relatório reporta o coeficiente "
                    "acompanhado do t, em todas as edições.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "Questões não cobertas",
            ["Índice amplo e cesta setorial podem ordenar a mesma carteira de "
             "forma oposta. Qual referência se aplica?",
             "Com que tamanho de amostra o t do excesso superaria 2, mantido "
             "o mesmo excesso por período?",
             "Que parcela do beta decorre de escolha e que parcela decorre da "
             "composição do universo elegível?"],
            "portfolio",
            proximo="A primeira é o assunto da semana 18. A segunda é o "
                    "Minimum Track Record Length, métrica 47.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


# Título do post = título da capa. Os dois eram diferentes enquanto o título do
# plano editorial era um gancho e a capa era descritiva; com o registro
# informativo, a duplicidade deixou de fazer sentido.
ROTEIROS = {
    "post-001-incerteza": (
        "Dispersão do capital final sob reamostragem de trajetórias",
        "Concept", 1, "Terça", post_001),
    "post-002-duas-carteiras": (
        "Duas séries com retorno acumulado idêntico e risco distinto",
        "Concept", 1, "Quinta", post_002),
    "post-003-regras": (
        "Critérios de medição da carteira, definidos antes da primeira posição",
        "Portfolio", 1, "Domingo", post_003),
    "post-004-assimetria": (
        "Relação entre queda percentual e alta necessária para recuperação",
        "Data", 2, "Terça", post_004),
    "post-005-media-engana": (
        "Média e mediana dos resultados em uma amostra de 420 operações",
        "Research", 2, "Quinta", post_005),
    "post-006-medir": (
        "Régua de medição: quatro métricas, mesma referência, mesmo período",
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
