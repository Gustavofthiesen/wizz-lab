"""Scorecard de confiabilidade: os seis gates do manual, em ordem.

O manual e explicito sobre isso e vale repetir aqui, porque e a parte que mais
se ignora na pratica:

    Antes de olhar Sharpe, Calmar ou CAGR, trate integridade e edge liquido
    como gates *eliminatorios*.

Gates:

* **Gate 0 - Integridade.** Sem lookahead, repaint, survivorship ou fills
  impossiveis. Qualquer falha material invalida o resto.
* **Gate 1 - Edge economico liquido.** Expectancy positiva depois de custos
  conservadores.
* **Gate 2 - Evidencia.** Incerteza, tamanho efetivo de amostra, bootstrap.
* **Gate 3 - Generalizacao.** OOS, walk-forward, PBO, estabilidade.
* **Gate 4 - Sobrevivencia.** Drawdown, caudas, streaks, Monte Carlo, ruina.
* **Gate 5 - Execucao.** Spread, slippage, fill, turnover, liquidez, capacidade.

Um ponto de metodo que o proprio manual levanta e que esta implementado aqui:
**o score composto nao finge independencia entre dimensoes.** Ele nao e uma
media ponderada que deixa um gate otimo compensar outro reprovado. Um gate
eliminatorio reprovado derruba o conjunto, ponto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .metrics import trade, risco, evidencia, generalizacao, execucao


@dataclass
class Criterio:
    """Um teste unico dentro de um gate."""

    nome: str
    valor: float
    limite: float
    comparacao: str = ">="   # ">=", "<=", "bool"
    nota: str = ""

    @property
    def passou(self) -> bool:
        if self.valor is None or (isinstance(self.valor, float) and np.isnan(self.valor)):
            return False
        if self.comparacao == ">=":
            return bool(self.valor >= self.limite)
        if self.comparacao == "<=":
            return bool(self.valor <= self.limite)
        return bool(self.valor)


@dataclass
class Gate:
    """Um dos seis portoes de validacao."""

    numero: int
    nome: str
    eliminatorio: bool
    criterios: list[Criterio] = field(default_factory=list)

    @property
    def passou(self) -> bool:
        return all(c.passou for c in self.criterios) if self.criterios else False

    @property
    def taxa(self) -> float:
        if not self.criterios:
            return float("nan")
        return sum(c.passou for c in self.criterios) / len(self.criterios)

    def tabela(self) -> pd.DataFrame:
        return pd.DataFrame([{
            "gate": f"{self.numero} · {self.nome}",
            "criterio": c.nome,
            "valor": c.valor,
            "limite": c.limite,
            "situacao": "PASS" if c.passou else "FAIL",
            "nota": c.nota,
        } for c in self.criterios])


def avaliar(
    r_multiples,
    retornos_diarios,
    *,
    custo_esperado: float = 0.05,
    integridade: dict[str, bool] | None = None,
    matriz_configuracoes=None,
    mdd_tolerado: float = -0.30,
    periodos: int = 252,
) -> list[Gate]:
    """Roda os seis gates sobre uma estrategia e devolve a lista de Gates.

    Parameters
    ----------
    r_multiples:
        Resultados por trade, ja liquidos de custos.
    retornos_diarios:
        Serie de retornos da carteira, indexada por data.
    custo_esperado:
        Custo total esperado por round trip, na unidade dos R-multiples.
    integridade:
        Resultado das auditorias do Gate 0. Chaves em
        :data:`wizzlab.metrics.execucao.AUDITORIAS_INTEGRIDADE`. Ausente conta
        como nao auditado -- e nao auditado reprova.
    matriz_configuracoes:
        Matriz ``(T, N)`` com o desempenho de cada configuracao testada, para
        calcular o PBO. Sem ela, o criterio de overfitting fica como nao
        avaliado (portanto, reprovado).
    mdd_tolerado:
        Drawdown maximo que o capital e a tolerancia operacional aguentam.
    """
    r = np.asarray(r_multiples, float)
    r = r[~np.isnan(r)]
    integridade = integridade or {}

    # --- Gate 0 --------------------------------------------------------------
    aud = execucao.auditoria_integridade(integridade)
    g0 = Gate(0, "Integridade do backtest", eliminatorio=True, criterios=[
        Criterio(f"{linha.auditoria}", float(linha.situacao == "PASS"), 1.0,
                 "bool", linha.pergunta)
        for linha in aud.itertuples()
    ])

    # --- Gate 1 --------------------------------------------------------------
    be = execucao.break_even_cost(r)
    g1 = Gate(1, "Edge econômico líquido", eliminatorio=True, criterios=[
        Criterio("Expectancy líquida (R)", trade.expectancy(r), 0.0, ">=",
                 "Condição necessária, não suficiente."),
        Criterio("Profit factor", trade.profit_factor(r), 1.20, ">=",
                 "1,1 é frágil; 1,3-1,5 começa a interessar."),
        Criterio("Margem sobre break-even WR", trade.margem_de_edge(r), 0.02, ">=",
                 "Margem de poucos p.p. some com slippage."),
        Criterio("Margem de segurança de custo", execucao.cost_safety_margin(r, custo_esperado),
                 2.0, ">=", f"Custo que zera o edge: {be:.3f}R."),
    ])

    # --- Gate 2 --------------------------------------------------------------
    lo, _ = evidencia.bootstrap_ci(r)
    g2 = Gate(2, "Evidência estatística", eliminatorio=False, criterios=[
        Criterio("t-stat (Newey-West)", evidencia.newey_west_t(r), 2.0, ">=",
                 "Corrigido por autocorrelação e heterocedasticidade."),
        Criterio("IC 95% inferior > 0", lo, 0.0, ">=",
                 "O edge não é só um ponto estimado frágil."),
        Criterio("P(E > 0)", evidencia.prob_expectancy_positiva(r), 0.95, ">=", ""),
        Criterio("N efetivo", evidencia.effective_sample_size(r), 100, ">=",
                 "Observações independentes, não brutas."),
    ])

    # --- Gate 3 --------------------------------------------------------------
    criterios3 = [
        Criterio("Retenção OOS/IS", generalizacao.oos_is_ratio(r), 0.50, ">=",
                 "Alguma degradação é normal; inversão de sinal não."),
        Criterio("Walk-forward efficiency", generalizacao.walk_forward_efficiency(r),
                 0.50, ">=", ""),
        Criterio("Janelas OOS positivas", generalizacao.positive_oos_windows(r),
                 0.60, ">=", "Resultado não pode vir de uma janela só."),
    ]
    if matriz_configuracoes is not None:
        pbo = generalizacao.pbo_cscv(matriz_configuracoes)
        criterios3.append(Criterio("PBO (CSCV)", pbo, 0.50, "<=",
                                   "Acima de 0,5: escolher pelo backtest é pior que sortear."))
    else:
        criterios3.append(Criterio("PBO (CSCV)", float("nan"), 0.50, "<=",
                                   "Não avaliado: matriz de configurações não fornecida."))
    g3 = Gate(3, "Generalização", eliminatorio=False, criterios=criterios3)

    # --- Gate 4 --------------------------------------------------------------
    mc = risco.monte_carlo_mdd(r)
    g4 = Gate(4, "Sobrevivência", eliminatorio=False, criterios=[
        Criterio("MDD observado", risco.max_drawdown(retornos_diarios),
                 mdd_tolerado, ">=", "Compatível com capital e tolerância."),
        Criterio("MDD simulado P95", float(mc.get("P95", float("nan"))),
                 mdd_tolerado, ">=",
                 "O que você precisa aguentar, não o que aconteceu."),
        Criterio("Risk of ruin (50%)", risco.risk_of_ruin(r), 0.01, "<=", ""),
        Criterio("Sortino", risco.sortino(retornos_diarios, periodos=periodos),
                 0.50, ">=", ""),
    ])

    # --- Gate 5 --------------------------------------------------------------
    sens = execucao.slippage_sensitivity(r, custos=(0.0, custo_esperado * 2))
    retencao = (sens.iloc[1] / sens.iloc[0]) if sens.iloc[0] else float("nan")
    g5 = Gate(5, "Execução", eliminatorio=False, criterios=[
        Criterio("Edge sobrevive a 2x o custo", retencao, 0.50, ">=",
                 "Inclinação importa mais que o nível."),
        Criterio("Expectancy a 2x o custo", float(sens.iloc[1]), 0.0, ">=", ""),
    ])

    return [g0, g1, g2, g3, g4, g5]


def tabela(gates: list[Gate]) -> pd.DataFrame:
    """Junta todos os gates em uma tabela unica."""
    return pd.concat([g.tabela() for g in gates], ignore_index=True)


def veredito(gates: list[Gate]) -> pd.Series:
    """Resumo por gate, mais o veredito geral.

    Regra de composicao: um gate eliminatorio reprovado invalida o conjunto,
    independentemente de quao bem os outros foram. Isso e deliberado -- e a
    diferenca entre um scorecard e uma media ponderada que se deixa comprar.
    """
    linhas = {f"Gate {g.numero} · {g.nome}":
              f"{'PASS' if g.passou else 'FAIL'} ({g.taxa:.0%})" for g in gates}
    bloqueio = [g for g in gates if g.eliminatorio and not g.passou]
    if bloqueio:
        linhas["VEREDITO"] = ("REPROVADO — gate eliminatório: " +
                              ", ".join(f"{g.numero}" for g in bloqueio))
    elif all(g.passou for g in gates):
        linhas["VEREDITO"] = "APROVADO em todos os gates"
    else:
        falhos = [str(g.numero) for g in gates if not g.passou]
        linhas["VEREDITO"] = ("RESSALVAS — gates não eliminatórios com falha: " +
                              ", ".join(falhos))
    return pd.Series(linhas)


def composite_reliability_score(gates: list[Gate]) -> float:
    """Score composto em [0, 1] -- com a ressalva que o manual exige.

    **Este numero nao deve ser o titular de nenhuma apresentacao.** Ele resume
    dimensoes que nao sao independentes, e resumir e justamente o que faz
    perder a informacao que importa. Use a tabela por gate.

    Retorna 0.0 se qualquer gate eliminatorio reprovou.
    """
    if any(g.eliminatorio and not g.passou for g in gates):
        return 0.0
    taxas = [g.taxa for g in gates if not np.isnan(g.taxa)]
    return float(np.mean(taxas)) if taxas else float("nan")
