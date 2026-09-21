"""Gráficos de diagnóstico no padrão visual Wizz.

Cada função aqui corresponde a uma figura do Apêndice B do manual ("Leitura
visual") ou a um conceito que precisa de imagem para ser ensinado.

A regra editorial que todas seguem, do manual de marca:

    Um gráfico útil deve declarar eixo, unidade, horizonte e comparação.
    Visual sofisticado sem pergunta explícita é apenas ruído visual.

Por isso toda função aceita ``fonte=`` e escreve o rodapé de procedência, e
nenhuma delas usa mais de duas cores de série.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

from . import brand
from .theme import figura, rotular_direto
from .metrics import risco, sinal, evidencia

_PCT = PercentFormatter(xmax=1, decimals=0)


def _fmt_r(ax, eixo: str = "x") -> None:
    getattr(ax, f"{eixo}axis").set_major_formatter(
        FuncFormatter(lambda v, _: f"{v:+.1f}R"))


# --- curva de capital --------------------------------------------------------
def curva_capital(retornos, benchmark=None, titulo="Curva de capital",
                  subtitulo="Base 100 · retorno acumulado", fonte="",
                  nome="Estratégia", nome_benchmark="Referência"):
    """Capital acumulado, com referência opcional.

    Duas séries no máximo, ambas rotuladas diretamente na ponta da linha --
    identidade nunca depende só da cor.
    """
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.6))
    cap = risco.curva_capital(retornos) * 100
    ax.plot(cap.index, cap.values, color=brand.SERIE_PRINCIPAL, zorder=3)
    rotular_direto(ax, cap.index[-1], cap.iloc[-1], nome, brand.SERIE_PRINCIPAL)

    if benchmark is not None:
        bench = risco.curva_capital(benchmark) * 100
        ax.plot(bench.index, bench.values, color=brand.SERIE_COMPARACAO,
                linewidth=1.8, zorder=2)
        rotular_direto(ax, bench.index[-1], bench.iloc[-1], nome_benchmark,
                       brand.SERIE_COMPARACAO)

    ax.axhline(100, color=brand.LINHA_SUTIL, linewidth=1, zorder=1)
    ax.set_ylabel("índice (base 100)")
    ax.margins(x=0.12)
    return fig, ax


def drawdown(retornos, titulo="Drawdown",
             subtitulo="Queda percentual desde o pico anterior", fonte=""):
    """Série de drawdown preenchida, com o MDD anotado.

    O manual lembra que o MDD observado é *uma amostra* do MDD possível. O
    subtítulo diz o que é; o Monte Carlo diz o que poderia ter sido.
    """
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 3.4))
    dd = risco.serie_drawdown(retornos)
    ax.fill_between(dd.index, dd.values, 0, color=brand.SERIE_COMPARACAO,
                    alpha=0.22, linewidth=0)
    ax.plot(dd.index, dd.values, color=brand.SERIE_COMPARACAO, linewidth=1.4)

    fundo = dd.idxmin()
    ax.annotate(f"MDD {dd.min():.1%}", xy=(fundo, dd.min()),
                xytext=(10, -14), textcoords="offset points",
                color=brand.SERIE_COMPARACAO, fontsize=9.5,
                fontweight="semibold")
    ax.yaxis.set_major_formatter(_PCT)
    ax.set_ylabel("drawdown")
    return fig, ax


# --- distribuição de trades --------------------------------------------------
def distribuicao_trades(r, titulo="Distribuição dos resultados por trade",
                        subtitulo="R-multiples · líquido de custos", fonte=""):
    """Histograma com média e mediana marcadas.

    A distância entre média e mediana é o diagnóstico: mostra se poucos
    winners sustentam o resultado.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.4))

    ax.hist(a, bins=40, color=brand.SERIE_PRINCIPAL, alpha=0.75,
            edgecolor=brand.MARFIM, linewidth=1.2)
    for valor, rotulo, cor, desloc in (
            (float(np.mean(a)), "média", brand.SERIE_COMPARACAO, 8),
            (float(np.median(a)), "mediana", brand.AZUL_PETROLEO, -46)):
        ax.axvline(valor, color=cor, linewidth=1.8, linestyle="--")
        ax.annotate(f"{rotulo} {valor:+.2f}R", xy=(valor, ax.get_ylim()[1] * 0.92),
                    xytext=(desloc, 0), textcoords="offset points",
                    color=cor, fontsize=9.5, fontweight="semibold")
    _fmt_r(ax)
    ax.set_xlabel("resultado do trade")
    ax.set_ylabel("nº de trades")
    return fig, ax


# --- Apêndice B, figura 1: Monte Carlo --------------------------------------
def monte_carlo(r, fracao_por_trade: float = 0.01, n_sim: int = 400,
                titulo="Monte Carlo: trajetórias alternativas",
                subtitulo="Reamostragem dos trades · capital base 1,0",
                fonte="", semente: int = 0):
    """Feixe de curvas simuladas com banda P5-P95 e mediana.

    O que observar, segundo o manual: a largura das bandas, a cauda inferior e
    como os percentis mudam com o método de resampling. **A linha mediana não
    é uma previsão** -- é o centro de uma distribuição de trajetórias.
    """
    caminhos = evidencia.monte_carlo_equity(r, fracao_por_trade, n_sim, semente)
    x = np.arange(caminhos.shape[1])
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.8))

    p05, p50, p95 = (np.quantile(caminhos, q, axis=0) for q in (0.05, 0.5, 0.95))
    ax.fill_between(x, p05, p95, color=brand.SERIE_PRINCIPAL, alpha=0.16,
                    linewidth=0)
    for linha in caminhos[:60]:
        ax.plot(x, linha, color=brand.SERIE_PRINCIPAL, alpha=0.07, linewidth=0.8)
    ax.plot(x, p50, color=brand.SERIE_PRINCIPAL, linewidth=2.2, zorder=4)
    ax.plot(x, p05, color=brand.SERIE_COMPARACAO, linewidth=1.5,
            linestyle="--", zorder=4)

    rotular_direto(ax, x[-1], p50[-1], "mediana", brand.SERIE_PRINCIPAL)
    rotular_direto(ax, x[-1], p05[-1], "P5", brand.SERIE_COMPARACAO)
    ax.axhline(1.0, color=brand.LINHA_SUTIL, linewidth=1)
    ax.set_xlabel("trades")
    ax.set_ylabel("capital (base 1,0)")
    ax.margins(x=0.10)
    return fig, ax


def distribuicao_mdd(r, fracao_por_trade: float = 0.01,
                     mdd_observado: float | None = None,
                     titulo="Drawdown máximo: observado vs. plausível",
                     subtitulo="Distribuição do MDD sob reamostragem",
                     fonte=""):
    """Histograma do MDD simulado, com o observado marcado.

    A figura que mais muda decisão de sizing: quase sempre o MDD observado
    está bem à direita da distribuição -- ou seja, o histórico foi sortudo.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    caminhos = evidencia.monte_carlo_equity(a, fracao_por_trade, 3000, 0)
    picos = np.maximum.accumulate(caminhos, axis=1)
    mdds = (caminhos / picos - 1).min(axis=1)

    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.2))
    ax.hist(mdds, bins=50, color=brand.SERIE_PRINCIPAL, alpha=0.75,
            edgecolor=brand.MARFIM, linewidth=1.0)
    p95 = float(np.quantile(mdds, 0.05))
    ax.axvline(p95, color=brand.SERIE_COMPARACAO, linewidth=1.8, linestyle="--")
    ax.annotate(f"P95 simulado {p95:.1%}", xy=(p95, ax.get_ylim()[1] * 0.9),
                xytext=(-8, 0), textcoords="offset points", ha="right",
                color=brand.SERIE_COMPARACAO, fontsize=9.5,
                fontweight="semibold")
    if mdd_observado is not None:
        ax.axvline(mdd_observado, color=brand.AZUL_PETROLEO, linewidth=1.8)
        ax.annotate(f"observado {mdd_observado:.1%}",
                    xy=(mdd_observado, ax.get_ylim()[1] * 0.72),
                    xytext=(8, 0), textcoords="offset points",
                    color=brand.AZUL_PETROLEO, fontsize=9.5,
                    fontweight="semibold")
    ax.xaxis.set_major_formatter(_PCT)
    ax.set_xlabel("drawdown máximo")
    ax.set_ylabel("nº de simulações")
    return fig, ax


# --- Apêndice B, figura 2: superfície de parâmetros --------------------------
def superficie_parametros(matriz, eixo_x, eixo_y, rotulo_x="parâmetro A",
                          rotulo_y="parâmetro B",
                          titulo="Superfície de parâmetros",
                          subtitulo="Métrica por combinação testada", fonte=""):
    """Heatmap sequencial de um único matiz, claro para escuro.

    O que observar: **regiões largas e suaves são mais convincentes que picos
    estreitos.** Um ótimo isolado cercado de resultados ruins é quase sempre
    ruído que foi escolhido depois do fato.
    """
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(7.4, 5.2))
    im = ax.imshow(np.asarray(matriz, float), cmap="wizz_verde",
                   origin="lower", aspect="auto",
                   extent=(min(eixo_x), max(eixo_x), min(eixo_y), max(eixo_y)))
    barra = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    barra.outline.set_visible(False)
    barra.ax.tick_params(length=0, labelsize=8.5)
    ax.grid(False)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel(rotulo_y)
    return fig, ax


# --- Apêndice B, figura 3: signal decay --------------------------------------
def signal_decay(ic_por_horizonte: pd.Series,
                 titulo="Decaimento do sinal",
                 subtitulo="Information Coefficient por horizonte à frente",
                 fonte=""):
    """Barras do IC por horizonte, com a meia-vida evidente.

    O manual avisa: um pico isolado merece suspeita e validação adicional, não
    comemoração.
    """
    s = pd.Series(ic_por_horizonte).sort_index()
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.0, 4.2))
    cores = [brand.SERIE_PRINCIPAL if v >= 0 else brand.SERIE_COMPARACAO
             for v in s.values]
    barras = ax.bar(range(len(s)), s.values, color=cores, width=0.68,
                    edgecolor=brand.MARFIM, linewidth=2.0)
    ax.bar_label(barras, fmt="%.3f", padding=3, fontsize=8.5,
                 color=brand.TEXTO_METADADO)
    ax.set_xticks(range(len(s)))
    ax.set_xticklabels([f"{h}" for h in s.index])
    ax.axhline(0, color=brand.LINHA_SUTIL, linewidth=1)
    ax.set_xlabel("horizonte (períodos à frente)")
    ax.set_ylabel("IC")
    return fig, ax


# --- Apêndice B, figura 4: quantis do indicador ------------------------------
def quantis_sinal(score, retorno_futuro, n_quantis: int = 5,
                  titulo="Retorno futuro por quantil do indicador",
                  subtitulo="Média do retorno à frente · por quintil do score",
                  fonte=""):
    """Barras por quantil, na rampa sequencial do verde.

    O que observar: **monotonicidade entre quantis é evidência mais estrutural
    que um único threshold otimizado.** Procure progressão coerente, inclusive
    fora da amostra.
    """
    tabela = sinal.quantile_analysis(score, retorno_futuro, n_quantis)
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.0, 4.4))
    rampa = list(reversed(brand.RAMPA_VERDE))[:len(tabela)]
    barras = ax.bar(tabela.index.astype(str), tabela.media.values,
                    color=rampa, width=0.66, edgecolor=brand.MARFIM,
                    linewidth=2.0)
    ax.bar_label(barras, fmt="%.4f", padding=3, fontsize=8.5,
                 color=brand.TEXTO_METADADO)
    mono = sinal.signal_monotonicity(score, retorno_futuro, n_quantis)
    ax.text(0.99, 0.04, f"monotonicidade (Spearman): {mono:+.2f}",
            transform=ax.transAxes, ha="right", fontsize=9,
            color=brand.TEXTO_METADADO)
    ax.axhline(0, color=brand.LINHA_SUTIL, linewidth=1)
    ax.set_xlabel("quantil do indicador (1 = menor score)")
    ax.set_ylabel("retorno médio à frente")
    return fig, ax


# --- Apêndice B, figura 5: MAE x MFE ----------------------------------------
def mae_mfe(trades: pd.DataFrame, titulo="MAE × MFE",
            subtitulo="Excursão adversa e favorável, por trade", fonte=""):
    """Nuvem MAE×MFE separando winners de losers.

    Duas séries, ambas com legenda E rótulo. Use a nuvem para **levantar
    hipóteses**, nunca para otimizar retroativamente um stop perfeito -- esse
    é exatamente o caminho para o overfitting.
    """
    df = trades.copy()
    ganhou = df.r_multiple > 0
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(7.2, 5.4))

    ax.scatter(df.mae[ganhou].abs(), df.mfe[ganhou], s=34,
               color=brand.SERIE_PRINCIPAL, alpha=0.65,
               edgecolor=brand.MARFIM, linewidth=1.2, label="winners")
    ax.scatter(df.mae[~ganhou].abs(), df.mfe[~ganhou], s=34,
               color=brand.SERIE_COMPARACAO, alpha=0.65, marker="s",
               edgecolor=brand.MARFIM, linewidth=1.2, label="losers")
    ax.legend(loc="upper left")
    ax.grid(True, axis="both", color=brand.LINHA_SUTIL, linewidth=0.7)
    ax.set_xlabel("MAE — excursão adversa máxima (R)")
    ax.set_ylabel("MFE — excursão favorável máxima (R)")
    return fig, ax


# --- Apêndice B, figura 6: concentração de P&L -------------------------------
def concentracao_pnl(r, titulo="Concentração do P&L",
                     subtitulo="Fração do lucro bruto acumulada pelos melhores trades",
                     fonte=""):
    """Curva de Lorenz do lucro.

    Uma curva que sobe muito rápido significa que poucos winners explicam a
    maior parte do resultado. Pode ser esperado em estratégias convexas -- mas
    precisa ser **explicitado** e testado com remoção dos melhores trades.
    """
    a = np.asarray(r, float)
    a = a[~np.isnan(a)]
    # Denominador é o lucro BRUTO (só os vencedores, do maior para o menor).
    # Contra o líquido a curva passaria de 100% e depois desceria: correto,
    # porque as perdas ainda não entraram, mas ilegível como leitura visual.
    a = np.sort(a[a > 0])[::-1]
    acumulado = np.cumsum(a) / a.sum()
    x = np.arange(1, len(a) + 1) / len(a)

    fig, ax = figura(titulo, subtitulo, fonte, figsize=(7.6, 4.6))
    ax.plot(x, acumulado, color=brand.SERIE_PRINCIPAL, zorder=3)
    ax.plot([0, 1], [0, 1], color=brand.SERIE_COMPARACAO, linewidth=1.5,
            linestyle="--", zorder=2)
    rotular_direto(ax, 1.0, 1.0, "distribuição uniforme",
                   brand.SERIE_COMPARACAO, dx=-8, dy=-18, ha="right")

    for frac in (0.05, 0.10):
        k = max(1, int(np.ceil(len(a) * frac)))
        ax.annotate(f"top {frac:.0%} dos vencedores → {acumulado[k - 1]:.0%} do lucro bruto",
                    xy=(frac, acumulado[k - 1]), xytext=(14, -4),
                    textcoords="offset points", fontsize=9,
                    color=brand.TEXTO_PRIMARIO)
        ax.scatter([frac], [acumulado[k - 1]], s=42,
                   color=brand.SERIE_PRINCIPAL, zorder=4,
                   edgecolor=brand.MARFIM, linewidth=2)
    ax.xaxis.set_major_formatter(_PCT)
    ax.yaxis.set_major_formatter(_PCT)
    ax.set_xlabel("fração dos trades, do melhor para o pior")
    ax.set_ylabel("fração do lucro total")
    return fig, ax


# --- incerteza ---------------------------------------------------------------
def intervalo_bootstrap(r, n_boot: int = 10_000,
                        titulo="O edge é um intervalo, não um ponto",
                        subtitulo="Distribuição bootstrap da expectancy",
                        fonte=""):
    """Distribuição bootstrap da média, com IC 95% e o zero marcado.

    É a figura que transforma "a estratégia rende +0,08R por trade" em "o que
    os dados suportam é algo entre -0,06R e +0,23R" -- uma afirmação bem
    diferente, e a honesta.
    """
    valores = evidencia.iid_bootstrap(r, n_boot=n_boot)
    lo, hi = np.quantile(valores, [0.025, 0.975])
    obs = float(np.nanmean(np.asarray(r, float)))

    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.2, 4.2))
    ax.hist(valores, bins=60, color=brand.SERIE_PRINCIPAL, alpha=0.70,
            edgecolor=brand.MARFIM, linewidth=1.0)
    ax.axvspan(lo, hi, color=brand.SERIE_PRINCIPAL, alpha=0.12, linewidth=0)
    ax.axvline(0, color=brand.SERIE_COMPARACAO, linewidth=2.0)
    ax.axvline(obs, color=brand.AZUL_PETROLEO, linewidth=1.8, linestyle="--")

    topo = ax.get_ylim()[1]
    ax.annotate("zero", xy=(0, topo * 0.95), xytext=(6, 0),
                textcoords="offset points", color=brand.SERIE_COMPARACAO,
                fontsize=9.5, fontweight="semibold")
    ax.annotate(f"observado {obs:+.3f}R", xy=(obs, topo * 0.80),
                xytext=(6, 0), textcoords="offset points",
                color=brand.AZUL_PETROLEO, fontsize=9.5, fontweight="semibold")
    ax.text(0.99, 0.05, f"IC 95%: [{lo:+.3f}R ; {hi:+.3f}R]",
            transform=ax.transAxes, ha="right", fontsize=9.5,
            color=brand.TEXTO_METADADO)
    _fmt_r(ax)
    ax.set_xlabel("expectancy reamostrada")
    ax.set_ylabel("frequência")
    return fig, ax


def rolling(retornos, janela: int = 252, metrica=np.mean,
            titulo="Métrica em janela móvel",
            subtitulo="Persistência do resultado ao longo do tempo", fonte=""):
    """Série móvel com o zero marcado e a fração de janelas positivas.

    O que se procura não é um valor alto: é um valor que **não desaparece**.
    """
    roll = sinal.rolling_metric(retornos, janela, metrica).dropna()
    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.0))
    ax.plot(roll.index, roll.values, color=brand.SERIE_PRINCIPAL)
    ax.fill_between(roll.index, roll.values, 0,
                    where=roll.values < 0, color=brand.SERIE_COMPARACAO,
                    alpha=0.22, linewidth=0)
    ax.axhline(0, color=brand.LINHA_SUTIL, linewidth=1.2)
    ax.text(0.99, 0.06, f"janelas positivas: {(roll > 0).mean():.0%}",
            transform=ax.transAxes, ha="right", fontsize=9.5,
            color=brand.TEXTO_METADADO)
    ax.set_ylabel(f"métrica ({janela} períodos)")
    return fig, ax


def gates(gates_avaliados, titulo="Scorecard de confiabilidade",
          subtitulo="Aprovação por gate · ordem de validação do manual",
          fonte=""):
    """Barras horizontais com a taxa de aprovação de cada gate.

    Cor semântica com rótulo -- nunca cor sozinha. Gates eliminatórios levam
    marcação explícita, porque o número sozinho esconde que um FAIL ali
    invalida tudo o que vem depois.
    """
    nomes = [f"Gate {g.numero} · {g.nome}" for g in gates_avaliados]
    taxas = [g.taxa for g in gates_avaliados]
    cores = [brand.POSITIVO if g.passou else brand.NEGATIVO
             for g in gates_avaliados]

    fig, ax = figura(titulo, subtitulo, fonte, figsize=(8.4, 4.4))
    y = np.arange(len(nomes))[::-1]
    barras = ax.barh(y, taxas, color=cores, height=0.62,
                     edgecolor=brand.MARFIM, linewidth=2.0)
    ax.bar_label(barras, labels=[f"{t:.0%}" for t in taxas], padding=6,
                 fontsize=9.5, color=brand.TEXTO_PRIMARIO,
                 fontweight="semibold")
    rotulos = [n + ("  (eliminatório)" if g.eliminatorio else "")
               for n, g in zip(nomes, gates_avaliados)]
    ax.set_yticks(y)
    ax.set_yticklabels(rotulos, fontsize=9.5)
    ax.set_xlim(0, 1.16)
    ax.xaxis.set_major_formatter(_PCT)
    ax.grid(True, axis="x", color=brand.LINHA_SUTIL, linewidth=0.7)
    ax.grid(False, axis="y")
    ax.set_xlabel("critérios aprovados dentro do gate")
    return fig, ax
