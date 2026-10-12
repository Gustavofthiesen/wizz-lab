"""Resultados publicados da carteira Wizz.

Carrega ``data/resultados_publicados.csv``: as estatísticas agregadas de
desempenho, janela a janela.

A linha entre resultado e estratégia
------------------------------------
Este módulo publica **resultado**. Nada aqui descreve como a carteira é
construída.

*Resultado* é o que qualquer gestor reporta: retorno, comparação com a
referência, volatilidade, drawdown, excesso ajustado por risco com erro-padrão,
beta, caixa médio e número de posições.

*Estratégia* é o método de avaliação das empresas, os filtros de elegibilidade,
a regra de dimensionamento e a de saída. **Nada disso entra neste repositório**,
nem nos posts, nem nos nomes das colunas.

A separação não é decorativa: é o que permite abrir o ferramental de métricas
para qualquer pessoa sem abrir o que produz os números.

A janela 2024–26 é marcada como reservada: não participou de nenhuma decisão de
construção. É a única cujo excesso pode ser lido sem desconto por seleção.
"""
from __future__ import annotations

import pathlib

import pandas as pd

#: Caminho do CSV publicado, relativo à raiz do repositório.
ARQUIVO = (pathlib.Path(__file__).resolve().parent.parent
           / "data" / "resultados_publicados.csv")

#: Período coberto pela série publicada.
PERIODO = "25/04/2017 a 11/09/2026"

#: O que a série não corrige. Declarado junto do número, sempre.
#:
#: Cada item descreve uma limitação da *medição*. Nenhum descreve o método que
#: produziu os retornos.
RESSALVAS = (
    "Resultado de simulação histórica sobre dados point-in-time, não de conta "
    "executada. O registro ao vivo começa em 2026.",
    "O universo histórico tem viés de sobrevivência residual: empresas que "
    "deixaram de existir estão sub-representadas.",
    "Diferenças de CAGR menores que ±2,4 pontos percentuais estão dentro do "
    "piso de ruído medido por intervenções-placebo, e não têm conteúdo.",
    "Parte relevante do excesso contra o índice amplo é exposição setorial, e "
    "não seleção. Contra a cesta do próprio setor, o excesso é menor.",
    "A configuração avaliada foi escolhida entre várias candidatas. A "
    "probabilidade de overfitting na escolha foi medida e é alta — por isso a "
    "janela reservada é a leitura que vale.",
)


def carregar() -> pd.DataFrame:
    """Devolve a tabela de resultados por janela, indexada pela janela."""
    return pd.read_csv(ARQUIVO).set_index("janela")


def janelas(incluir_cheia: bool = False) -> pd.DataFrame:
    """Só as janelas cronológicas, sem a linha de amostra cheia."""
    df = carregar()
    return df if incluir_cheia else df.drop(index="amostra-cheia")


def reservada() -> pd.Series:
    """A janela que não participou de nenhuma decisão de construção."""
    df = carregar()
    return df[df.reservada == 1].iloc[0]


def amostra_cheia() -> pd.Series:
    """A linha agregada do período inteiro."""
    return carregar().loc["amostra-cheia"]


def resumo() -> str:
    """Uma linha com o contraste que a série documenta."""
    r, c = reservada(), amostra_cheia()
    return (f"Amostra cheia: excesso {c.alpha:+.2%} (t = {c.t_alpha:.2f}). "
            f"Janela reservada: {r.alpha:+.2%} (t = {r.t_alpha:.2f}).")
