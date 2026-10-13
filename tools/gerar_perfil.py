"""Kit de perfil: avatar e capa de destaque, nas medidas do Instagram.

O símbolo de origem é o bitmap do manual de marca, que o próprio manual
classifica como *direção conceitual* pendente de redesenho vetorial. O que este
script faz é só o enquadramento correto — fundo da marca, margem de segurança e
recorte circular seguro. Não redesenha nada.

Medidas
-------
* **Avatar**: 1080×1080. O Instagram recorta em círculo, então o símbolo fica
  dentro de um círculo interno com folga; nada encosta na borda.
* **Destaque**: 1080×1920, para capa de stories fixados.

Rodar::

    python tools/gerar_perfil.py
"""
from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wizzlab import brand  # noqa: E402
from wizzlab.theme import _primeira_fonte_disponivel  # noqa: E402

#: O símbolo vive no projeto privado; aqui só é lido.
SIMBOLO = (RAIZ.parent / "Valuation" / "assets" / "wizz_symbol.jpg")
DESTINO = RAIZ / "assets" / "perfil"


def _carregar_simbolo():
    """Lê o símbolo, homogeneíza o fundo e corta na caixa do desenho.

    Duas correções sobre o JPG de origem:

    1. O fundo é quase-marfim, com ruído de compressão. Tudo que é claro
       demais vira o marfim exato da marca, para o símbolo assentar no fundo
       sem uma moldura visível de tom ligeiramente diferente.
    2. O arquivo traz folga branca em volta e o desenho não está centrado
       (a caixa de tinta é 344×304 num quadro de 509). Cortar num quadrado
       centrado na tinta é o que permite dimensionar pelo desenho, não pelo
       arquivo — sem isso o avatar sai pequeno e torto no recorte circular.
    """
    img = plt.imread(SIMBOLO).astype(float) / 255.0
    marfim = np.array([243, 239, 229]) / 255.0
    claro = img.mean(axis=2) > 0.88
    img[claro] = marfim

    ys, xs = np.where(~claro)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    lado = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.06
    y0, y1 = int(max(0, cy - lado)), int(min(img.shape[0], cy + lado))
    x0, x1 = int(max(0, cx - lado)), int(min(img.shape[1], cx + lado))
    return img[y0:y1, x0:x1]


def avatar(fundo: str = brand.MARFIM, nome: str = "avatar_marfim") -> str:
    """Foto de perfil 1080×1080, com o símbolo dentro do recorte circular."""
    fig = plt.figure(figsize=(1080 / 150, 1080 / 150), dpi=150,
                     facecolor=fundo)
    fig.set_layout_engine("none")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(fundo)

    # O Instagram corta em círculo de raio 0,5 e exibe a ~110 px. O desenho
    # (já cortado na caixa de tinta) ocupa 70% do lado: o canto do quadrado
    # fica a 0,70·√2/2 = 0,495 do centro, dentro do círculo por pouco — e a
    # margem real é maior, porque os cantos do símbolo são vazios.
    lado = 0.70
    im = ax.imshow(_carregar_simbolo(),
                   extent=(0.5 - lado / 2, 0.5 + lado / 2,
                           0.5 - lado / 2, 0.5 + lado / 2), zorder=2)

    if fundo != brand.MARFIM:
        # Em fundo escuro, o fundo marfim do próprio bitmap vira um disco:
        # recortar a imagem num círculo evita a quina quadrada aparecendo
        # por fora do desenho, que é circular.
        disco = Circle((0.5, 0.5), lado * 0.50, transform=ax.transData)
        im.set_clip_path(disco)

    caminho = DESTINO / f"{nome}.png"
    fig.savefig(caminho, dpi=150, facecolor=fundo)
    plt.close(fig)
    return str(caminho)


def destaque(titulo: str, nome: str) -> str:
    """Capa de destaque 1080×1920, fundo petróleo com o rótulo centrado."""
    titulo_f, texto_f = (_primeira_fonte_disponivel(brand.FONTES_TITULO),
                         _primeira_fonte_disponivel(brand.FONTES_TEXTO))
    fig = plt.figure(figsize=(1080 / 150, 1920 / 150), dpi=150,
                     facecolor=brand.AZUL_PETROLEO)
    fig.set_layout_engine("none")

    fig.text(0.5, 0.56, titulo.upper(), fontsize=46, color=brand.MARFIM,
             family=titulo_f, fontweight="heavy", ha="center", va="center")
    fig.add_artist(plt.Line2D([0.38, 0.62], [0.48, 0.48], color=brand.COBRE,
                              linewidth=4, solid_capstyle="butt"))
    fig.text(0.5, 0.42, "WIZZ", fontsize=20, color=brand.TEXTO_METADADO_ESCURO,
             family=texto_f, fontweight="bold", ha="center", va="center")

    caminho = DESTINO / f"{nome}.png"
    fig.savefig(caminho, dpi=150, facecolor=brand.AZUL_PETROLEO)
    plt.close(fig)
    return str(caminho)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    if not SIMBOLO.exists():
        raise SystemExit(f"símbolo não encontrado em {SIMBOLO}")

    saidas = [avatar(brand.MARFIM, "avatar_marfim"),
              avatar(brand.AZUL_PETROLEO, "avatar_petroleo")]
    for titulo, nome in (("Métricas", "destaque_metricas"),
                         ("Resultados", "destaque_resultados"),
                         ("Método", "destaque_metodo"),
                         ("Código", "destaque_codigo")):
        saidas.append(destaque(titulo, nome))

    for s in saidas:
        print(pathlib.Path(s).name)
    print(f"\n{len(saidas)} arquivos em assets/perfil/")


if __name__ == "__main__":
    main()
