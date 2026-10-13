"""Card da composição da carteira, a partir de um CSV público de três colunas.

Por que o CSV é separado e tem só três colunas
-----------------------------------------------
O arquivo de alocação do motor privado tem **74 colunas**, e a maioria delas é
método: faixa de valor justo, margem de segurança, pontuação de seleção, perfil
e subsetor. Apontar o gerador público direto para ele seria publicar a
estratégia por descuido na primeira vez que alguém acrescentasse uma coluna ao
card.

Então a fronteira é física: ``data/carteira_publicada.csv`` tem exatamente
``ticker,nota,peso`` e é preenchido à mão (ou por um script do lado privado que
só sabe escrever essas três colunas). O caixa entra como a linha ``CAIXA``.
``cards.carteira`` ainda recusa qualquer rótulo com termo de método — é a
segunda barreira, não a primeira.

Rodar::

    python tools/gerar_carteira.py                 # usa o CSV público
    python tools/gerar_carteira.py --exemplo       # renderiza só o exemplo
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wizzlab import cards  # noqa: E402

ARQUIVO = RAIZ / "data" / "carteira_publicada.csv"
DESTINO = RAIZ / "assets" / "posts"
EXEMPLOS = RAIZ / "assets" / "exemplos"
REPO = "github.com/Gustavofthiesen/wizz-lab"

#: Composição fictícia, só para conferir o desenho do card. Não é carteira.
EXEMPLO = [("AAAA3", "", 0.118), ("BBBB4", "", 0.104), ("CCCC11", "", 0.091),
           ("DDDD3", "", 0.087), ("EEEE4", "", 0.072), ("FFFF3", "", 0.058)]
EXEMPLO_CAIXA = 0.470


def carregar(caminho: pathlib.Path = ARQUIVO):
    """Lê o CSV público e devolve ``(posições, caixa)``.

    Recusa colunas extras em vez de ignorá-las: uma coluna a mais no arquivo é
    exatamente o modo como o método vazaria, e passar batido seria pior que
    falhar.
    """
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    esperado = ["ticker", "nota", "peso"]
    if list(df.columns) != esperado:
        raise SystemExit(
            f"{caminho.name} deve ter exatamente {esperado}; "
            f"veio {list(df.columns)}. Colunas a mais é como o método vaza.")
    df["nota"] = df["nota"].fillna("").astype(str)
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    linha_caixa = df[df.ticker == "CAIXA"]
    if linha_caixa.empty:
        raise SystemExit(f"{caminho.name} precisa de uma linha CAIXA")
    caixa = float(linha_caixa.peso.iloc[0])
    posicoes = [(r.ticker, r.nota, float(r.peso))
                for r in df[df.ticker != "CAIXA"].itertuples()]
    return posicoes, caixa


def montar(posicoes, caixa, data: str, leitura: str = "") -> object:
    return cards.carteira(
        "Composição da carteira", posicoes, caixa, "resultado", data=data,
        leitura=leitura or (
            f"{len(posicoes)} posições e "
            f"{caixa * 100:.0f}% em caixa".replace(".", ",") +
            ". O caixa não é sobra: é a parte do patrimônio que, na data da "
            "foto, não estava comprada."),
        rodape=f"Pesos sobre o patrimônio da conta · {REPO} · conteúdo "
               "educacional, não é recomendação individualizada")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exemplo", action="store_true",
                    help="renderiza a composição fictícia, para ver o layout")
    ap.add_argument("--data", default="", help="data da foto, dd/mm/aaaa")
    args = ap.parse_args()

    if args.exemplo or not ARQUIVO.exists():
        EXEMPLOS.mkdir(parents=True, exist_ok=True)
        fig = cards.carteira(
            "Composição da carteira", EXEMPLO, EXEMPLO_CAIXA, "resultado",
            data="EXEMPLO — tickers fictícios",
            leitura="Layout do card. Os tickers são fictícios e os pesos não "
                    "correspondem a nenhuma carteira. Serve para conferir o "
                    "desenho antes de haver posição para publicar.",
            rodape="Exemplo de layout · nenhum dado real")
        caminho = cards.salvar(fig, str(EXEMPLOS / "carteira-exemplo.png"))
        print(pathlib.Path(caminho).name)
        if not ARQUIVO.exists():
            print(f"\n{ARQUIVO.relative_to(RAIZ)} não existe — nada real a "
                  "publicar ainda.")
        return

    posicoes, caixa = carregar()
    DESTINO.mkdir(parents=True, exist_ok=True)
    fig = montar(posicoes, caixa, args.data)
    print(pathlib.Path(cards.salvar(
        fig, str(DESTINO / "rc-carteira-01.png"))).name)


if __name__ == "__main__":
    main()
