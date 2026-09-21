"""Out-of-sample, walk-forward, overfitting e robustez (metricas 63-81).

Capitulos 06 e 07 do manual. Este e o bloco que mais reprova estrategias.

A ideia central: um backtest bom nao prova nada se as regras foram escolhidas
olhando para o mesmo historico. O que se mede aqui nao e performance -- e
quanto da performance sobrevive quando ela nao pode mais ser ajustada.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd


def _arr(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[~np.isnan(a)]


# --- 63 a 65 -----------------------------------------------------------------
def dividir_is_oos(r, fracao_is: float = 0.7) -> tuple[np.ndarray, np.ndarray]:
    """Divide a amostra em in-sample e out-of-sample, na ordem do tempo.

    Nunca divida aleatoriamente uma serie temporal: isso vaza o futuro para o
    treino.
    """
    a = _arr(r)
    corte = int(len(a) * fracao_is)
    return a[:corte], a[corte:]


def oos_is_ratio(r, fracao_is: float = 0.7, metrica=np.mean) -> float:
    """**Quanto do desempenho in-sample sobrevive fora da amostra?**

    Razao entre a metrica no OOS e no IS. Perto de 1 e excelente; perto de 0
    (ou negativo) indica que o IS estava capturando ruido.
    """
    is_, oos = dividir_is_oos(r, fracao_is)
    base = metrica(is_)
    return float(metrica(oos) / base) if base else float("nan")


def oos_degradation(r, fracao_is: float = 0.7, metrica=np.mean) -> float:
    """**Que percentual do desempenho foi perdido fora da amostra?**

    ``1 - OOS/IS``. Alguma degradacao e normal e esperada; degradacao total ou
    inversao de sinal nao e.
    """
    razao = oos_is_ratio(r, fracao_is, metrica)
    return float(1 - razao) if not np.isnan(razao) else float("nan")


# --- 66 e 67 -----------------------------------------------------------------
def walk_forward(r, n_janelas: int = 6, fracao_treino: float = 0.6,
                 metrica=np.mean) -> pd.DataFrame:
    """Walk-forward ancorado: treina, testa a frente, avanca, repete.

    Devolve uma linha por janela com a metrica no treino e no teste. E o teste
    que mais se parece com a vida real: voce sempre recalibra com o passado e
    opera o futuro.
    """
    a = _arr(r)
    n = len(a)
    if n < n_janelas * 10:
        raise ValueError("amostra curta demais para esse numero de janelas")
    tam = n // n_janelas
    linhas = []
    for k in range(1, n_janelas):
        fim_treino = int(tam * k * fracao_treino) + tam * (k - 1)
        fim_treino = max(fim_treino, tam * k - int(tam * (1 - fracao_treino)))
        treino, teste = a[:tam * k], a[tam * k:tam * (k + 1)]
        if not len(teste):
            continue
        linhas.append({"janela": k, "n_treino": len(treino), "n_teste": len(teste),
                       "metrica_treino": float(metrica(treino)),
                       "metrica_teste": float(metrica(teste))})
    return pd.DataFrame(linhas)


def walk_forward_efficiency(r, n_janelas: int = 6, metrica=np.mean) -> float:
    """**A estrategia mantem qualidade quando recalibrada sequencialmente?**

    WFE = media(metrica no teste) / media(metrica no treino).
    """
    wf = walk_forward(r, n_janelas, metrica=metrica)
    if wf.empty or wf.metrica_treino.mean() == 0:
        return float("nan")
    return float(wf.metrica_teste.mean() / wf.metrica_treino.mean())


def positive_oos_windows(r, n_janelas: int = 6, metrica=np.mean) -> float:
    """**Em quantas janelas walk-forward o edge permanece positivo?**

    Uma estrategia cujo resultado vem de uma unica janela excepcional nao e
    uma estrategia -- e um evento.
    """
    wf = walk_forward(r, n_janelas, metrica=metrica)
    return float((wf.metrica_teste > 0).mean()) if not wf.empty else float("nan")


# --- 68 e 69 -----------------------------------------------------------------
def pbo_cscv(matriz_desempenho, n_particoes: int = 10) -> float:
    """**Probability of Backtest Overfitting**, via CSCV.

    Bailey, Borwein, Lopez de Prado & Zhu (2017).

    Parameters
    ----------
    matriz_desempenho:
        Matriz ``(T, N)``: T periodos nas linhas, N configuracoes testadas nas
        colunas. Cada celula e o retorno daquela configuracao naquele periodo.
    n_particoes:
        Numero de blocos (par). O metodo forma todas as combinacoes de metade
        dos blocos como IS e a outra metade como OOS.

    Returns
    -------
    float
        Fracao das divisoes em que a configuracao campea no IS ficou abaixo da
        mediana no OOS. **Acima de 0,5 significa que escolher pelo backtest e
        pior que escolher no sorteio.**

    Esta e, na minha leitura, a metrica mais desconfortavel do manual inteiro:
    ela testa o *processo de selecao*, nao a estrategia.
    """
    M = np.asarray(matriz_desempenho, dtype=float)
    T, N = M.shape
    if n_particoes % 2:
        raise ValueError("n_particoes precisa ser par")
    if N < 2:
        return float("nan")

    blocos = np.array_split(np.arange(T), n_particoes)
    metade = n_particoes // 2
    logits = []
    for comb in combinations(range(n_particoes), metade):
        idx_is = np.concatenate([blocos[b] for b in comb])
        idx_oos = np.concatenate([blocos[b] for b in range(n_particoes)
                                  if b not in comb])
        perf_is = M[idx_is].mean(axis=0)
        perf_oos = M[idx_oos].mean(axis=0)
        campea = int(np.argmax(perf_is))
        # posto relativo da campea no OOS, em (0, 1)
        rank = float((perf_oos <= perf_oos[campea]).sum()) / (N + 1)
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))
    logits = np.asarray(logits)
    return float((logits <= 0).mean())


# --- 70 e 71 -----------------------------------------------------------------
def reality_check(matriz_desempenho, n_boot: int = 2000,
                  semente: int = 0) -> float:
    """**White's Reality Check:** a melhor regra supera o benchmark apos data snooping?

    Devolve o p-valor da hipotese nula de que *nenhuma* das N regras tem
    desempenho esperado positivo. Bootstrap estacionario sobre as colunas.

    Interpretacao: p alto significa que a melhor regra encontrada e compativel
    com o que se acharia testando N regras sem valor nenhum.
    """
    M = np.asarray(matriz_desempenho, dtype=float)
    T, N = M.shape
    medias = M.mean(axis=0)
    V = np.sqrt(T) * medias.max()

    rng = np.random.default_rng(semente)
    centrado = M - medias
    nulos = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, T, size=T)
        nulos[b] = np.sqrt(T) * centrado[idx].mean(axis=0).max()
    return float((nulos >= V).mean())


def hansen_spa(matriz_desempenho, n_boot: int = 2000, semente: int = 0) -> float:
    """**Hansen SPA:** versao com studentizacao e recentragem.

    Menos conservador que o Reality Check porque nao deixa regras muito ruins
    inflarem o valor critico. Devolve o p-valor.
    """
    M = np.asarray(matriz_desempenho, dtype=float)
    T, N = M.shape
    medias = M.mean(axis=0)
    desvios = M.std(axis=0, ddof=1)
    desvios[desvios == 0] = np.nan
    t_obs = np.sqrt(T) * medias / desvios
    V = np.nanmax(np.append(t_obs, 0.0))

    # recentragem de Hansen: so regras nao "muito ruins" entram no nulo
    limite = -np.sqrt(2 * np.log(np.log(max(T, 3)))) * desvios / np.sqrt(T)
    ajuste = np.where(medias >= limite, medias, 0.0)
    centrado = M - ajuste

    rng = np.random.default_rng(semente)
    nulos = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, T, size=T)
        m = centrado[idx].mean(axis=0)
        nulos[b] = np.nanmax(np.append(np.sqrt(T) * m / desvios, 0.0))
    return float((nulos >= V).mean())


# --- 72 ----------------------------------------------------------------------
def research_trials(registro: list[dict]) -> pd.Series:
    """**Quantas oportunidades reais houve de achar um bom backtest por acaso?**

    Nao ha formula: ha contabilidade. Passe a lista de tudo que foi testado --
    cada variacao de parametro, cada filtro ligado e desligado, cada universo.

    O numero que importa nao e o de testes que voce registrou: e o de decisoes
    que voce tomou olhando para o mesmo historico. Se essa lista estiver vazia
    ou curta demais para ser plausivel, o DSR nao tem como te proteger.
    """
    n = len(registro)
    familias = {}
    for item in registro:
        familias[item.get("familia", "nao_declarada")] = \
            familias.get(item.get("familia", "nao_declarada"), 0) + 1
    return pd.Series({"trials_declarados": n, **familias})


# --- 73 a 77 -----------------------------------------------------------------
def parameter_stability(resultado_por_param: pd.Series) -> pd.Series:
    """**Valores proximos do parametro escolhido tambem funcionam?**

    Recebe uma Series indexada pelo valor do parametro. Devolve o otimo, a
    media dos vizinhos imediatos e a razao entre as duas.

    Um otimo que e muito melhor que seus vizinhos e um pico -- provavelmente
    ruido. O que se quer e um plato.
    """
    s = pd.Series(resultado_por_param).sort_index()
    if len(s) < 3:
        return pd.Series(dtype=float)
    i = int(np.argmax(s.values))
    vizinhos = s.values[max(0, i - 1):i + 2]
    vizinhos = np.delete(vizinhos, min(i, 1))
    otimo = float(s.values[i])
    media_viz = float(np.mean(vizinhos))
    return pd.Series({
        "parametro_otimo": s.index[i],
        "resultado_otimo": otimo,
        "media_vizinhos": media_viz,
        "razao_vizinhos": media_viz / otimo if otimo else float("nan"),
    })


def parameter_plateau_width(resultado_por_param: pd.Series,
                            tolerancia: float = 0.9) -> float:
    """**Que parcela do espaco fica perto do desempenho otimo?**

    Fracao dos valores testados cujo resultado e pelo menos `tolerancia` vezes
    o melhor. Plato largo e evidencia estrutural; pico estreito e sorte.
    """
    s = pd.Series(resultado_por_param).astype(float)
    melhor = s.max()
    if melhor <= 0:
        return float("nan")
    return float((s >= melhor * tolerancia).mean())


def neighborhood_robustness(resultado_por_param: pd.Series) -> float:
    """Quanto o otimo excede a media geral do espaco de parametros.

    Margem suspeita = o ponto escolhido e muito melhor que tudo em volta.
    """
    s = pd.Series(resultado_por_param).astype(float)
    if s.mean() == 0:
        return float("nan")
    return float(s.max() / s.mean())


def parameter_drift(otimos_por_janela) -> pd.Series:
    """**O parametro otimo muda muito entre janelas?**

    Se cada periodo pede um parametro diferente, o parametro nao esta captando
    estrutura -- esta captando o periodo.
    """
    s = pd.Series(otimos_por_janela).astype(float)
    return pd.Series({
        "media": float(s.mean()),
        "desvio": float(s.std(ddof=1)) if len(s) > 1 else float("nan"),
        "coef_variacao": float(s.std(ddof=1) / s.mean()) if len(s) > 1 and s.mean() else float("nan"),
        "min": float(s.min()),
        "max": float(s.max()),
    })


# --- 78 a 81 -----------------------------------------------------------------
def lag_robustness(retornos_por_lag: dict[int, float]) -> pd.Series:
    """**O edge sobrevive se a entrada atrasar uma ou mais barras?**

    Recebe ``{lag: metrica}``. Uma estrategia que morre com um dia de atraso
    provavelmente esta capturando informacao que nao estaria disponivel a
    tempo na vida real.
    """
    s = pd.Series(retornos_por_lag).sort_index().astype(float)
    base = s.iloc[0]
    return pd.Series({
        "metrica_lag_0": float(base),
        "metrica_lag_1": float(s.iloc[1]) if len(s) > 1 else float("nan"),
        "retencao_lag_1": float(s.iloc[1] / base) if len(s) > 1 and base else float("nan"),
        "lags_positivos": float((s > 0).mean()),
    })


def price_perturbation(r, piora_por_trade: float, n_repeticoes: int = 200,
                       semente: int = 0) -> pd.Series:
    """**Pequenas pioras no preco de entrada/saida destroem o resultado?**

    Subtrai de cada trade uma piora aleatoria com media `piora_por_trade`.
    Devolve a distribuicao da expectancy resultante.
    """
    a = _arr(r)
    rng = np.random.default_rng(semente)
    medias = []
    for _ in range(n_repeticoes):
        piora = np.abs(rng.normal(piora_por_trade, piora_por_trade * 0.4, a.size))
        medias.append(float((a - piora).mean()))
    arr = np.array(medias)
    return pd.Series({"expectancy_original": float(a.mean()),
                      "expectancy_P50": float(np.quantile(arr, 0.50)),
                      "expectancy_P05": float(np.quantile(arr, 0.05)),
                      "fracao_ainda_positiva": float((arr > 0).mean())})


def robustness_pass_rate(resultados: dict[str, bool]) -> float:
    """**Quantos testes de perturbacao PREVIAMENTE DEFINIDOS a estrategia supera?**

    A palavra que faz o trabalho e "previamente". Escolher depois quais testes
    contam e a propria definicao de data snooping.
    """
    if not resultados:
        return float("nan")
    return float(sum(bool(v) for v in resultados.values()) / len(resultados))
