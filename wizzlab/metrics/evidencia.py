"""Evidencia estatistica, incerteza e bootstrap (metricas 43-62).

Capitulos 04 e 05 do manual. A pergunta deste bloco nao e "quanto rendeu?",
e sim "quanto do que eu medi pode ser sorte?".

O erro que este capitulo existe para evitar: tratar uma estimativa pontual
como se fosse um fato. Toda metrica do capitulo 01 e um numero calculado sobre
uma amostra finita, e portanto tem um intervalo em volta.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _arr(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[~np.isnan(a)]


# --- 43 ----------------------------------------------------------------------
def t_stat(r) -> float:
    """**O ganho medio e grande em relacao ao erro de estimacao?**

    ``t = media / (desvio / sqrt(N))``

    Regra de bolso: |t| acima de 2 e o minimo para conversar. Mas t alto obtido
    depois de testar muitas variantes nao significa nada -- e por isso que
    existe o Deflated Sharpe Ratio.
    """
    a = _arr(r)
    sd = a.std(ddof=1)
    if a.size < 2 or sd == 0:
        return float("nan")
    return float(a.mean() / (sd / np.sqrt(a.size)))


# --- 44 e 45 -----------------------------------------------------------------
def bootstrap_ci(r, estatistica=np.mean, nivel: float = 0.95,
                 n_boot: int = 10_000, semente: int = 0) -> tuple[float, float]:
    """**Qual faixa de valores do edge e compativel com os dados?**

    Intervalo percentil por reamostragem com reposicao.

    Prefira reportar o intervalo em vez do ponto. Um edge de +0,20R com
    intervalo [-0,05; +0,45] e uma coisa bem diferente de +0,20R com
    [+0,14; +0,26], mesmo tendo o mesmo centro.
    """
    a = _arr(r)
    if a.size < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_boot, a.size), replace=True)
    valores = estatistica(amostras, axis=1)
    alfa = (1 - nivel) / 2
    return (float(np.quantile(valores, alfa)),
            float(np.quantile(valores, 1 - alfa)))


def prob_expectancy_positiva(r, n_boot: int = 10_000, semente: int = 0) -> float:
    """**Que fracao das reamostragens sugere expectancy positiva?**

    Nao e a probabilidade de a estrategia dar certo -- e a probabilidade de que
    o sinal observado nao seja artefato desta amostra especifica.
    """
    a = _arr(r)
    if a.size < 2:
        return float("nan")
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_boot, a.size), replace=True)
    return float((amostras.mean(axis=1) > 0).mean())


def bootstrap_se(r, estatistica=np.mean, n_boot: int = 10_000,
                 semente: int = 0) -> float:
    """**Quao variavel e uma metrica sob reamostragem empirica?** (metrica 53)"""
    a = _arr(r)
    if a.size < 2:
        return float("nan")
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_boot, a.size), replace=True)
    return float(np.std(estatistica(amostras, axis=1), ddof=1))


# --- 46 ----------------------------------------------------------------------
def probabilistic_sharpe(sharpe_obs: float, n: int, skew: float = 0.0,
                         kurt: float = 3.0, sharpe_ref: float = 0.0) -> float:
    """**Probabilidade de o Sharpe verdadeiro exceder um benchmark.**

    Bailey & Lopez de Prado (2012). Corrige o erro-padrao do Sharpe por
    assimetria e curtose -- as duas coisas que a formula ingenua ignora e que
    justamente inflam o Sharpe de estrategias com cauda esquerda.

    `sharpe_obs` e `sharpe_ref` devem estar na MESMA frequencia de `n`
    (ou seja, se `n` conta dias, passe o Sharpe diario, nao o anualizado).
    """
    from math import erf, sqrt
    if n < 2:
        return float("nan")
    denom = 1 - skew * sharpe_obs + (kurt - 1) / 4 * sharpe_obs ** 2
    if denom <= 0:
        return float("nan")
    z = (sharpe_obs - sharpe_ref) * np.sqrt(n - 1) / np.sqrt(denom)
    return float(0.5 * (1 + erf(z / sqrt(2))))


# --- 47 ----------------------------------------------------------------------
def min_track_record_length(sharpe_obs: float, skew: float = 0.0,
                            kurt: float = 3.0, sharpe_ref: float = 0.0,
                            confianca: float = 0.95) -> float:
    """**Quanto historico seria preciso para sustentar este Sharpe?**

    Devolve o numero de observacoes (na frequencia de `sharpe_obs`).

    E o antidoto mais direto contra track records curtos: um Sharpe de 1,5 em
    seis meses pode exigir varios anos para ser estatisticamente distinguivel
    de zero.
    """
    from statistics import NormalDist
    if sharpe_obs <= sharpe_ref:
        return float("inf")
    z = NormalDist().inv_cdf(confianca)
    denom = 1 - skew * sharpe_obs + (kurt - 1) / 4 * sharpe_obs ** 2
    return float(1 + denom * (z / (sharpe_obs - sharpe_ref)) ** 2)


# --- 48 ----------------------------------------------------------------------
def deflated_sharpe(sharpe_obs: float, n: int, n_trials: int,
                    var_sharpes: float, skew: float = 0.0,
                    kurt: float = 3.0) -> float:
    """**O Sharpe ainda e excepcional depois de considerar quantos testes foram feitos?**

    Bailey & Lopez de Prado (2014). Constroi o Sharpe esperado do *melhor de
    N tentativas sob a hipotese nula* e pergunta se o observado o supera.

    `n_trials` e o numero real de configuracoes testadas -- inclusive as que
    voce nao registrou. `var_sharpes` e a variancia dos Sharpes obtidos entre
    as tentativas. Se voce nao consegue estimar os dois, isso ja e o
    diagnostico: a pesquisa nao foi rastreada.
    """
    from statistics import NormalDist
    if n_trials < 2 or var_sharpes <= 0:
        return float("nan")
    nd = NormalDist()
    gamma = 0.5772156649  # Euler-Mascheroni
    esperado_max = np.sqrt(var_sharpes) * (
        (1 - gamma) * nd.inv_cdf(1 - 1 / n_trials)
        + gamma * nd.inv_cdf(1 - 1 / (n_trials * np.e)))
    return probabilistic_sharpe(sharpe_obs, n, skew, kurt,
                                sharpe_ref=float(esperado_max))


# --- 49 e 50 -----------------------------------------------------------------
def autocorrelacao(r, lags: int = 10) -> pd.Series:
    """**Resultados consecutivos sao dependentes?**

    Autocorrelacao por lag. Importa porque quase toda formula de erro-padrao
    supoe independencia -- se houver autocorrelacao, os intervalos de confianca
    ingenuos ficam estreitos demais e voce se convence sem motivo.
    """
    s = pd.Series(_arr(r))
    return pd.Series({k: float(s.autocorr(lag=k)) for k in range(1, lags + 1)})


def effective_sample_size(r, lags: int = 10) -> float:
    """**Quantas observacoes independentes a amostra realmente contem?**

    ``N_eff = N / (1 + 2 * soma(rho_k))``

    Com autocorrelacao positiva, N_eff pode ser uma fracao de N. Trezentos
    trades muito correlacionados podem valer como cinquenta independentes.
    """
    a = _arr(r)
    if a.size < 3:
        return float("nan")
    rhos = autocorrelacao(a, min(lags, a.size - 2)).fillna(0.0)
    fator = 1 + 2 * float(rhos[rhos > 0].sum())
    return float(a.size / fator) if fator > 0 else float(a.size)


# --- 51 ----------------------------------------------------------------------
def ljung_box(r, lags: int = 10) -> tuple[float, float]:
    """**Existe evidencia CONJUNTA de autocorrelacao em varios lags?**

    Devolve (estatistica Q, p-valor). Testar lag a lag multiplica o risco de
    falso positivo; o Ljung-Box testa todos de uma vez.
    """
    from math import erfc
    a = _arr(r)
    n = a.size
    if n < lags + 2:
        return (float("nan"), float("nan"))
    rhos = autocorrelacao(a, lags).fillna(0.0).values
    q = n * (n + 2) * float(np.sum(rhos ** 2 / (n - np.arange(1, lags + 1))))
    try:  # p-valor exato quando scipy estiver disponivel
        from scipy.stats import chi2
        return (q, float(chi2.sf(q, lags)))
    except ImportError:
        # Aproximacao de Wilson-Hilferty para a qui-quadrado.
        z = ((q / lags) ** (1 / 3) - (1 - 2 / (9 * lags))) / np.sqrt(2 / (9 * lags))
        return (q, float(0.5 * erfc(z / np.sqrt(2))))


# --- 52 ----------------------------------------------------------------------
def newey_west_t(r, lags: int | None = None) -> float:
    """**A significancia muda quando corrigimos autocorrelacao e heterocedasticidade?**

    Estatistica t da media com erro-padrao HAC (Newey-West).

    Compare com :func:`t_stat`. Se o t despenca ao corrigir, o t ingenuo estava
    contando a mesma informacao varias vezes.
    """
    a = _arr(r)
    n = a.size
    if n < 3:
        return float("nan")
    if lags is None:
        lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    d = a - a.mean()
    gamma0 = float((d ** 2).mean())
    var = gamma0
    for k in range(1, min(lags, n - 1) + 1):
        peso = 1 - k / (lags + 1)
        gamma = float((d[k:] * d[:-k]).mean())
        var += 2 * peso * gamma
    if var <= 0:
        return float("nan")
    return float(a.mean() / np.sqrt(var / n))


# --- 54 a 56 -----------------------------------------------------------------
def iid_bootstrap(r, estatistica=np.mean, n_boot: int = 5000,
                  semente: int = 0) -> np.ndarray:
    """Reamostragem trade a trade, supondo independencia (metrica 54).

    E a versao mais simples -- e a errada quando ha dependencia temporal.
    """
    a = _arr(r)
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_boot, a.size), replace=True)
    return np.asarray(estatistica(amostras, axis=1), dtype=float)


def moving_block_bootstrap(r, tamanho_bloco: int = 20, estatistica=np.mean,
                           n_boot: int = 5000, semente: int = 0) -> np.ndarray:
    """Reamostragem por blocos, preservando dependencia local (metrica 55).

    Em vez de sortear observacoes soltas, sorteia trechos contiguos. Assim,
    clusters de perdas continuam existindo nas amostras simuladas -- o que
    alarga (corretamente) os intervalos.
    """
    a = _arr(r)
    n = a.size
    if n < tamanho_bloco * 2:
        return iid_bootstrap(a, estatistica, n_boot, semente)
    rng = np.random.default_rng(semente)
    n_blocos = int(np.ceil(n / tamanho_bloco))
    inicios = rng.integers(0, n - tamanho_bloco, size=(n_boot, n_blocos))
    idx = (inicios[:, :, None] + np.arange(tamanho_bloco)).reshape(n_boot, -1)[:, :n]
    return np.asarray(estatistica(a[idx], axis=1), dtype=float)


def stationary_bootstrap(r, tamanho_medio: int = 20, estatistica=np.mean,
                         n_boot: int = 5000, semente: int = 0) -> np.ndarray:
    """Politis-Romano: blocos de comprimento aleatorio (metrica 56).

    Evita o artefato de escolher um comprimento fixo de bloco. A cada passo, a
    serie continua com probabilidade ``1 - 1/tamanho_medio`` ou salta para uma
    posicao nova.
    """
    a = _arr(r)
    n = a.size
    if n < 4:
        return iid_bootstrap(a, estatistica, n_boot, semente)
    rng = np.random.default_rng(semente)
    p = 1.0 / tamanho_medio
    idx = np.empty((n_boot, n), dtype=int)
    idx[:, 0] = rng.integers(0, n, size=n_boot)
    saltar = rng.random((n_boot, n)) < p
    novos = rng.integers(0, n, size=(n_boot, n))
    for t in range(1, n):
        continuar = (idx[:, t - 1] + 1) % n
        idx[:, t] = np.where(saltar[:, t], novos[:, t], continuar)
    return np.asarray(estatistica(a[idx], axis=1), dtype=float)


# --- 57 a 59 -----------------------------------------------------------------
def monte_carlo_equity(r, fracao_por_trade: float = 0.01, n_sim: int = 500,
                       semente: int = 0) -> np.ndarray:
    """Conjunto de curvas de capital plausiveis (metrica 57).

    Devolve matriz ``(n_sim, N)``. A linha mediana **nao e uma previsao**: e
    apenas o centro de uma distribuicao de trajetorias.
    """
    a = _arr(r)
    rng = np.random.default_rng(semente)
    amostras = rng.choice(a, size=(n_sim, a.size), replace=True)
    return np.cumprod(1 + amostras * fracao_por_trade, axis=1)


def monte_carlo_terminal(r, fracao_por_trade: float = 0.01, n_sim: int = 5000,
                         semente: int = 0) -> pd.Series:
    """Distribuicao do capital final apos o horizonte (metrica 59)."""
    caminhos = monte_carlo_equity(r, fracao_por_trade, n_sim, semente)
    finais = caminhos[:, -1]
    return pd.Series({q: float(np.quantile(finais, q / 100))
                      for q in (1, 5, 25, 50, 75, 95, 99)})


# --- resumo ------------------------------------------------------------------
def resumo(r, n_boot: int = 5000) -> pd.Series:
    """Bloco de evidencia estatistica em uma Series."""
    lo, hi = bootstrap_ci(r, n_boot=n_boot)
    q, p = ljung_box(r)
    return pd.Series({
        "t-stat": t_stat(r),
        "t-stat (Newey-West)": newey_west_t(r),
        "IC 95% inferior": lo,
        "IC 95% superior": hi,
        "P(E > 0)": prob_expectancy_positiva(r, n_boot=n_boot),
        "N": int(_arr(r).size),
        "N efetivo": effective_sample_size(r),
        "Ljung-Box Q": q,
        "Ljung-Box p": p,
        "Autocorr lag 1": float(autocorrelacao(r, 1).iloc[0]),
    })
