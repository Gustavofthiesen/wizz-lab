"""Diagnostico do sinal, estabilidade temporal e concentracao (metricas 82-107).

Capitulos 08 e 09 do manual.

A diferenca entre este bloco e todos os anteriores: aqui nao se avalia a
estrategia pronta, e sim o *indicador* que a alimenta. Um sinal pode ter
informacao real e ainda assim gerar uma estrategia ruim (custos, execucao,
sizing) -- e uma estrategia pode parecer boa sem que o sinal tenha informacao
nenhuma. Separar as duas coisas evita consertar a peca errada.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _arr(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[~np.isnan(a)]


# --- 82 a 84 -----------------------------------------------------------------
def signal_precision(sinal, evento) -> float:
    """**Quando o indicador sinaliza, com que frequencia o evento acontece?**

    ``P(evento | sinal)``. Ambos booleanos.
    """
    s = np.asarray(sinal, bool)
    e = np.asarray(evento, bool)
    return float(e[s].mean()) if s.sum() else float("nan")


def signal_recall(sinal, evento) -> float:
    """**Que fracao dos eventos-alvo o sinal captura?** ``P(sinal | evento)``

    Precisao e recall se movem em direcoes opostas quando voce aperta o
    limiar. Reportar so um dos dois e o truque mais comum para fazer um
    indicador parecer bom.
    """
    s = np.asarray(sinal, bool)
    e = np.asarray(evento, bool)
    return float(s[e].mean()) if e.sum() else float("nan")


def signal_lift(sinal, evento) -> float:
    """**Quanto o sinal melhora a probabilidade em relacao a taxa-base?**

    ``P(evento | sinal) / P(evento)``. Lift 1,0 significa que o indicador nao
    acrescenta nada -- mesmo que sua precisao pareca alta.
    """
    base = float(np.asarray(evento, bool).mean())
    return signal_precision(sinal, evento) / base if base else float("nan")


# --- 85 e 86 -----------------------------------------------------------------
def conditional_forward_return(sinal, retorno_futuro) -> pd.Series:
    """**Qual retorno futuro medio ocorre depois do sinal?**

    Compara o retorno condicional ao sinal com o incondicional. A diferenca e
    o que o indicador de fato entrega.
    """
    s = np.asarray(sinal, bool)
    r = np.asarray(retorno_futuro, float)
    return pd.Series({
        "com_sinal": float(r[s].mean()) if s.sum() else float("nan"),
        "sem_sinal": float(r[~s].mean()) if (~s).sum() else float("nan"),
        "incondicional": float(r.mean()),
        "diferenca": float(r[s].mean() - r[~s].mean()) if s.sum() and (~s).sum() else float("nan"),
        "n_sinais": int(s.sum()),
    })


def signal_decay(score, retornos_por_horizonte: dict[int, np.ndarray]) -> pd.Series:
    """**Por quanto tempo a informacao do indicador permanece util?**

    Recebe ``{horizonte: retornos_futuros}`` e devolve o IC em cada horizonte.

    O horizonte de maior retorno condicional indica a meia-vida do sinal. Um
    pico isolado em um horizonte estranho merece suspeita, nao comemoracao.
    """
    return pd.Series({h: information_coefficient(score, r)
                      for h, r in sorted(retornos_por_horizonte.items())})


# --- 87 a 89 -----------------------------------------------------------------
def information_coefficient(score, retorno_futuro) -> float:
    """**O score se relaciona linearmente com o retorno futuro?**

    Correlacao de Pearson entre o sinal e o retorno a frente.

    Calibragem util: em equities, IC de 0,02-0,05 ja e um sinal de valor. Se
    alguem te mostra IC de 0,40, procure o vazamento de informacao antes de
    procurar a explicacao economica.
    """
    s, r = np.asarray(score, float), np.asarray(retorno_futuro, float)
    ok = ~(np.isnan(s) | np.isnan(r))
    if ok.sum() < 3:
        return float("nan")
    return float(np.corrcoef(s[ok], r[ok])[0, 1])


def rank_ic(score, retorno_futuro) -> float:
    """**A ordenacao do sinal corresponde a ordenacao dos retornos?** (Spearman)

    Mais robusto que o IC de Pearson a outliers -- e mais proximo do que uma
    estrategia de ranking realmente explora.
    """
    s = pd.Series(np.asarray(score, float)).rank()
    r = pd.Series(np.asarray(retorno_futuro, float)).rank()
    return information_coefficient(s, r)


def ic_information_ratio(ics) -> float:
    """**O IC medio e estavel ao longo do tempo?** ``ICIR = media(IC)/desvio(IC)``

    Recebe a serie de ICs periodo a periodo. Um IC medio bom com desvio enorme
    significa que o sinal funciona as vezes -- o que, sem saber quando, e
    quase o mesmo que nao funcionar.
    """
    a = _arr(ics)
    sd = a.std(ddof=1)
    if a.size < 2 or sd == 0:
        return float("nan")
    return float(a.mean() / sd)


# --- 90 a 92 -----------------------------------------------------------------
def quantile_analysis(score, retorno_futuro, n_quantis: int = 5) -> pd.DataFrame:
    """**Como a distribuicao de retornos muda ao longo dos quantis do indicador?**

    Devolve media, mediana, desvio e contagem por quantil.

    O teste visual mais informativo do capitulo: se a progressao entre quantis
    for coerente, ha estrutura; se so o quantil extremo se destaca, o sinal
    pode ser um artefato de poucas observacoes.
    """
    df = pd.DataFrame({"score": np.asarray(score, float),
                       "fwd": np.asarray(retorno_futuro, float)}).dropna()
    df["quantil"] = pd.qcut(df.score, n_quantis, labels=False, duplicates="drop") + 1
    return df.groupby("quantil").fwd.agg(
        media="mean", mediana="median", desvio="std", n="count")


def signal_monotonicity(score, retorno_futuro, n_quantis: int = 5) -> float:
    """**Quantis mais fortes produzem retornos progressivamente melhores?**

    Correlacao de Spearman entre o numero do quantil e o retorno medio dele.
    Perto de +1 e o padrao desejado.
    """
    q = quantile_analysis(score, retorno_futuro, n_quantis)
    if len(q) < 3:
        return float("nan")
    return float(pd.Series(q.index).corr(pd.Series(q.media.values), method="spearman"))


def signal_coverage(sinal) -> float:
    """**Com que frequencia o indicador produz uma oportunidade negociavel?**

    Um sinal excelente que dispara tres vezes por decada nao gera amostra nem
    para ser validado.
    """
    return float(np.asarray(sinal, bool).mean())


# --- 93 ----------------------------------------------------------------------
def incremental_signal_value(novo_score, scores_existentes,
                             retorno_futuro) -> pd.Series:
    """**O novo indicador adiciona informacao alem dos filtros que ja existem?**

    Regride o retorno futuro sobre os sinais existentes, pega o residuo e mede
    o IC do novo sinal contra ele.

    E a pergunta que quase ninguem faz. A maioria dos indicadores "novos" e uma
    combinacao linear dos antigos.
    """
    X = np.column_stack([np.ones(len(retorno_futuro))] +
                        [np.asarray(s, float) for s in scores_existentes])
    y = np.asarray(retorno_futuro, float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuo = y - X @ beta
    return pd.Series({
        "ic_bruto": information_coefficient(novo_score, y),
        "ic_incremental": information_coefficient(novo_score, residuo),
    })


# --- 94 a 96 -----------------------------------------------------------------
def regime_performance(retornos, regimes) -> pd.DataFrame:
    """**Em quais ambientes de mercado a estrategia ganha ou perde?**"""
    df = pd.DataFrame({"r": np.asarray(retornos, float),
                       "regime": np.asarray(regimes)})
    return df.groupby("regime").r.agg(
        media="mean", mediana="median", desvio="std", n="count",
        total=lambda s: float(s.sum()))


def regime_dependency_score(retornos, regimes) -> float:
    """**Quanto do P&L depende do melhor regime?**

    Fracao do lucro total que vem do regime mais favoravel. Perto de 1
    significa que voce nao tem uma estrategia -- tem uma aposta em um regime.
    """
    tabela = regime_performance(retornos, regimes)
    total = tabela.total.sum()
    if total == 0:
        return float("nan")
    return float(tabela.total.max() / total)


def periodos_positivos(retornos, regra: str = "ME") -> float:
    """**Quao distribuido no calendario esta o resultado?**

    Fracao de meses (ou trimestres/anos) positivos.
    """
    s = pd.Series(retornos).dropna()
    agregado = (1 + s).resample(regra).prod() - 1
    return float((agregado > 0).mean()) if len(agregado) else float("nan")


# --- 97 a 101 ----------------------------------------------------------------
def rolling_metric(retornos, janela: int = 252, metrica=np.mean) -> pd.Series:
    """Metrica em janela movel -- a base das metricas 97 a 100.

    O que se procura nao e um valor alto, e um valor que nao desaparece.
    """
    s = pd.Series(retornos).dropna()
    return s.rolling(janela).apply(lambda x: metrica(x.values), raw=False)


def rolling_stability(retornos, janela: int = 252, metrica=np.mean) -> pd.Series:
    """Resumo da estabilidade de uma metrica ao longo do tempo (metrica 100)."""
    roll = rolling_metric(retornos, janela, metrica).dropna()
    if roll.empty:
        return pd.Series(dtype=float)
    return pd.Series({
        "media": float(roll.mean()),
        "desvio": float(roll.std(ddof=1)),
        "fracao_positiva": float((roll > 0).mean()),
        "minimo": float(roll.min()),
        "maximo": float(roll.max()),
    })


def edge_decay(retornos) -> pd.Series:
    """**Existe tendencia sistematica de deterioracao do edge?**

    Regressao do retorno contra o tempo. Inclinacao negativa com t
    significativo e o sinal de que o mercado aprendeu.
    """
    s = pd.Series(retornos).dropna()
    n = len(s)
    if n < 10:
        return pd.Series(dtype=float)
    t = np.arange(n, dtype=float)
    X = np.column_stack([np.ones(n), t])
    beta, *_ = np.linalg.lstsq(X, s.values, rcond=None)
    residuo = s.values - X @ beta
    se = np.sqrt((residuo ** 2).sum() / (n - 2) /
                 ((t - t.mean()) ** 2).sum())
    return pd.Series({"inclinacao": float(beta[1]),
                      "t_inclinacao": float(beta[1] / se) if se else float("nan")})


# --- 103 a 107 ---------------------------------------------------------------
def pnl_concentration(r, topos=(0.01, 0.05, 0.10)) -> pd.Series:
    """**Quanto do lucro total vem dos melhores trades?**

    Uma curva que sobe rapido significa que poucos winners explicam quase
    tudo. Pode ser esperado em estrategias convexas -- mas precisa ser
    declarado e testado com :func:`remove_best_trades`.

    Nota de convencao: o denominador aqui e o **lucro bruto** (a soma apenas
    dos trades positivos), nao o lucro liquido. Usar o liquido faz a fracao
    ultrapassar 100% -- o top 10% pode somar varias vezes o resultado final,
    porque as perdas ainda nao foram descontadas. Isso e matematicamente certo
    e comunicativamente pessimo. Se voce quiser a leitura contra o liquido,
    ela esta em ``razao_top10_sobre_liquido``.
    """
    a = np.sort(_arr(r))[::-1]
    bruto = a[a > 0].sum()
    if bruto <= 0:
        return pd.Series(dtype=float)
    out = {}
    for t in topos:
        k = max(1, int(np.ceil(len(a) * t)))
        out[f"top {t:.0%} do lucro bruto"] = float(a[:k].sum() / bruto)
    liquido = a.sum()
    if liquido > 0:
        k = max(1, int(np.ceil(len(a) * 0.10)))
        out["razao_top10_sobre_liquido"] = float(a[:k].sum() / liquido)
    return pd.Series(out)


def remove_best_trades(r, n: int = 5) -> pd.Series:
    """**A estrategia continua viva sem os melhores resultados?**

    Se remover cinco trades de centenas zera o edge, a estrategia depende de
    eventos, nao de um processo.
    """
    a = _arr(r)
    sem = np.sort(a)[:-n] if n < len(a) else np.array([])
    return pd.Series({
        "expectancy_original": float(a.mean()),
        f"expectancy_sem_top_{n}": float(sem.mean()) if sem.size else float("nan"),
        "ainda_positiva": bool(sem.size and sem.mean() > 0),
    })


def remove_worst_trades(r, n: int = 5) -> pd.Series:
    """**As perdas vem de poucos eventos anomalos ou de um problema recorrente?**

    Se remover as piores transforma um sistema medíocre em um otimo, investigue
    execucao e gap risk -- nao comemore.
    """
    a = _arr(r)
    sem = np.sort(a)[n:] if n < len(a) else np.array([])
    return pd.Series({
        "expectancy_original": float(a.mean()),
        f"expectancy_sem_piores_{n}": float(sem.mean()) if sem.size else float("nan"),
    })


def hhi_contribuicao(r, grupos=None) -> float:
    """**Quao concentrado esta o P&L?** Indice de Herfindahl-Hirschman.

    Sem `grupos`, mede concentracao entre trades; com `grupos` (ativo, regime),
    mede entre categorias. Perto de 1 = tudo veio de um lugar so.
    """
    a = _arr(r)
    if grupos is not None:
        a = pd.Series(a).groupby(np.asarray(grupos)).sum().values
    positivos = a[a > 0]
    if not positivos.size:
        return float("nan")
    share = positivos / positivos.sum()
    return float((share ** 2).sum())


def breadth(r, grupos) -> float:
    """**Quantas oportunidades relativamente independentes alimentam o edge?**

    Numero efetivo de grupos, via inverso do HHI. Dez ativos dos quais um
    responde por 80% do lucro nao sao dez apostas -- sao pouco mais de uma.
    """
    h = hhi_contribuicao(r, grupos)
    return float(1 / h) if h and not np.isnan(h) else float("nan")
