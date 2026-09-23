"""Gerador de cards de post no formato do Instagram (1080 × 1350).

Tudo em matplotlib, de propósito: os cards ficam versionados como código, são
reprodutíveis e mudam em bloco quando a marca muda. Nenhum deles é arte final
intocável -- são **direção de produção**.

A lógica que precisa permanecer, segundo o brand kit:

    label pequeno + linha cobre + um único elemento explicativo por card.

O registro do texto é o da nota técnica: título descritivo, legenda que declara
método e parâmetros, sem imperativo, sem segunda pessoa e sem a construção
"X não é Y, é Z". Os formatos que carregam conteúdo -- :func:`formula`,
:func:`tabela`, :func:`codigo`, :func:`referencias` -- existem para ocupar o
lugar que, de outro modo, o aforismo ocuparia.

Cinco papéis editoriais, mesma grade e mesma tipografia:

=============  ==========================================  =========
Série          Papel                                       Fundo
=============  ==========================================  =========
``concept``    Explica um conceito                         marfim
``data``       Mostra um número ou um gráfico              marfim
``research``   Apresenta um achado ou um teste             marfim
``portfolio``  Conta real, decisões, pesos                 petróleo
``note``       Nota curta, avulsa                          marfim
=============  ==========================================  =========
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from . import brand
from .theme import _primeira_fonte_disponivel

#: 1080 × 1350 px a 150 dpi.
LARGURA_PX, ALTURA_PX = 1080, 1350
DPI = 150
FIGSIZE = (LARGURA_PX / DPI, ALTURA_PX / DPI)

#: Margem lateral em fração da largura.
MARGEM = 0.085


@dataclass(frozen=True)
class EstiloSerie:
    """Aparência de cada papel editorial."""

    rotulo: str
    fundo: str
    tinta: str
    meta: str
    acento: str


ESTILOS: dict[str, EstiloSerie] = {
    "concept": EstiloSerie("WIZZ CONCEPT", brand.MARFIM, brand.AZUL_PETROLEO,
                           brand.CINZA_SALVIA, brand.COBRE),
    "data": EstiloSerie("WIZZ DATA", brand.MARFIM, brand.AZUL_PETROLEO,
                        brand.CINZA_SALVIA, brand.VERDE_FLORESTA),
    "research": EstiloSerie("WIZZ RESEARCH", brand.MARFIM, brand.AZUL_PETROLEO,
                            brand.CINZA_SALVIA, brand.COBRE),
    "portfolio": EstiloSerie("WIZZ PORTFOLIO", brand.AZUL_PETROLEO, brand.MARFIM,
                             brand.TEXTO_METADADO_ESCURO, brand.COBRE),
    "note": EstiloSerie("WIZZ NOTE", brand.MARFIM, brand.AZUL_PETROLEO,
                        brand.CINZA_SALVIA, brand.CINZA_SALVIA),
}


def _fontes() -> tuple[str, str]:
    return (_primeira_fonte_disponivel(brand.FONTES_TITULO),
            _primeira_fonte_disponivel(brand.FONTES_TEXTO))


def _base(serie: str) -> tuple[Figure, EstiloSerie]:
    """Cria a figura vazia com fundo, label da série e a régua cobre."""
    estilo = ESTILOS[serie]
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=estilo.fundo)
    # Os cards posicionam tudo manualmente; layout automático só atrapalha.
    fig.set_layout_engine("none")
    titulo_f, texto_f = _fontes()

    # Label da série, topo esquerdo.
    fig.text(MARGEM, 0.945, estilo.rotulo, fontsize=12.5, color=estilo.meta,
             family=texto_f, fontweight="bold", va="center")
    # Régua de acento logo abaixo — o "cobre é acento, não fundo".
    fig.add_artist(plt.Line2D([MARGEM, MARGEM + 0.10], [0.925, 0.925],
                              color=estilo.acento, linewidth=3.2,
                              solid_capstyle="butt"))
    # Assinatura, rodapé.
    fig.text(MARGEM, 0.042, "WIZZ", fontsize=15, color=estilo.tinta,
             family=titulo_f, fontweight="heavy", va="center")
    fig.text(MARGEM + 0.098, 0.042, "VALUATION & ALOCAÇÃO", fontsize=9.5,
             color=estilo.meta, family=texto_f, va="center")
    return fig, estilo


def _quebrar(texto: str, largura: int) -> str:
    return "\n".join(textwrap.wrap(texto, largura)) if texto else ""


def _largura_util(fig: Figure) -> float:
    """Largura disponível entre as margens, em polegadas."""
    return (1 - 2 * MARGEM) * fig.get_figwidth()


def _texto_ajustado(fig: Figure, texto: str, x: float, y: float, *,
                    fonte: str, tamanho: float, cor: str,
                    peso: str = "normal", va: str = "center",
                    linespacing: float = 1.2, min_tamanho: float = 10.0):
    """Escreve texto que **cabe** entre as margens, medindo de verdade.

    Quebra por palavra e, se ainda assim estourar, reduz o corpo em passos de
    meio ponto. Sem isso, um título uma palavra mais longo vaza para fora do
    card -- e é exatamente o tipo de erro que só aparece no post publicado.
    """
    limite = _largura_util(fig)
    renderer = fig.canvas.get_renderer()

    def cabe(conteudo: str, corpo: float) -> bool:
        artista = fig.text(x, y, conteudo, fontsize=corpo, family=fonte,
                           color=cor, fontweight=peso, va=va,
                           linespacing=linespacing)
        caixa = artista.get_window_extent(renderer=renderer)
        artista.remove()
        return caixa.width / fig.dpi <= limite

    corpo = tamanho
    while corpo >= min_tamanho:
        # Menor número de linhas que cabe neste corpo.
        for n_linhas in range(1, 9):
            largura_ch = max(8, int(len(texto) / n_linhas) + 6)
            candidato = _quebrar(texto, largura_ch)
            if candidato.count("\n") + 1 <= n_linhas and cabe(candidato, corpo):
                return fig.text(x, y, candidato, fontsize=corpo, family=fonte,
                                color=cor, fontweight=peso, va=va,
                                linespacing=linespacing)
        corpo -= 0.5
    return fig.text(x, y, _quebrar(texto, 20), fontsize=min_tamanho,
                    family=fonte, color=cor, fontweight=peso, va=va,
                    linespacing=linespacing)


# --- capa --------------------------------------------------------------------
def capa(titulo: str, serie: str = "concept", apoio: str = "",
         numero: str = "", figura_fn=None) -> Figure:
    """Card de abertura: o objeto medido e os valores principais.

    O título é um rótulo descritivo, no registro de título de nota técnica --
    "Dispersão do capital final sob reamostragem de trajetórias". Não é gancho,
    não é pergunta retórica e não monta contraste para chocar.

    ``apoio`` carrega o método e os números: n, semente, parâmetros e os
    valores que o post examina. É ele que permite a alguém decidir, no primeiro
    card, se o assunto interessa.
    """
    pergunta = titulo
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    if numero:
        fig.text(MARGEM, 0.875, numero, fontsize=11, color=estilo.acento,
                 family=texto_f, fontweight="bold", va="center")

    _texto_ajustado(fig, pergunta, MARGEM, 0.60, fonte=titulo_f,
                    tamanho=44, cor=estilo.tinta, peso="heavy",
                    linespacing=1.16, min_tamanho=26)

    if apoio:
        fig.text(MARGEM, 0.28, _quebrar(apoio, 46), fontsize=16,
                 color=estilo.meta, family=texto_f, va="center",
                 linespacing=1.5)
    return fig


# --- card de conceito --------------------------------------------------------
def conceito(titulo: str, corpo: str, serie: str = "concept",
             destaque: str = "", rodape: str = "") -> Figure:
    """Card de texto: um conceito, uma ideia. Nunca duas.

    ``destaque`` vira uma caixa com régua de acento à esquerda -- o mesmo
    tratamento que o manual de validação dá a "sinal favorável" e "ponto de
    atenção".
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.845, fonte=titulo_f, tamanho=30,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=20)

    y = 0.685
    fig.text(MARGEM, y, _quebrar(corpo, 42), fontsize=17.5,
             color=estilo.tinta, family=texto_f, va="top", linespacing=1.62)

    if destaque:
        linhas = _quebrar(destaque, 40)
        n = linhas.count("\n") + 1
        altura = 0.034 * n + 0.045
        topo = 0.245 + altura
        fig.patches.append(plt.Rectangle(
            (MARGEM, 0.245), 1 - 2 * MARGEM, altura,
            transform=fig.transFigure, facecolor=brand.SUPERFICIE_SUTIL
            if serie != "portfolio" else "#1B3B39", edgecolor="none", zorder=0))
        fig.add_artist(plt.Line2D([MARGEM, MARGEM], [0.245, topo],
                                  color=estilo.acento, linewidth=4.5))
        fig.text(MARGEM + 0.028, topo - 0.028, linhas, fontsize=16,
                 color=estilo.tinta, family=texto_f, va="top",
                 linespacing=1.5, fontweight="semibold")

    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top", linespacing=1.5)
    return fig


# --- card de número ----------------------------------------------------------
def numero(valor: str, legenda: str, serie: str = "data", contexto: str = "",
           rodape: str = "") -> Figure:
    """Hero number: quando o dado é um número só, não faça gráfico dele.

    O manual é explícito: *números importantes sempre acompanhados de unidade,
    período e fonte.* Por isso ``legenda`` e ``rodape`` não são opcionais na
    prática -- o número sozinho não significa nada.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, valor, MARGEM, 0.60, fonte=titulo_f, tamanho=112,
                    cor=estilo.acento, peso="heavy", min_tamanho=48)
    fig.text(MARGEM, 0.455, _quebrar(legenda, 34), fontsize=22,
             color=estilo.tinta, family=titulo_f, fontweight="semibold",
             va="top", linespacing=1.3)
    if contexto:
        fig.text(MARGEM, 0.315, _quebrar(contexto, 46), fontsize=16,
                 color=estilo.meta, family=texto_f, va="top", linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de gráfico ---------------------------------------------------------
def grafico(titulo: str, figura_fn, serie: str = "data", leitura: str = "",
            rodape: str = "") -> Figure:
    """Card com um gráfico embutido.

    Parameters
    ----------
    figura_fn:
        Função que recebe um ``Axes`` e desenha nele. Assim o card não precisa
        conhecer o gráfico, e qualquer função de :mod:`wizzlab.charts` pode ser
        adaptada.
    leitura:
        A frase de "o que observar". Um gráfico sem pergunta explícita é ruído
        visual -- este campo existe para que ela nunca falte.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=27,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=18)

    # Calha à esquerda para os rótulos de escala e o label do eixo Y. Sem ela,
    # um ylabel rotacionado vaza para fora do card — erro que só aparece depois
    # de publicado.
    CALHA = 0.070
    ax = fig.add_axes((MARGEM + CALHA, 0.335, 1 - 2 * MARGEM - CALHA, 0.40))
    ax.set_facecolor(estilo.fundo)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(estilo.meta)
    ax.tick_params(colors=estilo.meta, labelsize=11, length=0)
    ax.grid(True, axis="y", color=brand.LINHA_SUTIL if serie != "portfolio"
            else "#1E3C3A", linewidth=0.9)
    ax.set_axisbelow(True)
    figura_fn(ax)

    if leitura:
        fig.text(MARGEM, 0.255, _quebrar(leitura, 50), fontsize=15.5,
                 color=estilo.tinta, family=texto_f, va="top", linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de fechamento ------------------------------------------------------
def fechamento(frase: str, serie: str = "portfolio", chamada: str = "",
               transparencia: str = "") -> Figure:
    """Último card: a conclusão e, quando houver, o bloco de transparência.

    O bloco de transparência não é burocracia: é o ativo de reputação que o
    manual manda construir desde o primeiro dia.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, frase, MARGEM, 0.62, fonte=titulo_f, tamanho=34,
                    cor=estilo.tinta, peso="heavy", linespacing=1.22,
                    min_tamanho=22)
    if chamada:
        fig.text(MARGEM, 0.33, _quebrar(chamada, 44), fontsize=16.5,
                 color=estilo.meta, family=texto_f, va="center",
                 linespacing=1.55)
    if transparencia:
        fig.text(MARGEM, 0.160, _quebrar(transparencia, 74), fontsize=9.5,
                 color=estilo.meta, family=texto_f, va="top", linespacing=1.6)
    return fig


# --- card de fórmula ---------------------------------------------------------
def formula(titulo: str, expressao: str, termos: list[tuple[str, str]] | None = None,
            serie: str = "research", leitura: str = "", rodape: str = "") -> Figure:
    """Card com uma definição matemática e o glossário dos termos.

    Este card existe por uma razão editorial específica: a fórmula é o que
    separa explicar de afirmar. Mostrar ``E = p_W·W̄ − p_L·|L̄|`` e definir cada
    termo permite que o leitor confira a conta — e é justamente essa
    possibilidade de conferência que constrói autoridade.

    Parameters
    ----------
    expressao:
        Em sintaxe mathtext do matplotlib, sem os cifrões. Ex.:
        ``r"E = p_W \\bar{W} - p_L |\\bar{L}|"``.
    termos:
        Lista de ``(símbolo, significado)``. Sem isso, a fórmula vira enfeite.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=28,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=19)

    # A fórmula fica em uma faixa própria, para respirar.
    faixa_baixo, faixa_alto = 0.585, 0.755
    fig.patches.append(plt.Rectangle(
        (MARGEM, faixa_baixo), 1 - 2 * MARGEM, faixa_alto - faixa_baixo,
        transform=fig.transFigure,
        facecolor=brand.SUPERFICIE_SUTIL if serie != "portfolio" else "#1B3B39",
        edgecolor="none", zorder=0))
    fig.text(0.5, (faixa_baixo + faixa_alto) / 2, f"${expressao}$",
             fontsize=34, color=estilo.tinta, ha="center", va="center")

    y = 0.525
    for simbolo, significado in (termos or []):
        fig.text(MARGEM, y, f"${simbolo}$", fontsize=17, color=estilo.acento,
                 va="center")
        fig.text(MARGEM + 0.085, y, significado, fontsize=15,
                 color=estilo.tinta, family=texto_f, va="center")
        y -= 0.052

    if leitura:
        fig.text(MARGEM, max(y - 0.02, 0.20), _quebrar(leitura, 50),
                 fontsize=15.5, color=estilo.tinta, family=texto_f, va="top",
                 linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de tabela ----------------------------------------------------------
def tabela(titulo: str, cabecalho: tuple[str, ...], linhas: list[tuple],
           serie: str = "research", leitura: str = "", rodape: str = "",
           destacar: int | None = None) -> Figure:
    """Card com uma tabela de números.

    Uma tabela comunica precisão de um jeito que um gráfico não comunica: ela
    declara os valores em vez de sugeri-los. Use quando o ponto do post for a
    comparação exata entre poucos casos.

    Parameters
    ----------
    destacar:
        Índice da linha que recebe cor de acento — a que sustenta o argumento.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=28,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=19)

    n_col = len(cabecalho)
    largura = (1 - 2 * MARGEM)
    # Primeira coluna mais larga: costuma carregar o rótulo textual.
    pesos = [1.7] + [1.0] * (n_col - 1)
    total = sum(pesos)
    xs, acumulado = [], MARGEM
    for p in pesos:
        xs.append(acumulado)
        acumulado += largura * p / total

    def _x(i: int) -> float:
        """Primeira coluna alinha à esquerda; as de número, à direita."""
        return xs[i] if i == 0 else xs[i] + largura * pesos[i] / total

    y = 0.715
    for i, rotulo in enumerate(cabecalho):
        fig.text(_x(i), y, rotulo.upper(), fontsize=11.5, color=estilo.meta,
                 family=texto_f, fontweight="bold", va="center",
                 ha="left" if i == 0 else "right")
    fig.add_artist(plt.Line2D([MARGEM, 1 - MARGEM], [y - 0.022, y - 0.022],
                              color=estilo.acento, linewidth=2.0))

    y -= 0.062
    for k, linha in enumerate(linhas):
        cor = estilo.acento if k == destacar else estilo.tinta
        peso = "semibold" if k == destacar else "normal"
        for i, valor in enumerate(linha):
            fig.text(_x(i), y, str(valor), fontsize=16, color=cor,
                     family=texto_f, fontweight=peso, va="center",
                     ha="left" if i == 0 else "right")
        y -= 0.052

    if leitura:
        fig.text(MARGEM, max(y - 0.015, 0.20), _quebrar(leitura, 50),
                 fontsize=15.5, color=estilo.tinta, family=texto_f, va="top",
                 linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de código ----------------------------------------------------------
def codigo(titulo: str, linhas: list[str], saida: list[str] | None = None,
           serie: str = "research", leitura: str = "", rodape: str = "") -> Figure:
    """Card com código executável e a saída que ele produz.

    Este é o card que nenhum perfil de educação financeira consegue publicar, e
    é por isso que ele existe. Ele não afirma que o cálculo é possível: mostra
    as cinco linhas que o fazem, e o número que sai delas.

    Comentários (linhas iniciadas por ``#``) recebem a cor de metadado, para
    que a estrutura do trecho seja legível de relance no celular.

    Parameters
    ----------
    linhas:
        O trecho de código, uma string por linha. Mantenha abaixo de 10 linhas
        e 52 colunas — acima disso não se lê em tela de telefone.
    saida:
        O que o trecho imprime. Aparece destacado, em cor de acento.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()
    mono = _primeira_fonte_disponivel(
        ("Cascadia Mono", "Consolas", "JetBrains Mono", "DejaVu Sans Mono"))

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=27,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=18)

    fundo_bloco = brand.SUPERFICIE_SUTIL if serie != "portfolio" else "#1B3B39"
    altura_linha = 0.030
    n = len(linhas) + (len(saida) + 1 if saida else 0)
    topo = 0.760
    baixo = topo - altura_linha * n - 0.050
    fig.patches.append(plt.Rectangle(
        (MARGEM, baixo), 1 - 2 * MARGEM, topo - baixo,
        transform=fig.transFigure, facecolor=fundo_bloco, edgecolor="none",
        zorder=0))

    y = topo - 0.034
    for linha in linhas:
        cor = estilo.meta if linha.lstrip().startswith("#") else estilo.tinta
        fig.text(MARGEM + 0.028, y, linha, fontsize=14.5, family=mono,
                 color=cor, va="center")
        y -= altura_linha

    if saida:
        y -= altura_linha * 0.35
        fig.add_artist(plt.Line2D(
            [MARGEM + 0.028, 1 - MARGEM - 0.028], [y + 0.014, y + 0.014],
            color=estilo.acento, linewidth=1.2, alpha=0.55))
        y -= altura_linha * 0.30
        for linha in saida:
            fig.text(MARGEM + 0.028, y, linha, fontsize=14.5, family=mono,
                     color=estilo.acento, va="center", fontweight="bold")
            y -= altura_linha

    if leitura:
        fig.text(MARGEM, baixo - 0.030, _quebrar(leitura, 50), fontsize=15.5,
                 color=estilo.tinta, family=texto_f, va="top", linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de referências -----------------------------------------------------
def referencias(titulo: str, itens: list[tuple[str, str]],
                serie: str = "research", leitura: str = "",
                rodape: str = "") -> Figure:
    """Card com a bibliografia, com identificador verificável.

    Um post que cita "estudos mostram" pede confiança. Um post que imprime
    autor, ano, periódico e DOI dispensa confiança — e é essa diferença que
    define o público que o conteúdo atrai.

    Parameters
    ----------
    itens:
        Lista de ``(referência, identificador)``. O identificador é o DOI ou o
        periódico, impresso abaixo em cor de metadado.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=27,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=18)

    y = 0.735
    for i, (ref, ident) in enumerate(itens, start=1):
        fig.text(MARGEM, y, f"{i}", fontsize=15, color=estilo.acento,
                 family=texto_f, fontweight="bold", va="top")
        corpo = _quebrar(ref, 46)
        fig.text(MARGEM + 0.042, y, corpo, fontsize=14.5, color=estilo.tinta,
                 family=texto_f, va="top", linespacing=1.45)
        desce = 0.034 * (corpo.count("\n") + 1)
        fig.text(MARGEM + 0.042, y - desce - 0.006, ident, fontsize=11.5,
                 color=estilo.meta, family=texto_f, va="top")
        y -= desce + 0.058

    if leitura:
        fig.text(MARGEM, max(y - 0.010, 0.195), _quebrar(leitura, 50),
                 fontsize=15, color=estilo.tinta, family=texto_f, va="top",
                 linespacing=1.55)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- card de questões em aberto ----------------------------------------------
def em_aberto(titulo: str, questoes: list[str], serie: str = "research",
              proximo: str = "", rodape: str = "") -> Figure:
    """Card que fecha o carrossel com o que ficou por resolver.

    Substitui o card de conclusão. A diferença é deliberada: uma conclusão
    encerra o assunto e um conjunto de questões em aberto não — e o segundo é
    o que faz alguém procurar o próximo post, o notebook ou o artigo.

    Nenhuma das questões deve ser retórica. Todas precisam ter resposta
    conhecida, calculável, e endereço declarado no repositório ou na trilha.
    """
    fig, estilo = _base(serie)
    titulo_f, texto_f = _fontes()

    _texto_ajustado(fig, titulo, MARGEM, 0.875, fonte=titulo_f, tamanho=27,
                    cor=estilo.tinta, peso="heavy", va="top",
                    linespacing=1.18, min_tamanho=18)

    y = 0.720
    for i, questao in enumerate(questoes, start=1):
        fig.text(MARGEM, y, f"{i:02d}", fontsize=15, color=estilo.acento,
                 family=texto_f, fontweight="bold", va="top")
        corpo = _quebrar(questao, 42)
        fig.text(MARGEM + 0.062, y, corpo, fontsize=16, color=estilo.tinta,
                 family=texto_f, va="top", linespacing=1.5)
        y -= 0.038 * (corpo.count("\n") + 1) + 0.036

    if proximo:
        # A régua sobe o suficiente para que três linhas de `proximo` ainda
        # fiquem acima do rodapé, que é fixo em 0.115.
        fig.add_artist(plt.Line2D([MARGEM, 1 - MARGEM], [0.255, 0.255],
                                  color=estilo.acento, linewidth=2.0))
        fig.text(MARGEM, 0.230, _quebrar(proximo, 52), fontsize=14,
                 color=estilo.tinta, family=texto_f, va="top", linespacing=1.5)
    if rodape:
        fig.text(MARGEM, 0.115, _quebrar(rodape, 74), fontsize=11,
                 color=estilo.meta, family=texto_f, va="top")
    return fig


# --- utilidades --------------------------------------------------------------
def salvar(fig: Figure, caminho: str) -> str:
    """Salva o card em PNG no tamanho exato de 1080 × 1350, sem recorte.

    O `rc_context` aqui não é decorativo. O tema de gráfico define
    ``savefig.bbox = "tight"``, que é o certo para uma figura solta e o errado
    para um card: recorta as margens e entrega cada imagem com um tamanho
    diferente. Um carrossel do Instagram precisa de todas as peças com a mesma
    proporção, então aqui o recorte automático é desligado explicitamente.
    """
    import matplotlib as mpl
    with mpl.rc_context({"savefig.bbox": "standard", "savefig.pad_inches": 0.0}):
        fig.savefig(caminho, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return caminho


def carrossel(cards: list[Figure], prefixo: str, pasta: str = "assets/posts") -> list[str]:
    """Salva uma sequência de cards como ``prefixo-01.png``, ``-02``, ..."""
    import os
    os.makedirs(pasta, exist_ok=True)
    caminhos = []
    for i, fig in enumerate(cards, start=1):
        caminhos.append(salvar(fig, os.path.join(pasta, f"{prefixo}-{i:02d}.png")))
    return caminhos
