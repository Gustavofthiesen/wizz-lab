"""Post de abertura e post sobre a realização do P50.

O post 000 é a apresentação do perfil. A decisão editorial que o governa: a
medição desconfortável aparece **no card 3**, não ao final de seis meses. Um
perfil que abre declarando a janela em que o próprio resultado não se sustenta
seleciona o leitor que fica.

O post 009 publica a medição do P50 — o indicador que a estratégia usa para
decidir compra. Ele tem informação e não é alvo de preço, e as duas coisas são
mensuráveis separadamente.

Rodar::

    python tools/gerar_posts_abertura.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wizzlab import brand, cards, resultados as res  # noqa: E402
from wizzlab.theme import aplicar_tema, eixo_percentual  # noqa: E402

DESTINO = RAIZ / "assets" / "posts"
REPO = "github.com/Gustavofthiesen/wizz-lab"

aplicar_tema()
JAN = res.janelas()
CHEIA = res.amostra_cheia()
RESERVADA = res.reservada()
P50 = res.p50_realizacao()


def _br(t: str) -> str:
    return t.replace(".", ",").replace("-", "−")


def _pct(x, casas=1) -> str:
    return _br(f"{x * 100:+.{casas}f}%")


def _num(x, casas=2) -> str:
    return _br(f"{x:.{casas}f}")


# =============================================================================
# POST 000 — Note — apresentação do perfil
# =============================================================================
def post_000():
    def plot_janelas(ax):
        nomes = ["2017–19", "2020–21", "2022–23", "2024–26"]
        x = np.arange(len(JAN))
        cores = [brand.COBRE if r else brand.VERDE_FLORESTA for r in JAN.reservada]
        ax.bar(x, JAN.alpha, width=.5, color=cores, edgecolor=brand.MARFIM, lw=2)
        ax.axhline(0, color=brand.AZUL_PETROLEO, lw=1.4)
        ax.set_xticks(x)
        ax.set_xticklabels(nomes)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("excesso ajustado, a.a.", color=brand.CINZA_SALVIA,
                      fontsize=11)
        ax.annotate("janela reservada", xy=(3, JAN.iloc[3].alpha),
                    xytext=(0, 26), textcoords="offset points", ha="center",
                    fontsize=11.5, color=brand.COBRE, fontweight="semibold")

    return [
        cards.capa(
            "O que este perfil publica",
            "note", numero="000 · ABERTURA",
            apoio="Valuation de empresas brasileiras, com o método aberto e a "
                  "medição publicada — inclusive a janela em que o resultado "
                  "não se sustenta."),
        cards.tabela(
            "Três séries, duas publicações por semana",
            ("Série", "Conteúdo", "Quando"),
            [("Concept", "um conceito de validação", "terça"),
             ("Data", "uma medição, com método", "terça"),
             ("Research", "um teste conduzido", "sob demanda"),
             ("Portfolio", "a conta real, documentada", "domingo")],
            "note",
            leitura="Research sai quando houver medição conduzida, não por "
                    "calendário. Terça e domingo são fixos.",
            rodape="Cadência definida antes da primeira publicação"),
        cards.grafico(
            "A medição atual, antes de qualquer outra coisa",
            plot_janelas, "note",
            leitura=f"Excesso ajustado por risco da carteira, por janela. Na "
                    f"janela reservada — a que não participou de nenhuma "
                    f"escolha de regra — o excesso é {_pct(RESERVADA.alpha, 2)} "
                    f"com t = {_num(RESERVADA.t_alpha)}, e o intervalo de 95% "
                    "contém o zero.",
            rodape=f"2.315 pregões · {res.PERIODO} · {REPO}"),
        cards.conceito(
            "O critério de publicação",
            "Todo número sai com o método ao lado: tamanho de amostra, "
            "período, semente e fonte.\n\n"
            "Todo resultado de carteira sai com a janela reservada junto, não "
            "só com a amostra cheia.\n\n"
            "O que não foi medido é declarado como não medido.",
            "note",
            destaque="Resultados passados não garantem resultados futuros. "
                     "Conteúdo educacional, sem recomendação individualizada.",
            rodape="Manual de Marca Wizz V2 · seção 9, bloco de transparência"),
        cards.codigo(
            "O código é aberto e roda no navegador",
            ["from wizzlab import resultados",
             "",
             "r = resultados.reservada()",
             "print(r.cagr, r.alpha, r.t_alpha)",
             "",
             "for nota in resultados.RESSALVAS:",
             "    print(nota)"],
            saida=[f"{_num(RESERVADA.cagr, 4)}  {_num(RESERVADA.alpha, 4)}  "
                   f"{_num(RESERVADA.t_alpha)}",
                   "4 ressalvas declaradas"],
            serie="note",
            leitura="As ressalvas ficam no código, ao lado do número, para não "
                    "circularem separadas dele. Os notebooks abrem no Colab sem "
                    "instalar nada.",
            rodape=f"{REPO}"),
        cards.tabela(
            "O que não vai aparecer aqui",
            ("Não publica", "Motivo"),
            [("Preço-alvo", "a estimativa é uma faixa condicionada"),
             ("Chamada de compra", "o material é educacional"),
             ("Retorno sem referência", "número isolado não é informação"),
             ("Amostra cheia sozinha", "esconde a janela reservada"),
             ("Resultado sem o método", "não permite conferência")],
            "note",
            leitura="A última linha é a que governa as outras quatro.",
            rodape="Regra de nomenclatura: sem «trading», «calls» ou «alpha» "
                   "como promessa"),
        cards.em_aberto(
            "O que ainda não sei",
            ["Qual poder de detecção 651 pregões oferecem — a partir de que "
             "magnitude um excesso real seria visível?",
             "Quanto do resultado é seleção dentro do setor e quanto é "
             "inclinação setorial?",
             "O registro ao vivo, que começa agora, vai confirmar ou refutar "
             "a amostra cheia?"],
            "note",
            proximo="A terceira é a única que o tempo responde. As duas "
                    "primeiras são medições pendentes.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


# =============================================================================
# POST 009 — Research — realização do P50
# =============================================================================
def post_009():
    def plot_prometido(ax):
        nomes = list(P50.index)
        x = np.arange(len(P50))
        ax.bar(x - .19, P50.prometido, width=.38, color=brand.CINZA_SALVIA,
               edgecolor=brand.MARFIM, lw=2, label="prometido pelo P50")
        ax.bar(x + .19, P50.realizado_24m, width=.38, color=brand.VERDE_FLORESTA,
               edgecolor=brand.MARFIM, lw=2, label="realizado em 24 meses")
        ax.set_xticks(x)
        ax.set_xticklabels(nomes, fontsize=10.5)
        eixo_percentual(ax, "y", 0)
        ax.legend(frameon=False, fontsize=11.5, labelcolor=brand.AZUL_PETROLEO,
                  loc="upper left")
        ax.set_xlabel("desconto na entrada", color=brand.CINZA_SALVIA,
                      fontsize=11)

    def plot_razao(ax):
        nomes = list(P50.index)
        y = np.arange(len(P50))[::-1]
        razao = P50.preco_final_sobre_p50
        cores = [brand.VERDE_FLORESTA if v >= 0.95 else brand.COBRE
                 for v in razao]
        barras = ax.barh(y, razao, height=.46, color=cores,
                         edgecolor=brand.MARFIM, lw=2)
        ax.bar_label(barras, labels=[_num(v, 3) for v in razao], padding=6,
                     fontsize=12.5, color=brand.AZUL_PETROLEO,
                     fontweight="semibold")
        ax.axvline(1.0, color=brand.AZUL_PETROLEO, lw=1.8, ls="--")
        ax.set_yticks(y)
        ax.set_yticklabels(nomes, fontsize=11)
        ax.set_xlim(0, 1.32)
        ax.grid(False, axis="y")
        ax.set_xlabel("preço final ÷ P50 estimado na entrada",
                      color=brand.CINZA_SALVIA, fontsize=11)

    pior = P50.loc["acima de 60%"]

    return [
        cards.capa(
            "Realização do P50: o prometido contra o ocorrido em 24 meses",
            "research", numero="009 · DIAGNÓSTICO DO SINAL",
            apoio=f"4.844 observações. Na faixa de maior desconto, o P50 "
                  f"implica {_pct(pior.prometido, 1)} e o realizado foi "
                  f"{_pct(pior.realizado_24m, 1)}."),
        cards.conceito(
            "Duas leituras, ambas sustentadas pelos dados",
            "A inclinação do P50 contra o retorno futuro é positiva e "
            "significativa nos três horizontes testados, com t entre 2,8 e "
            "3,3. Ações com mais desconto renderam mais depois.\n\n"
            "No horizonte de 3 anos que a estratégia supõe, 13,5% do retorno "
            "prometido se materializa. Como previsão do preço futuro, o P50 é "
            "de duas a três vezes pior que usar o preço de hoje.",
            "research",
            destaque="Ter informação e ser um alvo de preço são propriedades "
                     "distintas, e medidas por testes distintos.",
            rodape="Manual de Validação · métricas 85 a 91"),
        cards.tabela(
            "Por faixa de desconto na entrada",
            ("Desconto", "Obs.", "Prometido", "Realizado 24m"),
            [(i, f"{int(l.observacoes):,}".replace(",", "."),
              _pct(l.prometido, 1), _pct(l.realizado_24m, 1))
             for i, l in P50.iterrows()],
            "research", destacar=3,
            leitura="A faixa de maior desconto concentra 3.240 das 4.844 "
                    "observações e é a que mais promete e menos entrega.",
            rodape=f"Carteira Wizz · {REPO}"),
        cards.grafico(
            "Prometido e realizado, lado a lado",
            plot_prometido, "research",
            leitura="O realizado é positivo em todas as faixas e quase "
                    "constante entre elas. O prometido cresce com o desconto; "
                    "o realizado, pouco.",
            rodape=f"4.844 observações · {REPO}"),
        cards.grafico(
            "Razão entre o preço final e o P50 estimado",
            plot_razao, "research",
            leitura="Valores abaixo de 1,0 indicam preço que não alcançou a "
                    "estimativa. Na faixa acima de 60% de desconto, o preço "
                    "final foi 48,3% do P50.",
            rodape=f"Horizonte de 24 meses · {REPO}"),
        cards.codigo(
            "Leitura da tabela publicada",
            ["from wizzlab import resultados",
             "",
             "t = resultados.p50_realizacao()",
             "print(t[['prometido', 'realizado_24m']])",
             "",
             "for a in resultados.P50_ACHADOS:",
             "    print(a)"],
            saida=[_br(f"0 a 12%        0.055   0.246"),
                   _br(f"12 a 30%       0.210   0.167"),
                   _br(f"30 a 60%       0.437   0.198"),
                   _br(f"acima de 60%   1.558   0.305")],
            serie="research",
            leitura="A consequência operacional já está aplicada: o P50 entra "
                    "como critério de ordenação entre candidatas, não como "
                    "preço de venda.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "Questões não cobertas",
            ["Se o desconto acima de 60% não entrega o que promete, qual "
             "faixa maximiza o realizado por unidade de risco?",
             "A razão preço/P50 de 0,483 vem de erro do modelo ou de "
             "seleção adversa nas empresas mais descontadas?",
             "O horizonte de 24 meses é o certo? Em que prazo a razão "
             "converge, se converge?"],
            "research",
            proximo="A segunda separa defeito de estimador de defeito de "
                    "universo, e muda o que precisa ser corrigido.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


ROTEIROS = {
    "post-000-abertura": ("O que este perfil publica", "Note", post_000),
    "post-009-p50-realizacao": (
        "Realização do P50: o prometido contra o ocorrido em 24 meses",
        "Research", post_009),
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    manifesto = []
    for slug, (titulo, serie, fabrica) in ROTEIROS.items():
        for antigo in DESTINO.glob(f"{slug}-*.png"):
            antigo.unlink()
        problemas = brand.checar_titulo(titulo)
        if problemas:
            raise SystemExit(f"título de {slug} usa termo banido: {problemas}")
        caminhos = cards.carrossel(fabrica(), slug, str(DESTINO))
        manifesto.append({"slug": slug, "titulo": titulo, "serie": serie,
                          "n_cards": len(caminhos),
                          "arquivos": [pathlib.Path(c).name for c in caminhos]})
        print(f"{slug:28} {len(caminhos)} cards · {serie}")

    destino = DESTINO / "manifest_abertura.json"
    destino.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"\n{destino.name} escrito com {len(manifesto)} posts")


if __name__ == "__main__":
    main()
