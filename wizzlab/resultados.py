"""Resultados publicados da carteira Wizz.

Este módulo carrega ``data/resultados_publicados.csv``: as estatísticas
agregadas de desempenho que foram **escolhidas para publicação**, janela a
janela.

O que está aqui e o que não está
--------------------------------
Estão aqui: CAGR, CDI do período, excesso, alpha com erro-padrão e intervalo,
beta, volatilidade, Sharpe, pior queda, caixa médio e número de posições.

Não estão aqui, e não entram neste repositório: as regras da estratégia, os
parâmetros do modelo de valuation, o universo elegível e as posições. A
separação é deliberada — o que sustenta a discussão de método é o resultado
medido, não o motor que o produziu.

A janela 2024–26 é marcada como reservada: ela não participou de nenhuma
escolha de regra ou parâmetro. É a única cujo alpha pode ser lido sem desconto
por seleção.
"""
from __future__ import annotations

import pathlib

import pandas as pd

#: Caminho do CSV publicado, relativo à raiz do repositório.
ARQUIVO = pathlib.Path(__file__).resolve().parent.parent / "data" / "resultados_publicados.csv"

#: Período coberto pela série publicada.
PERIODO = "25/04/2017 a 11/09/2026"

#: Configuração a que os números se referem.
CONFIGURACAO = (
    "V3 — grid por valor justo, permanência até margem de segurança de saída "
    "de 5%, alíquota de IR zero (isenção mensal de R$ 20.000 aplicável ao porte)"
)

#: O que a série NÃO corrige. Declarado junto do número, sempre.
RESSALVAS = (
    "Universo com viés de sobrevivência residual: das 30 empresas recuperadas "
    "no teste, 2 passariam o portão de entrada.",
    "Piso de ruído de recomposição de ±0,5 p.p. de CAGR e piso do cache de "
    "valuation de ±2,4 p.p. — diferenças menores que isso não têm conteúdo.",
    "58% do excesso do baseline é inclinação setorial, e não seleção dentro "
    "do setor.",
    "PBO por Sharpe medido em 0,677 sobre 43 configurações candidatas.",
)


def carregar() -> pd.DataFrame:
    """Devolve a tabela de resultados por janela, indexada pela janela."""
    df = pd.read_csv(ARQUIVO)
    return df.set_index("janela")


def janelas(incluir_cheia: bool = False) -> pd.DataFrame:
    """Só as janelas cronológicas, sem a linha de amostra cheia."""
    df = carregar()
    return df if incluir_cheia else df.drop(index="amostra-cheia")


def reservada() -> pd.Series:
    """A janela que não participou de nenhuma escolha de regra ou parâmetro."""
    df = carregar()
    return df[df.reservada == 1].iloc[0]


def amostra_cheia() -> pd.Series:
    """A linha agregada do período inteiro."""
    return carregar().loc["amostra-cheia"]


def resumo() -> str:
    """Uma linha com o contraste que a série documenta."""
    r, c = reservada(), amostra_cheia()
    return (f"Amostra cheia: alpha {c.alpha:+.2%} (t = {c.t_alpha:.2f}). "
            f"Janela reservada: alpha {r.alpha:+.2%} (t = {r.t_alpha:.2f}).")
