"""Gerador único do programa editorial. Dois trilhos, cinco cards cada.

Por que este arquivo substitui os três anteriores
-------------------------------------------------
O programa tinha cinco séries, três fontes de dado e carrosséis de sete cards
com oito formatos diferentes. Era coerente no visual e incoerente no editorial:
não dava para dizer, olhando os cards, o que a conta é.

Agora são dois trilhos, e só:

**MÉTRICAS** — como avaliar um portfólio. Vale para qualquer carteira, não só
para esta. Dados simulados, declarados como tais. O código é aberto e serve a
quem quiser medir a própria carteira.

**RESULTADOS** — o que esta carteira entregou. Só saída medida.

A linha entre os dois trilhos, e a regra que não se quebra
----------------------------------------------------------
O trilho de resultados publica **resultado**, nunca **método**.

Resultado: retorno, referência, volatilidade, drawdown, excesso ajustado com
erro-padrão, beta, caixa, número de posições.

Método: como as empresas são avaliadas, que filtros de elegibilidade existem,
como a posição é dimensionada e quando ela é encerrada. Nada disso aparece —
nem em card, nem em legenda, nem em nome de coluna de CSV.

Cinco cards por carrossel. Sete eram demais.

Rodar::

    python tools/gerar_programa.py
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

from wizzlab import brand, cards, data, metrics, resultados as res  # noqa: E402
from wizzlab.theme import aplicar_tema, eixo_percentual  # noqa: E402

DESTINO = RAIZ / "assets" / "posts"
REPO = "github.com/Gustavofthiesen/wizz-lab"
FONTE_SIM = f"Série simulada, semente 42 · código aberto em {REPO}"
FONTE_REAL = f"Carteira Wizz · {res.PERIODO} · {REPO}"

aplicar_tema()
SIM = data.gerar_estrategia(semente=42)
REF = data.gerar_benchmark(SIM)
JAN = res.janelas()
CHEIA = res.amostra_cheia()
RESERVADA = res.reservada()


def _br(t: str) -> str:
    return t.replace(".", ",").replace("-", "−")


def _pct(x, casas=1) -> str:
    return _br(f"{x * 100:+.{casas}f}%")


def _pct0(x, casas=1) -> str:
    return _pct(x, casas).lstrip("+")


def _num(x, casas=2) -> str:
    return _br(f"{x:.{casas}f}")


ROTULO = {"2017-19": "2017–19", "2020-21": "2020–21",
          "2022-23": "2022–23", "2024-26": "2024–26"}


# =============================================================================
# TRILHO A — MÉTRICAS DE AVALIAÇÃO DE PORTFÓLIO
# =============================================================================
def m01_cagr():
    """Retorno composto: por que a média aritmética não serve."""
    cagr = metrics.risco.cagr(SIM.diario)
    cagr_ref = metrics.risco.cagr(REF)
    media_arit = float(SIM.diario.mean() * 252)

    def plot(ax):
        cap = metrics.risco.curva_capital(SIM.diario) * 100
        ben = metrics.risco.curva_capital(REF) * 100
        ax.plot(cap.index, cap.values, color=brand.VERDE_FLORESTA, lw=2.2)
        ax.plot(ben.index, ben.values, color=brand.COBRE, lw=1.8)
        ax.annotate("carteira", xy=(cap.index[-1], cap.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", color=brand.VERDE_FLORESTA,
                    fontsize=12, fontweight="semibold", va="center")
        ax.annotate("referência", xy=(ben.index[-1], ben.iloc[-1]),
                    xytext=(8, 0), textcoords="offset points",
                    color=brand.COBRE, fontsize=12, fontweight="semibold",
                    va="center")
        ax.axhline(100, color=brand.LINHA_SUTIL, lw=1)
        ax.set_ylabel("índice (base 100)", color=brand.CINZA_SALVIA, fontsize=11)
        ax.margins(x=.22)

    return [
        cards.capa(
            "Retorno composto anual (CAGR)",
            "metrica", numero="MÉTRICA 01",
            apoio="A taxa constante que levaria do capital inicial ao final no "
                  "mesmo prazo. Nesta série: CAGR de "
                  f"{_pct0(cagr, 2)} contra média aritmética de "
                  f"{_pct0(media_arit, 2)}."),
        cards.formula(
            "Definição",
            r"\mathrm{CAGR} = \left(\frac{W_T}{W_0}\right)^{1/n} - 1",
            [(r"W_T", "capital ao final"),
             (r"W_0", "capital inicial"),
             (r"n", "número de anos")],
            "metrica",
            leitura="A média aritmética dos retornos anuais superestima o "
                    "crescimento sempre que houver variação. A diferença cresce "
                    "com a volatilidade.",
            rodape="Identidade, não estimativa"),
        cards.grafico(
            "Capital acumulado contra a referência",
            plot, "metrica",
            leitura=f"Ambas em base 100, no mesmo intervalo. CAGR de "
                    f"{_pct0(cagr, 2)} contra {_pct0(cagr_ref, 2)} da "
                    "referência.",
            rodape=FONTE_SIM),
        cards.tabela(
            "Como ler",
            ("Situação", "Leitura"),
            [("CAGR sem referência", "não é informação"),
             ("CAGR sem período declarado", "não é comparável"),
             ("Média aritmética no lugar", "superestima"),
             ("Janela escolhida depois", "data-snooping")],
            "metrica", destacar=3,
            leitura="A última é a mais comum e a menos discutida: escolher o "
                    "início da série depois de ver o resultado.",
            rodape="Toda publicação da Wizz declara período e referência"),
        cards.codigo(
            "Cálculo",
            ["from wizzlab import metrics",
             "",
             "# retornos diários da sua carteira",
             "print(metrics.risco.cagr(r))"],
            saida=[f"{_num(cagr, 4)}"],
            serie="metrica",
            leitura="Funciona com qualquer série de retornos diários, não só "
                    "com a desta simulação.",
            rodape=f"Executável no Colab · {REPO}"),
    ]


def m02_drawdown():
    """Drawdown: profundidade e duração são riscos distintos."""
    mdd = metrics.risco.max_drawdown(SIM.diario)
    tuw = metrics.risco.time_under_water(SIM.diario)
    ulcer = metrics.risco.ulcer_index(SIM.diario)
    eps = metrics.risco.episodios_drawdown(SIM.diario)

    def plot(ax):
        dd = metrics.risco.serie_drawdown(SIM.diario)
        ax.fill_between(dd.index, dd.values, 0, color=brand.COBRE, alpha=.24,
                        lw=0)
        ax.plot(dd.index, dd.values, color=brand.COBRE, lw=1.8)
        ax.axhline(0, color=brand.LINHA_SUTIL, lw=1)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("queda desde o pico", color=brand.CINZA_SALVIA,
                      fontsize=11)
        fundo = dd.idxmin()
        ax.annotate(f"{_pct(dd.min(), 1)}", xy=(fundo, dd.min()),
                    xytext=(10, 8), textcoords="offset points",
                    color=brand.COBRE, fontsize=12.5, fontweight="semibold")

    return [
        cards.capa(
            "Drawdown: profundidade, duração e persistência",
            "metrica", numero="MÉTRICA 02",
            apoio=f"Nesta série: queda máxima de {_pct(mdd, 1)}, "
                  f"{tuw:.0%} do período abaixo do pico anterior, "
                  f"Ulcer Index de {_num(ulcer, 3)}."),
        cards.formula(
            "As três medidas",
            r"D_t = \frac{W_t}{\max\,W_{s \leq t}} - 1"
            r"\qquad UI = \sqrt{\frac{1}{T}\sum D_t^{\,2}}",
            [(r"D_t", "drawdown no instante t"),
             (r"\max D_t", "queda máxima — um único extremo"),
             (r"UI", "Ulcer Index — profundidade e permanência")],
            "metrica",
            leitura="A queda máxima registra um instante. O tempo abaixo do "
                    "pico registra duração. O Ulcer Index combina os dois ao "
                    "elevar o drawdown ao quadrado e tirar a média no tempo.",
            rodape="Martin & McCann"),
        cards.grafico(
            "A série de drawdown",
            plot, "metrica",
            leitura=f"Queda percentual desde o pico anterior, dia a dia. O "
                    f"episódio mais profundo chegou a {_pct(mdd, 1)}; o período "
                    f"inteiro passou {tuw:.0%} do tempo abaixo de algum pico.",
            rodape=FONTE_SIM),
        cards.tabela(
            "Os episódios mais profundos",
            ("Profundidade", "Duração", "Recuperação"),
            [(_pct(l.profundidade, 1),
              f"{int(l.duracao)} dias" if pd.notna(l.duracao) else "em curso",
              f"{int(l.tempo_recuperacao)} dias"
              if pd.notna(l.tempo_recuperacao) else "—")
             for _, l in eps.head(4).iterrows()],
            "metrica", destacar=0,
            leitura="Dois episódios de mesma profundidade e durações muito "
                    "diferentes não são o mesmo risco para quem opera.",
            rodape="wizzlab.metrics.risco.episodios_drawdown()"),
        cards.codigo(
            "Cálculo",
            ["from wizzlab import metrics as m",
             "",
             "print(m.risco.max_drawdown(r))",
             "print(m.risco.time_under_water(r))",
             "print(m.risco.ulcer_index(r))"],
            saida=[f"queda máxima      {_num(mdd, 4)}",
                   f"tempo abaixo      {_num(tuw, 4)}",
                   f"Ulcer Index       {_num(ulcer, 4)}"],
            serie="metrica",
            leitura="`episodios_drawdown()` devolve a tabela completa, com "
                    "início, fundo, recuperação e duração de cada episódio.",
            rodape=f"Executável no Colab · {REPO}"),
    ]


def m03_sharpe():
    """Sharpe e o que ele supõe."""
    sharpe = metrics.risco.sharpe(SIM.diario)
    sortino = metrics.risco.sortino(SIM.diario)
    calmar = metrics.risco.calmar(SIM.diario)
    skew = metrics.trade.skewness(SIM.diario)
    vol = metrics.risco.volatilidade(SIM.diario)

    def plot(ax):
        nomes = ["Sharpe", "Sortino", "Calmar"]
        vals = [sharpe, sortino, calmar]
        x = np.arange(3)
        barras = ax.bar(x, vals, width=.5, color=brand.VERDE_FLORESTA,
                        edgecolor=brand.MARFIM, lw=2)
        ax.bar_label(barras, labels=[_num(v) for v in vals], padding=5,
                     fontsize=13, color=brand.AZUL_PETROLEO,
                     fontweight="semibold")
        ax.set_xticks(x)
        ax.set_xticklabels(nomes, fontsize=12)
        ax.set_ylim(0, max(vals) * 1.3)
        ax.set_ylabel("razão", color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Sharpe, Sortino e Calmar: três denominadores de risco",
            "metrica", numero="MÉTRICA 03",
            apoio=f"O numerador é o mesmo. Muda o que conta como risco. Nesta "
                  f"série: {_num(sharpe)}, {_num(sortino)} e {_num(calmar)}."),
        cards.formula(
            "O que muda entre as três",
            r"S = \frac{\mu - r_f}{\sigma}\;;\quad"
            r"\mathrm{So} = \frac{\mu - r_f}{\sigma_{\!-}}\;;\quad"
            r"C = \frac{\mathrm{CAGR}}{|\max D|}",
            [(r"\sigma", "desvio total — oscilação para os dois lados"),
             (r"\sigma_{\!-}", "desvio só do que ficou abaixo do alvo"),
             (r"|\max D|", "a queda máxima observada")],
            "metrica",
            leitura="Sharpe trata alta e queda como o mesmo risco. Sortino "
                    "pune só a queda. Calmar usa um único extremo observado, "
                    "e por isso é o mais sensível à amostra.",
            rodape="Lo (2002) · doi 10.2469/faj.v58.n4.2453"),
        cards.grafico(
            "As três sobre a mesma série",
            plot, "metrica",
            leitura=f"Volatilidade anual de {_pct0(vol, 1)}. A diferença entre "
                    "Sharpe e Sortino indica quanto da oscilação está no lado "
                    "favorável.",
            rodape=FONTE_SIM),
        cards.tabela(
            "Onde o Sharpe engana",
            ("Situação", "Efeito sobre o Sharpe"),
            [("Assimetria negativa", "infla — perda rara não entra"),
             ("Caudas pesadas", "infla — σ subestima o extremo"),
             ("Retornos autocorrelacionados", "infla pela anualização"),
             ("Amostra curta", "erro-padrão grande, não reportado")],
            "metrica", destacar=0,
            leitura=f"A assimetria desta série é {_num(skew)}. Sharpe alto com "
                    "assimetria muito negativa descreve ganho constante com "
                    "uma perda que ainda não ocorreu no período medido.",
            rodape="Manual de Validação · métricas 11, 15, 50"),
        cards.codigo(
            "Cálculo",
            ["from wizzlab import metrics as m",
             "",
             "print(m.risco.sharpe(r))",
             "print(m.risco.sortino(r))",
             "print(m.risco.calmar(r))",
             "print(m.trade.skewness(r))   # leia junto"],
            saida=[f"Sharpe      {_num(sharpe)}",
                   f"Sortino     {_num(sortino)}",
                   f"Calmar      {_num(calmar)}",
                   f"assimetria  {_num(skew)}"],
            serie="metrica",
            leitura="A última linha não é opcional: Sharpe sem assimetria ao "
                    "lado é um número sem o aviso que ele precisa.",
            rodape=f"Executável no Colab · {REPO}"),
    ]


def m04_excesso():
    """Excesso ajustado e beta: o que sobra depois do mercado."""
    reg = metrics.execucao.beta_e_alfa(SIM.diario.values, REF.values)
    lo, hi = metrics.evidencia.bootstrap_ci(SIM.diario.values)

    def plot(ax):
        x = REF.values * 100
        y = SIM.diario.values * 100
        ax.scatter(x, y, s=10, color=brand.VERDE_FLORESTA, alpha=.30,
                   edgecolor="none")
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, float(reg["excesso_por_periodo"]) * 100
                + float(reg["beta"]) * xs, color=brand.COBRE, lw=2.4)
        ax.axhline(0, color=brand.LINHA_SUTIL, lw=1)
        ax.axvline(0, color=brand.LINHA_SUTIL, lw=1)
        ax.set_xlabel("retorno da referência, % ao dia",
                      color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylabel("retorno da carteira, % ao dia",
                      color=brand.CINZA_SALVIA, fontsize=11)
        ax.grid(True, axis="both", color=brand.LINHA_SUTIL, lw=.7)

    return [
        cards.capa(
            "Excesso ajustado por risco e beta",
            "metrica", numero="MÉTRICA 04",
            apoio=f"Separa o que é exposição ao mercado do que sobra depois "
                  f"dela. Nesta série: beta de {_num(float(reg['beta']))}, "
                  f"t do excesso de {_num(float(reg['t_excesso']))}."),
        cards.formula(
            "A decomposição",
            r"r_t = \alpha + \beta\,r^{m}_{t} + \varepsilon_t",
            [(r"\beta", "sensibilidade ao movimento da referência"),
             (r"\alpha", "o que a referência não explica"),
             (r"t(\alpha)", "o excesso dividido pelo próprio erro-padrão")],
            "metrica",
            leitura="O coeficiente sozinho não basta. Sem o erro-padrão não há "
                    "como saber se o excesso é distinguível de zero na amostra "
                    "disponível.",
            rodape="Mínimos quadrados sobre retornos diários"),
        cards.grafico(
            "Carteira contra referência, dia a dia",
            plot, "metrica",
            leitura=f"Cada ponto é um pregão. A inclinação da reta é o beta "
                    f"({_num(float(reg['beta']))}); o intercepto é o excesso. "
                    f"R² de {_num(float(reg['r2']))}.",
            rodape=FONTE_SIM),
        cards.tabela(
            "O que reportar junto",
            ("Item", "Nesta série"),
            [("Beta", _num(float(reg["beta"]))),
             ("t do beta", _num(float(reg["t_beta"]))),
             ("Excesso por período", _num(float(reg["excesso_por_periodo"]), 5)),
             ("t do excesso", _num(float(reg["t_excesso"]))),
             ("R²", _num(float(reg["r2"])))],
            "metrica", destacar=3,
            leitura="Valores de t abaixo de 2 indicam estimativa pequena em "
                    "relação ao erro de medição. A linha destacada é a que "
                    "costuma ser omitida.",
            rodape="wizzlab.metrics.execucao.beta_e_alfa()"),
        cards.codigo(
            "Cálculo",
            ["from wizzlab import metrics as m",
             "",
             "# r = carteira, b = referência, mesmo período",
             "print(m.execucao.beta_e_alfa(r, b))"],
            saida=[f"beta            {_num(float(reg['beta']))}",
                   f"t do beta       {_num(float(reg['t_beta']))}",
                   f"t do excesso    {_num(float(reg['t_excesso']))}",
                   f"R quadrado      {_num(float(reg['r2']))}"],
            serie="metrica",
            leitura="A escolha da referência muda o resultado. Índice amplo e "
                    "cesta setorial podem ordenar a mesma carteira de forma "
                    "oposta.",
            rodape=f"Executável no Colab · {REPO}"),
    ]


# =============================================================================
# TRILHO B — RESULTADOS DA CARTEIRA
# =============================================================================
#: As três janelas que participaram da construção. A reservada fica de fora.
_CONSTR = JAN.loc[["2017-19", "2020-21", "2022-23"]]


def r00_abertura():
    """Post de abertura: o que esta conta é, com a medição desconfortável.

    A medição que incomoda entra no card 3, não no sexto mês. Abrir com o
    excesso da amostra cheia e só depois revelar que a janela reservada não
    rejeita o zero seria construir uma expectativa para desmontar mais tarde;
    o público que esta conta quer é justamente o que descontaria isso sozinho.
    """
    return [
        cards.capa(
            "O que esta conta publica",
            "resultado", numero="ABERTURA",
            apoio="Duas coisas, e só: como se avalia um portfólio, com o "
                  "código aberto; e o que esta carteira entregou, medido do "
                  "mesmo jeito que se cobraria de qualquer outra."),
        cards.tabela(
            "Dois trilhos",
            ("Trilho", "O que é", "Dado"),
            [("Métricas", "como avaliar", "simulado"),
             ("Resultados", "o que entregou", "carteira real")],
            "resultado",
            leitura="O trilho de métricas usa série simulada de propósito: "
                    "quando se define o processo gerador, sabe-se qual é a "
                    "resposta certa e dá para conferir se a métrica a "
                    "encontra. O de resultados usa a carteira.",
            rodape=f"{REPO}"),
        cards.tabela(
            "O número que esta conta não esconde",
            ("Janela", "CAGR", "Excesso aj.", "t"),
            # Média geométrica ponderada por pregão: as três janelas têm
            # 672, 495 e 498 dias, e tratá-las como iguais inflaria a de
            # 2022–23, que é a melhor e a mais curta.
            [("Construção (2017–23)", _pct0(
                np.exp((np.log1p(_CONSTR.cagr) * _CONSTR.pregoes).sum()
                       / _CONSTR.pregoes.sum()) - 1, 2),
              "—", "—"),
             ("Reservada (2024–26)", _pct0(RESERVADA.cagr, 2),
              _pct(RESERVADA.alpha, 2), _num(RESERVADA.t_alpha))],
            "resultado", destacar=1,
            leitura=f"Na janela reservada — a que não participou de nenhuma "
                    f"decisão de construção — o excesso ajustado tem t = "
                    f"{_num(RESERVADA.t_alpha)}. Isso não rejeita a hipótese "
                    f"de que o excesso seja zero. Está dito aqui, no começo.",
            rodape=FONTE_REAL),
        cards.conceito(
            "Resultado sai; método não",
            "Sai: retorno, referência, volatilidade, pior queda, excesso "
            "ajustado com erro-padrão, beta, caixa e número de posições.\n\n"
            "Não sai: como as empresas são avaliadas, que filtros de "
            "elegibilidade existem, como a posição é dimensionada e quando "
            "ela é encerrada.\n\n"
            "A separação é o que permite abrir o ferramental de métricas "
            "para qualquer pessoa sem abrir o que produz os números.",
            "resultado",
            rodape="Conteúdo educacional · não é recomendação "
                   "individualizada · resultados passados não garantem "
                   "resultados futuros"),
        cards.codigo(
            "O ferramental é seu",
            ["pip install git+https://github.com/Gustavofthiesen/wizz-lab",
             "",
             "from wizzlab import metrics, resultados",
             "",
             "metrics.risco.resumo(minha_carteira)",
             "resultados.resumo()"],
            saida=["153 métricas · 4 notebooks no Colab"],
            serie="resultado",
            leitura="As 153 métricas existem para responder uma pergunta: "
                    "como distinguir um backtest convincente de uma "
                    "estratégia robusta. Valem para qualquer carteira.",
            rodape=f"{REPO} · MIT"),
    ]


def r01_por_janela():
    """O resultado medido, janela a janela."""
    def plot(ax):
        nomes = [ROTULO[i] for i in JAN.index]
        x = np.arange(len(JAN))
        cores = [brand.COBRE if r else "#7FA99B" for r in JAN.reservada]
        ax.errorbar(x, JAN.alpha,
                    yerr=[JAN.alpha - JAN.ic95_inf, JAN.ic95_sup - JAN.alpha],
                    fmt="none", ecolor=brand.TEXTO_METADADO_ESCURO,
                    elinewidth=1.8, capsize=7, capthick=1.8, zorder=3)
        ax.bar(x, JAN.alpha, width=.5, color=cores,
               edgecolor=brand.AZUL_PETROLEO, lw=2, zorder=2)
        ax.axhline(0, color=brand.MARFIM, lw=1.4)
        ax.set_xticks(x)
        ax.set_xticklabels(nomes)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("excesso ajustado, a.a.",
                      color=brand.TEXTO_METADADO_ESCURO, fontsize=11)
        for xi, (_, l) in zip(x, JAN.iterrows()):
            ax.annotate(f"t = {_num(l.t_alpha)}", xy=(xi, l.ic95_sup),
                        xytext=(0, 8), textcoords="offset points", ha="center",
                        fontsize=11, color=brand.MARFIM, fontweight="semibold")

    return [
        cards.capa(
            "Resultado da carteira, janela a janela",
            "resultado", numero="RESULTADO 01",
            apoio=f"2.315 pregões. Amostra cheia: excesso ajustado de "
                  f"{_pct(CHEIA.alpha, 2)} ao ano, t = {_num(CHEIA.t_alpha)}. "
                  f"Janela reservada: {_pct(RESERVADA.alpha, 2)}, "
                  f"t = {_num(RESERVADA.t_alpha)}."),
        cards.tabela(
            "Os números",
            ("Janela", "CAGR", "CDI", "Excesso aj.", "t"),
            [(ROTULO[i], _pct0(l.cagr, 2), _pct0(l.cdi, 2),
              _pct(l.alpha, 2), _num(l.t_alpha)) for i, l in JAN.iterrows()]
            + [("Amostra cheia", _pct0(CHEIA.cagr, 2), _pct0(CHEIA.cdi, 2),
                _pct(CHEIA.alpha, 2), _num(CHEIA.t_alpha))],
            "resultado", destacar=3,
            leitura="A linha destacada é a janela reservada: não participou de "
                    "nenhuma decisão de construção. É a única cujo excesso "
                    "pode ser lido sem desconto por seleção.",
            rodape=FONTE_REAL),
        cards.grafico(
            "Excesso ajustado e intervalo de 95%",
            plot, "resultado",
            leitura=f"Barras: excesso anualizado. Hastes: intervalo de "
                    f"confiança. Em 2024–26 o intervalo é "
                    f"[{_pct(RESERVADA.ic95_inf, 1)}; "
                    f"{_pct(RESERVADA.ic95_sup, 1)}] e contém o zero.",
            rodape=FONTE_REAL),
        cards.tabela(
            "Risco por janela",
            ("Janela", "Volatilidade", "Pior queda", "Sharpe"),
            [(ROTULO[i], _pct0(l.volatilidade, 1), _pct(l.pior_queda, 1),
              _num(l.sharpe)) for i, l in JAN.iterrows()],
            "resultado", destacar=3,
            leitura=f"O Sharpe da janela reservada é "
                    f"{_num(RESERVADA.sharpe)}, contra "
                    f"{_num(JAN.loc['2022-23'].sharpe)} na melhor janela do "
                    "período de construção.",
            rodape=FONTE_REAL),
        cards.codigo(
            "Como conferir",
            ["from wizzlab import resultados",
             "",
             "print(resultados.carregar())",
             "print(resultados.resumo())"],
            saida=[f"cheia       {_num(CHEIA.alpha, 4)}   t {_num(CHEIA.t_alpha)}",
                   f"reservada   {_num(RESERVADA.alpha, 4)}   t {_num(RESERVADA.t_alpha)}"],
            serie="resultado",
            leitura="O repositório publica os resultados medidos. O método que "
                    "os produziu não é aberto, e isso está declarado no módulo.",
            rodape=f"data/resultados_publicados.csv · {REPO}"),
    ]


def r02_ressalvas():
    """O que os números não dizem."""
    def plot(ax):
        nomes = ["recomposição", "cache de cálculo"]
        pisos = [0.005, 0.024]
        y = np.arange(len(nomes))[::-1]
        barras = ax.barh(y, pisos, height=.42, color=brand.COBRE,
                         edgecolor=brand.AZUL_PETROLEO, lw=2)
        ax.bar_label(barras,
                     labels=[_br(f"±{v * 100:.1f} p.p.") for v in pisos],
                     padding=6, fontsize=13, color=brand.MARFIM,
                     fontweight="semibold")
        ax.set_yticks(y)
        ax.set_yticklabels(nomes, fontsize=12)
        ax.set_xlim(0, 0.033)
        eixo_percentual(ax, "x", 1)
        ax.grid(False, axis="y")
        ax.set_xlabel("variação de CAGR sem conteúdo econômico",
                      color=brand.TEXTO_METADADO_ESCURO, fontsize=11)

    return [
        cards.capa(
            "O que estes números não dizem",
            "resultado", numero="RESULTADO 02",
            apoio="Cinco limitações da medição, declaradas junto do resultado. "
                  "Elas ficam no código, ao lado dos dados, para não "
                  "circularem separadas deles."),
        cards.tabela(
            "As cinco ressalvas",
            ("Limitação", "Efeito"),
            [("Simulação histórica", "não é conta executada"),
             ("Viés de sobrevivência", "universo favorece quem restou"),
             ("Piso de ruído", "±2,4 p.p. sem conteúdo"),
             ("Exposição setorial", "parte do excesso não é seleção"),
             ("Escolha entre candidatas", "probabilidade de overfitting alta")],
            "resultado", destacar=4,
            leitura="A última é a razão de a janela reservada ser a leitura "
                    "que vale, e não a amostra cheia.",
            rodape="wizzlab.resultados.RESSALVAS"),
        cards.grafico(
            "Piso de ruído medido por intervenção-placebo",
            plot, "resultado",
            leitura="Variação de CAGR produzida por intervenções sem conteúdo "
                    "econômico. Diferenças menores que o piso não são "
                    "distinguíveis de ruído de implementação.",
            rodape=f"Medição própria · {REPO}"),
        cards.conceito(
            "Por que isto sai junto do número",
            "Um resultado sem as suas limitações não é um resultado "
            "incompleto: é um resultado diferente do que foi medido.\n\n"
            "As cinco ressalvas estão em `resultados.RESSALVAS`, no mesmo "
            "módulo que carrega a tabela. Quem usa o dado recebe as duas "
            "coisas na mesma importação.",
            "resultado",
            rodape="Conteúdo educacional · resultados passados não garantem "
                   "resultados futuros"),
        cards.codigo(
            "As ressalvas vêm com os dados",
            ["from wizzlab import resultados",
             "",
             "for nota in resultados.RESSALVAS:",
             "    print(nota)"],
            saida=["5 ressalvas declaradas"],
            serie="resultado",
            leitura="O registro ao vivo começa em 2026 e não tem nenhuma "
                    "dessas limitações de seleção. É o dado que vai valer.",
            rodape=f"{REPO}"),
    ]


# =============================================================================
PROGRAMA = {
    # trilho, slug, título, fábrica
    "metricas": [
        ("m01-cagr", "Retorno composto anual (CAGR)", m01_cagr),
        ("m02-drawdown", "Drawdown: profundidade, duração e persistência",
         m02_drawdown),
        ("m03-sharpe", "Sharpe, Sortino e Calmar: três denominadores de risco",
         m03_sharpe),
        ("m04-excesso", "Excesso ajustado por risco e beta", m04_excesso),
    ],
    "resultados": [
        ("r00-abertura", "O que esta conta publica", r00_abertura),
        ("r01-por-janela", "Resultado da carteira, janela a janela",
         r01_por_janela),
        ("r02-ressalvas", "O que estes números não dizem", r02_ressalvas),
    ],
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    manifesto = []
    for trilho, posts in PROGRAMA.items():
        for slug, titulo, fabrica in posts:
            for antigo in DESTINO.glob(f"{slug}-*.png"):
                antigo.unlink()
            problemas = brand.checar_titulo(titulo)
            if problemas:
                raise SystemExit(f"{slug}: termo banido {problemas}")
            caminhos = cards.carrossel(fabrica(), slug, str(DESTINO))
            manifesto.append({"trilho": trilho, "slug": slug, "titulo": titulo,
                              "n_cards": len(caminhos),
                              "arquivos": [pathlib.Path(c).name
                                           for c in caminhos]})
            print(f"{trilho:11} {slug:16} {len(caminhos)} cards")

    destino = DESTINO / "manifest_programa.json"
    destino.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"\n{destino.name}: {len(manifesto)} posts")


if __name__ == "__main__":
    main()
