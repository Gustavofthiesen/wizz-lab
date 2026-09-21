"""Economia do trade e distribuicao de resultados (metricas 1-14).

Capitulo 01 do *Manual de Validacao de Estrategias Sistematicas*. E por aqui
que se comeca: antes de qualquer ratio sofisticado, entenda como os trades
ganham e perdem e se o valor esperado continua positivo depois de custos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _arr(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[~np.isnan(a)]


# --- 1 -----------------------------------------------------------------------
def expectancy(r) -> float:
    """**Quanto a estrategia tende a ganhar ou perder por operacao?**

    ``E = p_W * W - p_L * |L|``

    E o valor esperado economico de uma operacao -- que, para uma amostra, e
    simplesmente a media. Calcule sempre liquido de custos.

    Expectancy positiva e condicao *necessaria* para um sistema lucrativo, mas
    nao prova robustez: ela pode ter sido criada por poucos outliers, sumir
    apos custos ou mudar de sinal fora da amostra.
    """
    a = _arr(r)
    return float(a.mean()) if a.size else float("nan")


# --- 2 -----------------------------------------------------------------------
def expectancy_r(pnl, risco_inicial) -> float:
    """**O edge continua comparavel quando o tamanho das posicoes muda?**

    ``R_i = PnL_i / RiscoInicial_i`` e depois ``E[R]``.

    Normaliza cada trade pelo risco assumido na entrada. +0,20R significa ganho
    medio de 0,20 unidade de risco por trade, independentemente do valor
    nominal da posicao.

    Cuidado: se o risco inicial e mal definido, se os stops sao discricionarios
    ou se a posicao muda durante o trade, o R deixa de ser comparavel.
    """
    p = np.asarray(pnl, float)
    risco = np.asarray(risco_inicial, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(risco != 0, p / risco, np.nan)
    return expectancy(r)


# --- 3 e 4 -------------------------------------------------------------------
def win_rate(r) -> float:
    """**Com que frequencia os trades terminam positivos?** ``WR = N_W / N``

    Mede frequencia, nao qualidade. Uma estrategia pode ganhar com 30% de
    acerto se os winners forem muito maiores; outra pode perder com 80% se
    houver perdas raras e enormes. Otimizar para acerto costuma piorar a
    assimetria e o risco de cauda.
    """
    a = _arr(r)
    return float((a > 0).mean()) if a.size else float("nan")


def loss_rate(r) -> float:
    """**Qual a frequencia das operacoes perdedoras?** ``LR = 1 - WR``

    Serve principalmente para streaks, risco de ruina e sizing. Uma taxa
    aparentemente pequena pode esconder perdas muito grandes ou gap risk.
    """
    a = _arr(r)
    return float((a < 0).mean()) if a.size else float("nan")


# --- 5 -----------------------------------------------------------------------
def payoff_ratio(r) -> float:
    """**Quanto o ganho medio compensa a perda media?** ``Payoff = W / |L|``

    Em conjunto com o win rate, determina a expectancy basica. Desconfie de
    payoff alto produzido por um ou dois winners extremos -- compare media e
    mediana dos vencedores.
    """
    a = _arr(r)
    w, l = a[a > 0], a[a < 0]
    if not w.size or not l.size:
        return float("nan")
    return float(w.mean() / abs(l.mean()))


# --- 6 -----------------------------------------------------------------------
def break_even_win_rate(r) -> float:
    """**Qual taxa minima de acerto e necessaria para nao perder dinheiro?**

    ``WR_BE = |L| / (W + |L|)``

    Transforma o payoff em uma taxa de acerto de equilibrio. O excesso do win
    rate real sobre ela e uma margem intuitiva de edge -- e uma margem de
    poucos pontos percentuais e a que desaparece com slippage.
    """
    a = _arr(r)
    w, l = a[a > 0], a[a < 0]
    if not w.size or not l.size:
        return float("nan")
    ganho, perda = w.mean(), abs(l.mean())
    return float(perda / (ganho + perda))


def margem_de_edge(r) -> float:
    """Win rate observado menos o break-even. Positivo e o que se quer ver."""
    return win_rate(r) - break_even_win_rate(r)


# --- 7 -----------------------------------------------------------------------
def profit_factor(r) -> float:
    """**Quanto lucro bruto para cada unidade de perda bruta?**

    ``PF = GrossProfit / |GrossLoss|``

    Heuristica, nao corte universal: 1,1 e fragil; 1,3-1,5 comeca a
    interessar; valores muito altos pedem investigacao de amostra, custos e
    overfitting. PF nao e significancia estatistica.
    """
    a = _arr(r)
    ganho, perda = a[a > 0].sum(), abs(a[a < 0].sum())
    if perda == 0:
        return float("inf") if ganho > 0 else float("nan")
    return float(ganho / perda)


# --- 8 -----------------------------------------------------------------------
def average_winner(r) -> float:
    """**Qual a magnitude tipica de um ganho?** ``W = E[PnL | PnL > 0]``"""
    a = _arr(r)
    w = a[a > 0]
    return float(w.mean()) if w.size else float("nan")


def average_loser(r) -> float:
    """**Qual a magnitude tipica de uma perda?** ``L = E[PnL | PnL < 0]``

    Junto com :func:`average_winner`, mostra se o sistema corta perdas e deixa
    ganhos correr, ou se acumula pequenos ganhos com perdas grandes.
    """
    a = _arr(r)
    l = a[a < 0]
    return float(l.mean()) if l.size else float("nan")


# --- 9 -----------------------------------------------------------------------
def median_trade(r) -> float:
    """**O trade tipico e lucrativo, ou a media depende de extremos?**

    A mediana resiste a outliers. Media > 0 com mediana < 0 nao e
    necessariamente ruim: revela um sistema que depende de cauda positiva,
    comum em trend following. Mas precisa ser uma escolha consciente.
    """
    a = _arr(r)
    return float(np.median(a)) if a.size else float("nan")


# --- 10 ----------------------------------------------------------------------
def largest_winner(r) -> float:
    """**Qual foi o melhor trade?** Diagnostico, nao ratio de qualidade."""
    a = _arr(r)
    return float(a.max()) if a.size else float("nan")


def largest_loser(r) -> float:
    """**Qual foi a pior perda?**

    Revela gap risk, stop failure e caudas gordas. Se uma perda excede muito o
    risco modelado, o problema nao e de performance -- e de execucao.
    """
    a = _arr(r)
    return float(a.min()) if a.size else float("nan")


# --- 11 ----------------------------------------------------------------------
def skewness(r) -> float:
    """**A distribuicao tem cauda maior para ganhos ou para perdas?**

    ``Skew = E[(R-mu)^3] / sigma^3``

    Skew positivo indica cauda direita. Trend following aceita muitos pequenos
    losses em troca disso; short-vol e mean reversion costumam exibir skew
    negativo. O sinal de perigo classico: Sharpe alto com skew fortemente
    negativo e perdas extremas ainda nao observadas no periodo.
    """
    a = _arr(r)
    if a.size < 3:
        return float("nan")
    return float(((a - a.mean()) ** 3).mean() / a.std(ddof=0) ** 3)


# --- 12 ----------------------------------------------------------------------
def excess_kurtosis(r) -> float:
    """**Com que frequencia aparecem retornos extremos?** ``Kurt - 3``

    Kurtosis elevada sugere caudas pesadas, o que torna inferencia normal, VaR
    parametrico e anualizacao simplista menos confiaveis.
    """
    a = _arr(r)
    if a.size < 4:
        return float("nan")
    return float(((a - a.mean()) ** 4).mean() / a.std(ddof=0) ** 4 - 3)


# --- 13 ----------------------------------------------------------------------
def tail_ratio(r, q: float = 0.05) -> float:
    """**A cauda positiva e maior que a negativa?**

    Razao entre o quantil superior e o modulo do inferior. Acima de 1, a cauda
    boa domina. Estimativa instavel em amostra pequena.
    """
    a = _arr(r)
    if a.size < 20:
        return float("nan")
    alto, baixo = np.quantile(a, 1 - q), abs(np.quantile(a, q))
    return float(alto / baixo) if baixo else float("nan")


# --- 14 ----------------------------------------------------------------------
def iqr(r) -> float:
    """**Qual a dispersao robusta da distribuicao?** Q3 - Q1."""
    a = _arr(r)
    if not a.size:
        return float("nan")
    return float(np.quantile(a, 0.75) - np.quantile(a, 0.25))


def mad(r) -> float:
    """Desvio absoluto mediano: dispersao que nao se deixa levar por extremos."""
    a = _arr(r)
    return float(np.median(np.abs(a - np.median(a)))) if a.size else float("nan")


# --- resumo ------------------------------------------------------------------
def resumo(r) -> pd.Series:
    """Devolve o capitulo 01 inteiro em uma unica Series, pronta para exibir."""
    return pd.Series({
        "Expectancy (R)": expectancy(r),
        "Win rate": win_rate(r),
        "Loss rate": loss_rate(r),
        "Payoff ratio": payoff_ratio(r),
        "Break-even WR": break_even_win_rate(r),
        "Margem de edge": margem_de_edge(r),
        "Profit factor": profit_factor(r),
        "Average winner": average_winner(r),
        "Average loser": average_loser(r),
        "Median trade": median_trade(r),
        "Largest winner": largest_winner(r),
        "Largest loser": largest_loser(r),
        "Skewness": skewness(r),
        "Excess kurtosis": excess_kurtosis(r),
        "Tail ratio": tail_ratio(r),
        "IQR": iqr(r),
        "MAD": mad(r),
    })
