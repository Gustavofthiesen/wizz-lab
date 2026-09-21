"""Execucao, custos, liquidez, capacidade e integridade (metricas 108-153).

Capitulos 10, 11 e 12 do manual.

Este e o bloco que separa um resultado de planilha de um resultado de conta.
Tudo aqui responde a mesma pergunta por angulos diferentes: *o que acontece
com o edge quando ele precisa passar por um mercado real?*
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _arr(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[~np.isnan(a)]


# --- 108 a 110 ---------------------------------------------------------------
def slippage_sensitivity(r, custos=(0.0, 0.05, 0.10, 0.20, 0.40)) -> pd.Series:
    """**Quanto a performance piora quando o preco executado piora?**

    Recebe custos adicionais por trade na mesma unidade de `r` (R-multiples,
    normalmente) e devolve a expectancy resultante em cada nivel.

    A leitura util nao e o valor em cada linha: e a *inclinacao*. Uma
    estrategia cujo edge cai pela metade com 0,05R de custo extra e uma
    estrategia que nao existe fora do backtest.
    """
    a = _arr(r)
    return pd.Series({c: float((a - c).mean()) for c in custos})


def break_even_cost(r) -> float:
    """**Qual custo total por round trip zera a expectancy?**

    E simplesmente a expectancy bruta: o custo que a consome inteira.
    Compare com o custo real esperado -- essa razao e a margem de seguranca.
    """
    a = _arr(r)
    return float(a.mean()) if a.size else float("nan")


def cost_safety_margin(r, custo_esperado: float) -> float:
    """**Quantas vezes o custo suportavel excede o custo esperado?**

    Abaixo de 2x eu nao dormiria tranquilo: qualquer piora de spread,
    alargamento de book ou mudanca de corretagem come a margem.
    """
    be = break_even_cost(r)
    return float(be / custo_esperado) if custo_esperado else float("inf")


# --- 111 a 116 ---------------------------------------------------------------
def turnover(volume_negociado, patrimonio_medio: float) -> float:
    """**Quanto capital e negociado em relacao ao patrimonio?**

    Turnover alto nao e defeito por si -- e um multiplicador de custo. Leia
    sempre junto de :func:`break_even_cost`.
    """
    return float(np.sum(volume_negociado) / patrimonio_medio) if patrimonio_medio else float("nan")


def exposure(posicoes) -> float:
    """**Que fracao do tempo a estrategia fica exposta?**"""
    p = np.asarray(posicoes, float)
    return float((np.abs(p) > 0).mean()) if p.size else float("nan")


def capital_utilization(capital_alocado, capital_total) -> pd.Series:
    """**Que fracao do capital esta comprometida, em media e nos picos?**

    Caixa ocioso alto nao e necessariamente vazamento: pode ser o funil nao
    aprovando ninguem. Mas precisa ser explicado, nao ignorado.
    """
    a = np.asarray(capital_alocado, float) / capital_total
    return pd.Series({"media": float(a.mean()), "p95": float(np.quantile(a, 0.95)),
                      "maximo": float(a.max())})


def trades_por_ano(trades: pd.DataFrame, coluna_data: str = "data_entrada") -> float:
    """**A estrategia gera amostra suficiente por unidade de tempo?**

    Poucos trades por ano significam que voce vai precisar de decadas para
    saber se funciona -- o que e, em si, um risco de projeto.
    """
    datas = pd.to_datetime(trades[coluna_data])
    anos = (datas.max() - datas.min()).days / 365.25
    return float(len(trades) / anos) if anos > 0 else float("nan")


def holding_period(trades: pd.DataFrame, entrada: str = "data_entrada",
                   saida: str = "data_saida") -> pd.Series:
    """**Quanto tempo uma posicao permanece aberta?** Media, mediana e extremos."""
    d = (pd.to_datetime(trades[saida]) - pd.to_datetime(trades[entrada])).dt.days
    return pd.Series({"media": float(d.mean()), "mediana": float(d.median()),
                      "p95": float(d.quantile(0.95)), "maximo": float(d.max())})


def winner_vs_loser_holding(trades: pd.DataFrame, coluna_r: str = "r_multiple",
                            entrada: str = "data_entrada",
                            saida: str = "data_saida") -> pd.Series:
    """**Ganhos e perdas tem duracoes diferentes?**

    O padrao saudavel em sistemas convexos: perdas curtas, ganhos longos. O
    padrao preocupante e o inverso -- sinal de que o sistema realiza lucro
    cedo e carrega prejuizo esperando voltar.
    """
    d = (pd.to_datetime(trades[saida]) - pd.to_datetime(trades[entrada])).dt.days
    r = trades[coluna_r]
    return pd.Series({"winners_dias": float(d[r > 0].mean()),
                      "losers_dias": float(d[r < 0].mean())})


# --- 117 a 122 ---------------------------------------------------------------
def mae_mfe(trades: pd.DataFrame, mae: str = "mae", mfe: str = "mfe",
            r: str = "r_multiple") -> pd.DataFrame:
    """Tabela MAE x MFE por resultado do trade.

    A nuvem MAE x MFE revela a geometria intratrade: quanto os vencedores
    andaram contra antes de virar, e quanto do movimento favoravel a saida
    deixou na mesa. Use para levantar hipoteses -- nunca para otimizar
    retroativamente um stop perfeito.
    """
    df = trades[[mae, mfe, r]].copy()
    df["resultado"] = np.where(df[r] > 0, "winner", "loser")
    return df


def mfe_capture_ratio(trades: pd.DataFrame, mfe: str = "mfe",
                      r: str = "r_multiple") -> float:
    """**Quanto do movimento favoravel maximo foi efetivamente monetizado?**

    Media de ``R / MFE`` entre os vencedores. Perto de 1 significa saida
    quase perfeita -- o que, em backtest, e mais motivo de suspeita que de
    orgulho.
    """
    df = trades[trades[r] > 0]
    if df.empty:
        return float("nan")
    with np.errstate(divide="ignore", invalid="ignore"):
        razao = np.where(df[mfe] > 0, df[r] / df[mfe], np.nan)
    return float(np.nanmean(razao))


def mae_efficiency(trades: pd.DataFrame, mae: str = "mae",
                   r: str = "r_multiple", stop: float = 1.0) -> pd.Series:
    """**O stop esta longe demais em relacao as excursoes dos vencedores?**

    Se o pior MAE dos trades vencedores e muito menor que o stop, ha espaco
    para aperta-lo -- mas o teste honesto e refazer o backtest inteiro com o
    stop novo, nao inferir o ganho desta tabela.
    """
    vencedores = trades[trades[r] > 0][mae].abs()
    if vencedores.empty:
        return pd.Series(dtype=float)
    return pd.Series({
        "mae_medio_winners": float(vencedores.mean()),
        "mae_p95_winners": float(vencedores.quantile(0.95)),
        "stop_atual": float(stop),
        "folga_p95": float(stop - vencedores.quantile(0.95)),
    })


# --- 123 a 127 ---------------------------------------------------------------
def fill_probability(ordens_enviadas: int, ordens_executadas: int) -> float:
    """**Qual a chance de uma ordem limite ser realmente executada?**

    Backtests com ordens limite costumam supor fill garantido -- o que inverte
    a selecao: voce e executado justamente quando o mercado vai contra.
    """
    return float(ordens_executadas / ordens_enviadas) if ordens_enviadas else float("nan")


def slippage_distribution(slippages) -> pd.Series:
    """**Como o slippage varia, em vez de assumir um valor fixo?**

    A media engana quando a cauda e o que machuca. Reporte tambem P95 e P99.
    """
    a = _arr(slippages)
    if not a.size:
        return pd.Series(dtype=float)
    return pd.Series({"media": float(a.mean()), "mediana": float(np.median(a)),
                      "p95": float(np.quantile(a, 0.95)),
                      "p99": float(np.quantile(a, 0.99)),
                      "maximo": float(a.max())})


def participation_rate(volume_ordem, volume_mercado) -> float:
    """**Quanto a ordem representa do volume negociado?**

    Acima de alguns por cento do volume diario, voce deixa de ser tomador de
    preco e passa a fazer o preco contra si mesmo.
    """
    vm = float(np.sum(volume_mercado))
    return float(np.sum(volume_ordem) / vm) if vm else float("nan")


def capacity(expectancy_bruta: float, impacto_por_milhao: float) -> float:
    """**Quanto capital o sistema absorve antes de o edge ser destruido?**

    Modelo linear simples: capital (em milhoes) em que o impacto de mercado
    iguala a expectancy bruta. E uma aproximacao grosseira -- o impacto real
    costuma crescer com a raiz do tamanho, nao linearmente -- mas serve para
    saber se a ordem de grandeza e milhares ou milhoes.
    """
    return float(expectancy_bruta / impacto_por_milhao) if impacto_por_milhao else float("inf")


# --- 128 e 129 ---------------------------------------------------------------
def cross_market_transfer(resultado_por_mercado: dict[str, float],
                          mercado_base: str) -> pd.Series:
    """**Quanto da performance original se preserva em outros mercados?**

    Transferencia nao precisa ser perfeita; precisa existir. Uma logica que so
    funciona em um ativo geralmente esta descrevendo a historia daquele ativo.
    """
    s = pd.Series(resultado_por_mercado, dtype=float)
    base = s.get(mercado_base, float("nan"))
    razoes = s / base if base else s * float("nan")
    return pd.Series({"base": float(base),
                      "media_outros": float(s.drop(mercado_base).mean()),
                      "retencao_media": float(razoes.drop(mercado_base).mean()),
                      "mercados_positivos": float((s.drop(mercado_base) > 0).mean())})


# --- 130 a 137: auditorias de integridade (Gate 0) ---------------------------
#: Estas nao sao formulas -- sao verificacoes. O manual e explicito: quando a
#: medida nao tem definicao matematica unica, declare o procedimento em vez de
#: inventar uma equacao. A funcao abaixo apenas organiza o checklist.
AUDITORIAS_INTEGRIDADE = {
    "lookahead": "Alguma decisao usa informacao que nao existia no instante da ordem?",
    "repainting": "O indicador historico muda depois que novas barras chegam?",
    "same_bar": "Quando stop e target cabem na mesma barra OHLC, qual ocorreu primeiro?",
    "intrabar": "O resultado muda ao reconstruir caminhos intrabar plausiveis?",
    "timestamp": "Horarios, sessoes e fusos estao alinhados ao mercado real?",
    "corporate_action": "Precos ajustados e rolagens criam retornos artificiais?",
    "survivorship": "O universo historico inclui ativos que desapareceram?",
    "data_snooping": "Quantas decisoes foram tomadas olhando o mesmo historico?",
}


def auditoria_integridade(resultados: dict[str, bool]) -> pd.DataFrame:
    """Monta a tabela do Gate 0 a partir das auditorias declaradas.

    Qualquer FAIL material aqui invalida tudo o que vem depois. Nao adianta
    discutir Sharpe de um backtest com lookahead.

    Parameters
    ----------
    resultados:
        ``{chave: passou}`` usando as chaves de :data:`AUDITORIAS_INTEGRIDADE`.
        Chaves ausentes sao reportadas como *nao auditado* -- que, para efeito
        de gate, conta como falha.
    """
    linhas = []
    for chave, pergunta in AUDITORIAS_INTEGRIDADE.items():
        estado = resultados.get(chave)
        linhas.append({"auditoria": chave, "pergunta": pergunta,
                       "situacao": "PASS" if estado is True
                       else ("FAIL" if estado is False else "NAO AUDITADO")})
    return pd.DataFrame(linhas)


# --- 142 a 145: live versus backtest -----------------------------------------
def live_vs_backtest_gap(expectancy_live: float, expectancy_backtest: float,
                         ic_backtest: tuple[float, float]) -> pd.Series:
    """**A performance ao vivo esta dentro da distribuicao prevista?**

    Nao basta comparar dois numeros: compare o numero ao vivo com o
    *intervalo* previsto. Ficar abaixo da media e esperado metade das vezes;
    ficar fora do intervalo nao e.
    """
    lo, hi = ic_backtest
    return pd.Series({
        "expectancy_live": expectancy_live,
        "expectancy_backtest": expectancy_backtest,
        "gap": expectancy_live - expectancy_backtest,
        "ic_inferior": lo, "ic_superior": hi,
        "dentro_do_intervalo": bool(lo <= expectancy_live <= hi),
    })


def kill_switch(retornos_live, mdd_limite: float, n_trades_minimo: int = 30,
                expectancy_limite: float = 0.0) -> pd.Series:
    """**Quando a evidencia indica reduzir ou suspender a estrategia?**

    A regra precisa ser definida *ex ante*. Um kill-switch decidido durante o
    drawdown nao e gestao de risco -- e panico com nome tecnico.
    """
    from .risco import max_drawdown
    a = _arr(retornos_live)
    mdd = max_drawdown(a) if a.size else float("nan")
    amostra_ok = a.size >= n_trades_minimo
    return pd.Series({
        "n_observacoes": int(a.size),
        "amostra_suficiente": amostra_ok,
        "mdd_live": mdd,
        "mdd_limite": mdd_limite,
        "expectancy_live": float(a.mean()) if a.size else float("nan"),
        "acionar": bool(a.size and (mdd <= mdd_limite or
                                    (amostra_ok and a.mean() < expectancy_limite))),
    })


# --- 146 a 153: bruto vs liquido e relacao com o mercado ---------------------
def gross_vs_net(r_bruto, custos) -> pd.Series:
    """**Quanto da performance e consumida por friccoes?**"""
    b, c = _arr(r_bruto), _arr(custos)
    liquido = b - c
    return pd.Series({
        "expectancy_bruta": float(b.mean()),
        "expectancy_liquida": float(liquido.mean()),
        "custo_medio": float(c.mean()),
        "fracao_consumida": float(c.mean() / b.mean()) if b.mean() else float("nan"),
    })


def beta_e_alfa(retornos, benchmark) -> pd.Series:
    """**Quanto o PnL responde ao mercado, e o que sobra depois disso?**

    Regressao simples. O intercepto e o excesso em relacao a exposicao de
    mercado; o coeficiente e quanto do resultado e simplesmente estar comprado.

    Observacao de metodo: o benchmark precisa ser adequado. Contra um indice
    amplo, uma carteira setorial concentrada pode exibir excesso que some
    quando comparada a cesta do proprio setor.
    """
    y = _arr(retornos)
    x = _arr(benchmark)
    n = min(len(y), len(x))
    y, x = y[:n], x[:n]
    if n < 3:
        return pd.Series(dtype=float)
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuo = y - X @ beta
    dof = n - 2
    s2 = float((residuo ** 2).sum() / dof)
    cov = s2 * np.linalg.inv(X.T @ X)
    return pd.Series({
        "excesso_por_periodo": float(beta[0]),
        "t_excesso": float(beta[0] / np.sqrt(cov[0, 0])),
        "beta": float(beta[1]),
        "t_beta": float(beta[1] / np.sqrt(cov[1, 1])),
        "r2": float(1 - (residuo ** 2).sum() /
                    ((y - y.mean()) ** 2).sum()),
    })


def correlacao_entre_estrategias(retornos_por_estrategia: dict) -> pd.DataFrame:
    """**O sistema diversifica ou repete o mesmo risco?** Matriz de correlacao."""
    return pd.DataFrame(retornos_por_estrategia).corr()


def drawdown_overlap(retornos_a, retornos_b, limiar: float = -0.05) -> float:
    """**As estrategias sofrem ao mesmo tempo?**

    Fracao dos periodos em que ambas estao em drawdown acima do limiar.
    Correlacao media baixa com sobreposicao alta de drawdown e o pior dos
    mundos: diversificacao que evapora justamente quando seria necessaria.
    """
    from .risco import serie_drawdown
    da, db = serie_drawdown(retornos_a), serie_drawdown(retornos_b)
    n = min(len(da), len(db))
    if not n:
        return float("nan")
    return float(((da.values[:n] <= limiar) & (db.values[:n] <= limiar)).mean())
