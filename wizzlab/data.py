"""Geradores de dados didaticos.

Nenhum dado real de carteira entra neste repositorio. Tudo aqui e simulado e
reprodutivel por semente, exatamente como o Apendice B do manual de validacao
recomenda: *"figura com dados simulados para fins didaticos"*.

O ponto de usar dados sinteticos e pedagogico, nao evasivo: quando voce mesmo
escolhe o processo gerador, sabe qual e a resposta certa e pode conferir se a
metrica de fato a encontra.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Estrategia:
    """Um conjunto de trades simulados mais a curva de capital resultante.

    Attributes
    ----------
    trades:
        DataFrame com uma linha por operacao. Colunas: ``data_entrada``,
        ``data_saida``, ``retorno`` (fracao do capital arriscado), ``r_multiple``,
        ``mae``, ``mfe``, ``ativo``, ``regime``.
    diario:
        Serie de retornos diarios da carteira.
    nome:
        Rotulo usado nos graficos.
    """

    trades: pd.DataFrame
    diario: pd.Series
    nome: str = "Estratégia"
    meta: dict = field(default_factory=dict)

    @property
    def capital(self) -> pd.Series:
        """Curva de capital com base 1,0."""
        return (1 + self.diario).cumprod()

    def __repr__(self) -> str:  # pragma: no cover - conveniencia de notebook
        return (f"<Estrategia {self.nome!r}: {len(self.trades)} trades, "
                f"{len(self.diario)} pregoes>")


def gerar_estrategia(
    n_trades: int = 420,
    win_rate: float = 0.42,
    payoff: float = 1.9,
    custo_por_trade: float = 0.0008,
    vol_diaria: float = 0.009,
    drift_anual: float = 0.11,
    inicio: str = "2012-01-02",
    semente: int = 42,
    nome: str = "Estratégia",
) -> Estrategia:
    """Simula uma estrategia com edge conhecido.

    Os parametros sao o "gabarito": voce sabe de antemao qual win rate e qual
    payoff colocou, e pode conferir se as metricas os recuperam dentro do erro
    amostral. Um `win_rate` de 42% com `payoff` 1,9 produz expectancy positiva
    -- e um bom caso para mostrar que acerto e qualidade sao coisas diferentes.

    O default carrega de proposito a licao mais importante do manual. Com
    ``win_rate=0.42`` e ``payoff=1.9``, a expectancy *verdadeira* do processo e
    de cerca de +0,22R -- um edge real e economicamente relevante. Ainda assim,
    em 420 trades a estatistica t fica proxima de 1, ou seja, **indistinguivel
    de zero**. Nao e defeito do gerador: e o tamanho de amostra que a maioria
    dos backtests tem.

    Aumente ``n_trades`` para 3000 e veja o mesmo processo virar significativo.
    Esse par de execucoes ensina mais sobre validacao que qualquer ratio.

    Parameters
    ----------
    custo_por_trade:
        Fricao total por round trip, em fracao do capital arriscado. O manual
        insiste que todo edge seja medido liquido.
    """
    rng = np.random.default_rng(semente)

    ganhou = rng.random(n_trades) < win_rate
    # Winners com cauda direita (lognormal) e losers mais concentrados:
    # e a assimetria tipica de um sistema que corta perdas e deixa ganhos correr.
    ganhos = rng.lognormal(mean=np.log(payoff) - 0.18, sigma=0.60, size=n_trades)
    perdas = -np.abs(rng.normal(loc=1.0, scale=0.28, size=n_trades))
    r = np.where(ganhou, ganhos, perdas) - custo_por_trade / 0.01

    pregoes = pd.bdate_range(inicio, periods=int(n_trades * 6.5))
    entradas = np.sort(rng.choice(len(pregoes) - 12, size=n_trades, replace=True))
    duracao = np.where(ganhou,
                       rng.integers(4, 30, n_trades),
                       rng.integers(2, 12, n_trades))
    saidas = np.minimum(entradas + duracao, len(pregoes) - 1)

    regimes = np.array(["alta", "lateral", "queda"])
    # O regime nao e sorteado de forma independente: ele vem em blocos, para
    # que a estrategia tenha dependencia temporal de verdade.
    blocos = rng.integers(0, 3, size=max(1, n_trades // 25) + 1)
    regime_trade = np.repeat(blocos, 25)[:n_trades]

    trades = pd.DataFrame({
        "data_entrada": pregoes[entradas],
        "data_saida": pregoes[saidas],
        "r_multiple": r,
        "retorno": r * 0.01,          # 1% do capital arriscado por trade
        "ativo": rng.choice([f"ATIVO{i}" for i in range(1, 13)], n_trades),
        "regime": regimes[regime_trade],
    })
    # MAE/MFE coerentes com o resultado: todo trade anda contra antes de andar
    # a favor, e o vencedor quase nunca sai no topo.
    trades["mae"] = -np.abs(rng.normal(0.45, 0.25, n_trades))
    trades["mfe"] = np.where(trades.r_multiple > 0,
                             trades.r_multiple * rng.uniform(1.05, 1.9, n_trades),
                             np.abs(rng.normal(0.35, 0.22, n_trades)))
    trades = trades.sort_values("data_entrada").reset_index(drop=True)

    # A serie diaria carrega o P&L dos trades mais um ruido de mercado.
    diario = pd.Series(rng.normal(drift_anual / 252, vol_diaria, len(pregoes)),
                       index=pregoes, name="retorno")
    for saida, ret in zip(saidas, trades.retorno.values):
        diario.iloc[saida] += ret

    return Estrategia(trades=trades, diario=diario, nome=nome,
                      meta={"win_rate_verdadeiro": win_rate,
                            "payoff_verdadeiro": payoff,
                            "custo_por_trade": custo_por_trade,
                            "semente": semente})


def gerar_benchmark(estrategia: Estrategia, beta: float = 0.55,
                    vol_diaria: float = 0.011, drift_anual: float = 0.09,
                    semente: int = 7) -> pd.Series:
    """Gera um indice de referencia correlacionado com a estrategia.

    O manual de marca exige comparar sempre no mesmo periodo e com referencia
    adequada. Sem benchmark, retorno bruto nao diz nada.
    """
    rng = np.random.default_rng(semente)
    idx = estrategia.diario.index
    ruido = rng.normal(drift_anual / 252, vol_diaria, len(idx))
    serie = beta * estrategia.diario.values + (1 - beta) * ruido
    return pd.Series(serie, index=idx, name="benchmark")


def gerar_sinal(n: int = 3000, ic_verdadeiro: float = 0.045,
                semente: int = 11) -> pd.DataFrame:
    """Gera pares (score do indicador, retorno futuro) com IC conhecido.

    Serve ao capitulo de diagnostico do sinal: como `ic_verdadeiro` e dado,
    da para mostrar quanta amostra e necessaria para enxerga-lo.
    """
    rng = np.random.default_rng(semente)
    score = rng.normal(0, 1, n)
    ruido = rng.normal(0, 1, n)
    rho = ic_verdadeiro
    fwd = rho * score + np.sqrt(max(0.0, 1 - rho ** 2)) * ruido
    return pd.DataFrame({"score": score, "retorno_futuro": fwd * 0.02})
