"""Qualidade do retorno, drawdown, caudas e sobrevivencia (metricas 15-42).

Capitulos 02 e 03 do manual. Aqui a pergunta muda: nao e mais "existe lucro?",
e sim "quanto risco foi preciso correr para obte-lo, e a estrategia sobrevive
ao pior caminho plausivel?".

Convencao deste modulo: `retornos` e uma serie de retornos periodicos (diarios,
por padrao) ja liquidos de custos. `periodos` e quantos periodos formam um ano.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DIAS_UTEIS_ANO = 252


def _s(x) -> pd.Series:
    s = pd.Series(x).astype(float)
    return s.dropna()


# --- blocos de base ----------------------------------------------------------
def curva_capital(retornos, base: float = 1.0) -> pd.Series:
    """Capital acumulado a partir dos retornos periodicos."""
    return base * (1 + _s(retornos)).cumprod()


def cagr(retornos, periodos: int = DIAS_UTEIS_ANO) -> float:
    """Taxa de crescimento anual composta.

    Nao confunda com media dos retornos anuais: o CAGR e geometrico, e e ele
    que corresponde ao que o capital efetivamente fez.
    """
    s = _s(retornos)
    if s.empty:
        return float("nan")
    total = float((1 + s).prod())
    anos = len(s) / periodos
    if anos <= 0 or total <= 0:
        return float("nan")
    return float(total ** (1 / anos) - 1)


def volatilidade(retornos, periodos: int = DIAS_UTEIS_ANO) -> float:
    """Desvio-padrao anualizado dos retornos."""
    return float(_s(retornos).std(ddof=1) * np.sqrt(periodos))


def downside_deviation(retornos, alvo: float = 0.0,
                       periodos: int = DIAS_UTEIS_ANO) -> float:
    """Dispersao apenas do que ficou abaixo do alvo.

    E o denominador do Sortino: pune queda, nao oscilacao para cima.
    """
    s = _s(retornos)
    abaixo = np.minimum(s - alvo, 0.0)
    return float(np.sqrt((abaixo ** 2).mean()) * np.sqrt(periodos))


# --- 15 ----------------------------------------------------------------------
def sharpe(retornos, rf: float = 0.0, periodos: int = DIAS_UTEIS_ANO) -> float:
    """**Quanto retorno excedente por unidade de volatilidade total?**

    ``S = (mu - rf) / sigma``, anualizado.

    O ratio mais citado e o mais mal usado. Ele assume que volatilidade e uma
    boa medida de risco -- o que deixa de valer quando a distribuicao tem
    cauda esquerda pesada. Sharpe alto com skew muito negativo e um alerta,
    nao um elogio.

    Sharpe tambem nao e comparavel entre frequencias sem cuidado: anualizar por
    ``sqrt(252)`` supoe independencia serial, que e justamente o que
    :func:`~wizzlab.metrics.evidencia.autocorrelacao` vai testar.
    """
    s = _s(retornos)
    excesso = s - rf / periodos
    sd = excesso.std(ddof=1)
    if sd == 0:
        return float("nan")
    return float(excesso.mean() / sd * np.sqrt(periodos))


# --- 16 ----------------------------------------------------------------------
def sortino(retornos, alvo: float = 0.0, periodos: int = DIAS_UTEIS_ANO) -> float:
    """**Quanto retorno por unidade de desvio de queda?**

    Substitui o desvio total pelo downside deviation. Util quando a estrategia
    e deliberadamente assimetrica e a volatilidade para cima nao e problema.
    """
    s = _s(retornos)
    dd = downside_deviation(s, alvo, periodos)
    if dd == 0:
        return float("nan")
    return float((s.mean() * periodos - alvo) / dd)


# --- 17 ----------------------------------------------------------------------
def omega(retornos, limiar: float = 0.0) -> float:
    """**O ganho esperado acima de um limiar supera a perda abaixo dele?**

    Razao entre as areas da distribuicao acima e abaixo do limiar. Usa a
    distribuicao inteira, nao so os dois primeiros momentos.
    """
    s = _s(retornos) - limiar
    acima, abaixo = s[s > 0].sum(), abs(s[s < 0].sum())
    if abaixo == 0:
        return float("inf") if acima > 0 else float("nan")
    return float(acima / abaixo)


# --- 18 ----------------------------------------------------------------------
def gain_to_pain(retornos) -> float:
    """**Quanto ganho total para cada unidade de retorno negativo?**

    Soma dos retornos dividida pela soma dos modulos dos negativos.
    """
    s = _s(retornos)
    dor = abs(s[s < 0].sum())
    if dor == 0:
        return float("inf") if s.sum() > 0 else float("nan")
    return float(s.sum() / dor)


# --- 28 e derivados ----------------------------------------------------------
def serie_drawdown(retornos) -> pd.Series:
    """Drawdown periodo a periodo, em fracao do pico anterior (valores <= 0)."""
    cap = curva_capital(retornos)
    return cap / cap.cummax() - 1


def max_drawdown(retornos) -> float:
    """**Qual a maior perda percentual entre um pico e o fundo seguinte?**

    O numero que mais determina se alguem consegue de fato seguir a estrategia.
    Cuidado: o MDD observado e apenas *uma amostra* do MDD possivel -- use
    :func:`monte_carlo_mdd` para saber quao sortudo foi o histórico.
    """
    dd = serie_drawdown(retornos)
    return float(dd.min()) if len(dd) else float("nan")


def average_drawdown(retornos) -> float:
    """Profundidade media dos episodios de drawdown."""
    dd = serie_drawdown(retornos)
    negativos = dd[dd < 0]
    return float(negativos.mean()) if len(negativos) else 0.0


def median_drawdown(retornos) -> float:
    """Profundidade do episodio mediano -- resiste ao episodio unico e enorme."""
    dd = serie_drawdown(retornos)
    negativos = dd[dd < 0]
    return float(negativos.median()) if len(negativos) else 0.0


def time_under_water(retornos) -> float:
    """**Que fracao do tempo a equity fica abaixo do high-water mark?**

    Costuma ser mais dificil de aguentar que a profundidade. Uma queda de 15%
    que dura tres anos machuca mais que uma de 25% que dura dois meses.
    """
    dd = serie_drawdown(retornos)
    return float((dd < 0).mean()) if len(dd) else float("nan")


def episodios_drawdown(retornos) -> pd.DataFrame:
    """Tabela de episodios: inicio, fundo, recuperacao, profundidade, duracao.

    Alimenta as metricas 31 (Drawdown Duration) e 33 (Recovery Time).
    """
    dd = serie_drawdown(retornos)
    episodios, dentro = [], False
    ini = fundo_idx = None
    for data, valor in dd.items():
        if not dentro and valor < 0:
            dentro, ini, fundo_idx = True, data, data
        elif dentro:
            if valor < dd.loc[fundo_idx]:
                fundo_idx = data
            if valor >= 0:
                episodios.append((ini, fundo_idx, data, float(dd.loc[fundo_idx])))
                dentro = False
    if dentro:  # episodio ainda aberto no fim da amostra
        episodios.append((ini, fundo_idx, None, float(dd.loc[fundo_idx])))

    df = pd.DataFrame(episodios, columns=["inicio", "fundo", "recuperacao",
                                          "profundidade"])
    if df.empty:
        return df
    df["duracao"] = [(rec - ini).days if rec is not None else np.nan
                     for ini, rec in zip(df.inicio, df.recuperacao)]
    df["tempo_recuperacao"] = [(rec - f).days if rec is not None else np.nan
                               for f, rec in zip(df.fundo, df.recuperacao)]
    return df.sort_values("profundidade").reset_index(drop=True)


# --- 19 a 25 -----------------------------------------------------------------
def calmar(retornos, periodos: int = DIAS_UTEIS_ANO) -> float:
    """**Quanto CAGR por unidade de drawdown maximo?**

    Intuitivo e muito sensivel a um unico evento: o denominador e um extremo
    observado, nao uma media. Leia junto do Monte Carlo do MDD.
    """
    mdd = abs(max_drawdown(retornos))
    return float(cagr(retornos, periodos) / mdd) if mdd else float("nan")


#: MAR e, na convencao mais comum, o Calmar calculado sobre o historico inteiro.
mar = calmar


def sterling(retornos, margem: float = 0.10,
             periodos: int = DIAS_UTEIS_ANO) -> float:
    """Calmar com uma margem de seguranca somada ao drawdown.

    Convencao varia entre autores e plataformas -- declare a sua no relatorio,
    como o manual pede.
    """
    mdd = abs(max_drawdown(retornos)) + margem
    return float(cagr(retornos, periodos) / mdd) if mdd else float("nan")


def burke(retornos, periodos: int = DIAS_UTEIS_ANO) -> float:
    """**Quanto retorno em relacao ao conjunto de drawdowns, nao so ao pior?**

    Usa a raiz da soma dos quadrados das profundidades, o que dilui o peso de
    um unico episodio excepcional.
    """
    eps = episodios_drawdown(retornos)
    if eps.empty:
        return float("nan")
    raiz = np.sqrt((eps.profundidade ** 2).sum())
    return float(cagr(retornos, periodos) / raiz) if raiz else float("nan")


def recovery_factor(retornos) -> float:
    """Lucro liquido total dividido pelo pior drawdown."""
    s = _s(retornos)
    lucro = float((1 + s).prod() - 1)
    mdd = abs(max_drawdown(s))
    return float(lucro / mdd) if mdd else float("nan")


def ulcer_index(retornos) -> float:
    """**Quao profundos E quao persistentes sao os drawdowns?**

    Raiz da media dos quadrados do drawdown. Diferente do MDD, penaliza ficar
    muito tempo embaixo d'agua, nao so afundar muito uma vez.
    """
    dd = serie_drawdown(retornos)
    return float(np.sqrt((dd ** 2).mean())) if len(dd) else float("nan")


def martin(retornos, rf: float = 0.0, periodos: int = DIAS_UTEIS_ANO) -> float:
    """Retorno excedente por unidade de Ulcer Index (Ulcer Performance Index)."""
    ui = ulcer_index(retornos)
    return float((cagr(retornos, periodos) - rf) / ui) if ui else float("nan")


# --- 26 e 27 -----------------------------------------------------------------
def return_on_exposure(retornos, exposicao) -> float:
    """**Quanto retorno por unidade de tempo efetivamente exposto?**

    `exposicao` e a fracao do periodo em que havia posicao aberta. Uma
    estrategia que fica 20% do tempo no mercado e rende metade de outra que
    fica 100% pode ser muito melhor por unidade de risco assumido.
    """
    s = _s(retornos)
    exp_media = float(pd.Series(exposicao).astype(float).mean())
    total = float((1 + s).prod() - 1)
    return float(total / exp_media) if exp_media else float("nan")


def sqn(r) -> float:
    """**System Quality Number:** expectancy e grande frente a dispersao e ao N?

    ``SQN = sqrt(N) * media(R) / desvio(R)``

    Conceito de Van Tharp. E, na pratica, uma estatistica t dos R-multiples --
    o que deixa explicito que SQN alto tanto pode vir de edge quanto de
    amostra grande.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    sd = a.std(ddof=1)
    if a.size < 2 or sd == 0:
        return float("nan")
    return float(np.sqrt(a.size) * a.mean() / sd)


# --- 34 a 39 -----------------------------------------------------------------
def var_historico(retornos, nivel: float = 0.05) -> float:
    """**Qual perda-limite e excedida apenas em `nivel` dos periodos?**

    Quantil empirico. Nao diz nada sobre o que acontece *dentro* da cauda --
    para isso existe o :func:`expected_shortfall`.
    """
    s = _s(retornos)
    return float(np.quantile(s, nivel)) if len(s) else float("nan")


def expected_shortfall(retornos, nivel: float = 0.05) -> float:
    """**Quando entramos na cauda ruim, qual e a perda media?** (CVaR)

    Responde o que o VaR omite. Para sizing e risco de ruina, e a medida mais
    honesta das duas.
    """
    s = _s(retornos)
    if not len(s):
        return float("nan")
    corte = np.quantile(s, nivel)
    cauda = s[s <= corte]
    return float(cauda.mean()) if len(cauda) else float("nan")


def piores_periodos(retornos, regras=("D", "W", "ME", "YE")) -> pd.Series:
    """Pior retorno em cada horizonte de agregacao."""
    s = _s(retornos)
    out = {}
    for regra in regras:
        agregado = (1 + s).resample(regra).prod() - 1
        out[regra] = float(agregado.min()) if len(agregado) else float("nan")
    return pd.Series(out)


def kelly_fraction(r) -> float:
    """**Que fracao do capital maximiza crescimento logaritmico?**

    ``f* = (p*b - q) / b`` na versao de dois resultados.

    Kelly e um teto teorico, nao uma recomendacao: ele supoe que a distribuicao
    estimada esta certa. Como ela nunca esta, a pratica usual e fracao de
    Kelly (metade ou menos). Kelly cheio sobre parametros estimados costuma
    produzir drawdowns intoleraveis.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    w, l = a[a > 0], a[a < 0]
    if not w.size or not l.size:
        return float("nan")
    p = w.size / a.size
    b = w.mean() / abs(l.mean())
    return float((p * b - (1 - p)) / b) if b else float("nan")


def risk_of_ruin(r, fracao_por_trade: float = 0.01, ruina: float = 0.5,
                 n_trades: int = 500, n_sim: int = 5000,
                 semente: int = 0) -> float:
    """**Qual a probabilidade de chegar a um nivel de capital inviavel?**

    Simulacao direta: reamostra os R-multiples observados, aplica o sizing e
    conta em que fracao dos caminhos o capital cai abaixo de `ruina`.

    Depende inteiramente do sizing. Uma estrategia com edge positivo e ruina
    quase certa se a fracao por trade for grande demais.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    if not a.size:
        return float("nan")
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_sim, n_trades), replace=True)
    caminhos = np.cumprod(1 + amostras * fracao_por_trade, axis=1)
    return float((caminhos.min(axis=1) <= ruina).mean())


# --- 40 a 42 -----------------------------------------------------------------
def max_streak(r, vencedora: bool = False) -> int:
    """Maior sequencia consecutiva de perdas (padrao) ou de ganhos.

    Streaks nao sao Bernoulli independentes quando ha regimes -- compare o
    observado com :func:`monte_carlo_streak`, que supoe independencia. Se o
    real for muito maior, ha dependencia temporal.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    alvo = a > 0 if vencedora else a < 0
    melhor = atual = 0
    for v in alvo:
        atual = atual + 1 if v else 0
        melhor = max(melhor, atual)
    return int(melhor)


# --- Monte Carlo (metricas 57-61) --------------------------------------------
def monte_carlo_mdd(r, fracao_por_trade: float = 0.01, n_trades: int | None = None,
                    n_sim: int = 5000, semente: int = 0) -> pd.Series:
    """**Qual drawdown maximo e tipico, e qual e plausivel na cauda?**

    Devolve P50/P95/P99 do MDD sob reamostragem iid dos trades.

    E a pergunta que separa um backtest sortudo de um backtest robusto: se o
    MDD observado foi 18% mas o P95 simulado e 34%, voce precisa aguentar 34%.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    if not a.size:
        return pd.Series(dtype=float)
    n = n_trades or a.size
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_sim, n), replace=True)
    caminhos = np.cumprod(1 + amostras * fracao_por_trade, axis=1)
    picos = np.maximum.accumulate(caminhos, axis=1)
    mdds = (caminhos / picos - 1).min(axis=1)
    return pd.Series({"P50": float(np.quantile(mdds, 0.50)),
                      "P95": float(np.quantile(mdds, 0.05)),
                      "P99": float(np.quantile(mdds, 0.01))})


def monte_carlo_streak(r, n_sim: int = 5000, semente: int = 0) -> pd.Series:
    """Distribuicao da maior sequencia de perdas sob independencia."""
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    rng = np.random.default_rng(semente)
    out = []
    for _ in range(n_sim):
        out.append(max_streak(rng.choice(a, size=a.size, replace=True)))
    arr = np.array(out)
    return pd.Series({"observado": max_streak(a),
                      "P50": float(np.quantile(arr, 0.50)),
                      "P95": float(np.quantile(arr, 0.95)),
                      "P99": float(np.quantile(arr, 0.99))})


def monte_carlo_prob_perda(r, fracao_por_trade: float = 0.01,
                           n_trades: int | None = None, n_sim: int = 5000,
                           semente: int = 0) -> float:
    """Chance de terminar abaixo do capital inicial no horizonte simulado."""
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    n = n_trades or a.size
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_sim, n), replace=True)
    finais = np.prod(1 + amostras * fracao_por_trade, axis=1)
    return float((finais < 1.0).mean())


# --- resumo ------------------------------------------------------------------
def resumo(retornos, periodos: int = DIAS_UTEIS_ANO) -> pd.Series:
    """Qualidade do retorno e sobrevivencia em uma Series."""
    return pd.Series({
        "CAGR": cagr(retornos, periodos),
        "Volatilidade": volatilidade(retornos, periodos),
        "Sharpe": sharpe(retornos, periodos=periodos),
        "Sortino": sortino(retornos, periodos=periodos),
        "Omega": omega(retornos),
        "Gain-to-pain": gain_to_pain(retornos),
        "Max drawdown": max_drawdown(retornos),
        "Avg drawdown": average_drawdown(retornos),
        "Time under water": time_under_water(retornos),
        "Calmar": calmar(retornos, periodos),
        "Burke": burke(retornos, periodos),
        "Recovery factor": recovery_factor(retornos),
        "Ulcer index": ulcer_index(retornos),
        "Martin (UPI)": martin(retornos, periodos=periodos),
        "VaR 5%": var_historico(retornos),
        "Expected shortfall 5%": expected_shortfall(retornos),
    })
