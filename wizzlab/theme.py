"""Tema matplotlib da Wizz.

Uso:

    from wizzlab.theme import aplicar_tema, figura
    aplicar_tema()
    fig, ax = figura("Curva de capital", "Simulacao didatica, 2010-2026")

Regras que o tema impoe sozinho, para nao depender de disciplina:

* fundo marfim, texto azul petroleo, grade salvia discreta;
* apenas grade horizontal, fina, atras dos dados;
* ciclo de cores com duas series (verde floresta, cobre) -- ver `brand.py`;
* sem moldura superior/direita;
* numeros tabulares e margens amplas.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from cycler import cycler

from . import brand

#: Mapa sequencial (magnitude): um unico matiz, claro -> escuro.
CMAP_SEQUENCIAL = LinearSegmentedColormap.from_list(
    "wizz_verde", list(reversed(brand.RAMPA_VERDE)))
#: Mapa divergente (polaridade): cobre <-> verde, cinza neutro no meio.
CMAP_DIVERGENTE = LinearSegmentedColormap.from_list(
    "wizz_div", list(brand.RAMPA_DIVERGENTE))

try:  # matplotlib >= 3.9 exige o nome no registro
    mpl.colormaps.register(CMAP_SEQUENCIAL, name="wizz_verde", force=True)
    mpl.colormaps.register(CMAP_DIVERGENTE, name="wizz_div", force=True)
except Exception:  # pragma: no cover - registro e conveniencia, nao requisito
    pass


def _primeira_fonte_disponivel(candidatas: tuple[str, ...]) -> str:
    """Devolve a primeira fonte instalada; cai no default do matplotlib."""
    from matplotlib import font_manager
    instaladas = {f.name for f in font_manager.fontManager.ttflist}
    for nome in candidatas:
        if nome in instaladas:
            return nome
    return candidatas[-1]


def aplicar_tema(escuro: bool = False) -> None:
    """Aplica o tema Wizz globalmente ao matplotlib.

    Parameters
    ----------
    escuro:
        Usa fundo azul petroleo. Reservado a serie Portfolio, que o manual
        visual pede mais escura para criar ritmo no feed.
    """
    fundo = brand.SUPERFICIE_ESCURA if escuro else brand.SUPERFICIE_CLARA
    tinta = brand.TEXTO_SOBRE_ESCURO if escuro else brand.TEXTO_PRIMARIO
    meta = brand.TEXTO_METADADO_ESCURO if escuro else brand.TEXTO_METADADO
    grade = "#1E3C3A" if escuro else brand.LINHA_SUTIL

    mpl.rcParams.update({
        "figure.facecolor": fundo,
        "axes.facecolor": fundo,
        "savefig.facecolor": fundo,
        "savefig.bbox": "tight",
        "savefig.dpi": 200,

        "font.family": "sans-serif",
        "font.sans-serif": [_primeira_fonte_disponivel(brand.FONTES_TEXTO)],
        "font.size": 10.5,

        "text.color": tinta,
        "axes.labelcolor": meta,
        "xtick.color": meta,
        "ytick.color": meta,
        "axes.edgecolor": grade,

        "axes.titlesize": 13,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlecolor": tinta,
        "axes.titlepad": 28,   # abre espaço para o subtítulo abaixo do título
        "axes.labelsize": 9.5,

        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.linewidth": 0.9,

        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": grade,
        "grid.linewidth": 0.7,
        "grid.alpha": 1.0,
        "axes.axisbelow": True,

        "axes.prop_cycle": cycler(color=list(brand.SERIES)),
        "lines.linewidth": 2.0,
        "lines.markersize": 8,
        "lines.solid_capstyle": "round",

        "patch.edgecolor": fundo,
        "patch.linewidth": 2.0,     # o "spacer" de 2px entre areas vizinhas

        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "legend.labelcolor": tinta,

        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,

        "figure.constrained_layout.use": True,
    })


def figura(titulo: str, subtitulo: str = "", fonte: str = "",
           figsize: tuple[float, float] = (8.0, 4.8), escuro: bool = False,
           **kwargs):
    """Cria uma figura ja titulada no padrao editorial da Wizz.

    O manual exige que todo grafico declare unidade, periodo e fonte. Esta
    funcao reserva o lugar dos tres: `titulo` diz o que e, `subtitulo` carrega
    unidade e periodo, `fonte` carrega a procedencia.

    Returns
    -------
    (Figure, Axes)
    """
    aplicar_tema(escuro=escuro)
    fig, ax = plt.subplots(figsize=figsize, **kwargs)
    meta = brand.TEXTO_METADADO_ESCURO if escuro else brand.TEXTO_METADADO

    ax.set_title(titulo)
    if subtitulo:
        # Ancorado em pontos, não em fração dos eixos: assim a distância até o
        # título não muda quando a figura muda de altura.
        ax.annotate(subtitulo, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 8), textcoords="offset points",
                    fontsize=9.5, color=meta, va="bottom", ha="left")
    if fonte:
        fig.text(0.0, -0.035, fonte, fontsize=8, color=meta, ha="left",
                 va="top")
    return fig, ax


def rotular_direto(ax, x, y, texto: str, cor: str, dx: float = 6.0,
                   dy: float = 0.0, **kwargs):
    """Escreve o nome da serie ao lado da propria linha.

    A paleta da Wizz e deliberadamente dessaturada. Rotulo direto e o que
    garante que a identidade da serie nunca dependa so da cor.
    """
    return ax.annotate(texto, xy=(x, y), xytext=(dx, dy),
                       textcoords="offset points", color=cor, fontsize=9.5,
                       fontweight="semibold", va="center", **kwargs)


def marca_dagua(fig, texto: str = brand.ASSINATURA, escuro: bool = False):
    """Assina a figura no rodape, discretamente."""
    cor = brand.TEXTO_METADADO_ESCURO if escuro else brand.TEXTO_METADADO
    fig.text(1.0, -0.035, texto, fontsize=7.5, color=cor, ha="right", va="top")
    return fig
