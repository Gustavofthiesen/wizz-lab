"""Carrosséis construídos sobre os resultados publicados da carteira.

A diferença destes posts para os de `gerar_posts.py` é a fonte: aqui os números
vêm de `data/resultados_publicados.csv`, que é a medição da carteira real, e
não de uma série simulada.

Isso muda o que o material pode afirmar. Uma simulação demonstra um método; uma
medição documenta um resultado — inclusive quando o resultado é que o alpha não
sobrevive fora da amostra.

O registro do texto é o mesmo de `gerar_posts.py`: título descritivo, legenda
que declara método, sem imperativo e sem conclusão fechada.

Rodar::

    python tools/gerar_posts_carteira.py
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
FONTE = f"Carteira Wizz · {res.PERIODO} · {REPO}"

aplicar_tema()
JAN = res.janelas()
CHEIA = res.amostra_cheia()
RESERVADA = res.reservada()


def _br(t: str) -> str:
    return t.replace(".", ",").replace("-", "−")


def _pct(x, casas=1) -> str:
    return _br(f"{x * 100:+.{casas}f}%")


def _num(x, casas=2) -> str:
    return _br(f"{x:.{casas}f}")


ROTULO = {"2017-19": "2017–19", "2020-21": "2020–21",
          "2022-23": "2022–23", "2024-26": "2024–26"}


# =============================================================================
# POST 007 — Research — alpha por janela
# =============================================================================
def post_007():
    def plot_alpha(ax):
        nomes = [ROTULO[i] for i in JAN.index]
        x = np.arange(len(JAN))
        cores = [brand.COBRE if r else brand.VERDE_FLORESTA
                 for r in JAN.reservada]
        # A barra é o alpha; a haste é o intervalo de confiança de 95%.
        ax.errorbar(x, JAN.alpha, yerr=[JAN.alpha - JAN.ic95_inf,
                                        JAN.ic95_sup - JAN.alpha],
                    fmt="none", ecolor=brand.CINZA_SALVIA, elinewidth=1.8,
                    capsize=7, capthick=1.8, zorder=3)
        ax.bar(x, JAN.alpha, width=.52, color=cores, edgecolor=brand.MARFIM,
               lw=2, zorder=2)
        ax.axhline(0, color=brand.AZUL_PETROLEO, lw=1.4)
        ax.set_xticks(x)
        ax.set_xticklabels(nomes)
        eixo_percentual(ax, "y", 0)
        ax.set_ylabel("excesso ajustado, a.a.", color=brand.CINZA_SALVIA,
                      fontsize=11)
        for xi, (_, linha) in zip(x, JAN.iterrows()):
            ax.annotate(f"t = {_num(linha.t_alpha)}",
                        xy=(xi, linha.ic95_sup), xytext=(0, 8),
                        textcoords="offset points", ha="center", fontsize=11,
                        color=brand.AZUL_PETROLEO, fontweight="semibold")

    def plot_sharpe(ax):
        nomes = [ROTULO[i] for i in JAN.index]
        x = np.arange(len(JAN))
        cores = [brand.COBRE if r else brand.VERDE_FLORESTA
                 for r in JAN.reservada]
        barras = ax.bar(x, JAN.sharpe, width=.52, color=cores,
                        edgecolor=brand.MARFIM, lw=2)
        ax.bar_label(barras, labels=[_num(v) for v in JAN.sharpe], padding=4,
                     fontsize=12, color=brand.AZUL_PETROLEO,
                     fontweight="semibold")
        ax.set_xticks(x)
        ax.set_xticklabels(nomes)
        ax.axhline(0, color=brand.AZUL_PETROLEO, lw=1.2)
        ax.set_ylabel("Sharpe da janela", color=brand.CINZA_SALVIA, fontsize=11)
        ax.set_ylim(0, 2.1)

    return [
        cards.capa(
            "Excesso ajustado por risco, por janela, com intervalo de confiança",
            "research", numero="007 · CARTEIRA",
            apoio=f"2.315 pregões, {res.PERIODO}. Amostra cheia: "
                  f"{_pct(CHEIA.alpha, 2)} ao ano, t = {_num(CHEIA.t_alpha)}. "
                  f"Janela reservada: {_pct(RESERVADA.alpha, 2)}, "
                  f"t = {_num(RESERVADA.t_alpha)}."),
        cards.tabela(
            "Resultado por janela",
            ("Janela", "CAGR", "CDI", "Excesso aj.", "t"),
            [(ROTULO[i], _pct(l.cagr, 2).lstrip("+"), _pct(l.cdi, 2).lstrip("+"),
              _pct(l.alpha, 2), _num(l.t_alpha))
             for i, l in JAN.iterrows()]
            + [("Amostra cheia", _pct(CHEIA.cagr, 2).lstrip("+"),
                _pct(CHEIA.cdi, 2).lstrip("+"), _pct(CHEIA.alpha, 2),
                _num(CHEIA.t_alpha))],
            "research", destacar=3,
            leitura="A linha destacada é a janela reservada: não participou de "
                    "nenhuma escolha de regra ou parâmetro. É a única cujo "
                    "excesso pode ser lido sem desconto por seleção.",
            rodape=FONTE),
        cards.grafico(
            "Excesso ajustado e intervalo de 95%",
            plot_alpha, "research",
            leitura="Barras: excesso ajustado por risco, anualizado. Hastes: "
                    "intervalo de confiança "
                    "de 95%. Em 2024–26 o intervalo é "
                    f"[{_pct(RESERVADA.ic95_inf, 1)}; "
                    f"{_pct(RESERVADA.ic95_sup, 1)}] e contém o zero.",
            rodape=FONTE),
        cards.grafico(
            "Sharpe por janela",
            plot_sharpe, "research",
            leitura=f"O Sharpe da janela reservada é "
                    f"{_num(RESERVADA.sharpe)}, contra "
                    f"{_num(JAN.loc['2022-23'].sharpe)} na melhor janela do "
                    "período de construção.",
            rodape=FONTE),
        cards.formula(
            "O que a estatística t mede aqui",
            r"t = \frac{\hat{\alpha}}{\mathrm{ep}(\hat{\alpha})}",
            [(r"\hat{\alpha}", "excesso ajustado, estimado na janela"),
             (r"\mathrm{ep}", "erro-padrão da estimativa"),
             (r"t", "razão entre o efeito e a incerteza sobre ele")],
            "research",
            leitura="Valores abaixo de 2 indicam que a estimativa é pequena em "
                    "relação ao próprio erro de medição. Na janela reservada, "
                    f"t = {_num(RESERVADA.t_alpha)}.",
            rodape="Manual de Validação · métricas 43 e 52"),
        cards.codigo(
            "Leitura dos resultados publicados",
            ["from wizzlab import resultados",
             "",
             "r = resultados.reservada()",
             "c = resultados.amostra_cheia()",
             "",
             "print(c.alpha, c.t_alpha)",
             "print(r.alpha, r.t_alpha)"],
            saida=[f"cheia       {_num(CHEIA.alpha, 4)}   {_num(CHEIA.t_alpha)}",
                   f"reservada   {_num(RESERVADA.alpha, 4)}   {_num(RESERVADA.t_alpha)}"],
            serie="research",
            leitura="A tabela está em data/resultados_publicados.csv. O "
                    "repositório contém os resultados medidos, não as regras "
                    "que os produziram.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "O que esta medição não estabelece",
            ["651 pregões dão que poder de detecção? A partir de qual "
             "magnitude o teste enxergaria um excesso real?",
             "O beta subiu de 0,115 para 0,644 entre a primeira e a última "
             "janela. Quanto do resultado mudou de natureza?",
             "58% do excesso do baseline é inclinação setorial. Quanto sobra "
             "contra a cesta do próprio setor?"],
            "research",
            proximo="A primeira é uma análise de poder; a terceira exige o "
                    "benchmark setorial, e não o índice amplo.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


# =============================================================================
# POST 008 — Research — seleção de configuração e piso de ruído
# =============================================================================
def post_008():
    # PBO por CSCV medido no projeto, por tamanho do conjunto de candidatas.
    conjuntos = [("10 configurações", 10, 0.223),
                 ("43 configurações", 43, 0.677)]
    # Pisos de ruído medidos por intervenção-placebo.
    pisos = [("Recomposição de carteira", 0.005),
             ("Cache de valuation", 0.024)]

    def plot_pbo(ax):
        x = np.arange(len(conjuntos))
        valores = [v for _, _, v in conjuntos]
        cores = [brand.VERDE_FLORESTA if v < .5 else brand.COBRE
                 for v in valores]
        barras = ax.bar(x, valores, width=.46, color=cores,
                        edgecolor=brand.MARFIM, lw=2)
        ax.bar_label(barras, labels=[_num(v, 3) for v in valores], padding=5,
                     fontsize=13, color=brand.AZUL_PETROLEO,
                     fontweight="semibold")
        ax.axhline(0.5, color=brand.AZUL_PETROLEO, lw=1.8, ls="--")
        ax.annotate("0,50 — equivale a sortear", xy=(1.4, 0.5), xytext=(0, 7),
                    textcoords="offset points", ha="right", fontsize=11,
                    color=brand.AZUL_PETROLEO)
        ax.set_xticks(x)
        ax.set_xticklabels([n for n, _, _ in conjuntos])
        ax.set_ylim(0, 0.85)
        ax.set_ylabel("PBO (CSCV, por Sharpe)", color=brand.CINZA_SALVIA,
                      fontsize=11)

    def plot_piso(ax):
        y = np.arange(len(pisos))[::-1]
        valores = [v for _, v in pisos]
        barras = ax.barh(y, valores, height=.44, color=brand.COBRE,
                         edgecolor=brand.MARFIM, lw=2)
        ax.bar_label(barras, labels=[_br(f"±{v * 100:.1f} p.p.") for v in valores],
                     padding=6, fontsize=13, color=brand.AZUL_PETROLEO,
                     fontweight="semibold")
        ax.set_yticks(y)
        ax.set_yticklabels([n for n, _ in pisos], fontsize=11.5)
        ax.set_xlim(0, 0.032)
        eixo_percentual(ax, "x", 1)
        ax.grid(False, axis="y")
        ax.set_xlabel("variação de CAGR sem conteúdo",
                      color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Probabilidade de overfitting na escolha da configuração",
            "research", numero="008 · MÉTODO",
            apoio="PBO por CSCV medido sobre as configurações candidatas deste "
                  "projeto: 0,223 com 10 candidatas e 0,677 com 43."),
        cards.formula(
            "O que o PBO estima",
            r"\mathrm{PBO} = \Pr\!\left[\,\mathrm{posto}_{\mathrm{OOS}}"
            r"(c^{*}_{\mathrm{IS}}) < \mathrm{mediana}\,\right]",
            [(r"c^{*}_{\mathrm{IS}}", "configuração campeã dentro da amostra"),
             (r"\mathrm{posto}_{\mathrm{OOS}}", "posto dela fora da amostra")],
            "research",
            leitura="A fração das divisões em que a campeã dentro da amostra "
                    "cai abaixo da mediana fora dela. Em 0,50, o procedimento "
                    "de seleção equivale a sortear.",
            rodape="Bailey, Borwein, López de Prado & Zhu (2017) · métrica 68"),
        cards.grafico(
            "PBO por tamanho do conjunto de candidatas",
            plot_pbo, "research",
            leitura="O PBO cresce com o número de configurações avaliadas. As "
                    "dez do conjunto menor são quase idênticas entre si, o que "
                    "reduz a medida sem reduzir a exposição real à seleção.",
            rodape=f"Medição própria por CSCV · {REPO}"),
        cards.grafico(
            "Piso de ruído por intervenção-placebo",
            plot_piso, "research",
            leitura="Variação de CAGR produzida por intervenções sem conteúdo "
                    "econômico. Diferenças menores que o piso não são "
                    "distinguíveis de ruído de implementação.",
            rodape=f"Medição própria · {REPO}"),
        cards.tabela(
            "Dois testes com veredito oposto",
            ("Hipótese", "Critérios", "Placebo"),
            [("Célula por subsetor", "7 de 7", "5 de 5 — aprovada"),
             ("Célula por faixa de volume", "—", "1 de 5 — reprovada"),
             ("Calibrar aprovação por setor", "7 de 7", "reprovada")],
            "research", destacar=2,
            leitura="A terceira linha passou em todos os critérios "
                    "pré-registrados e não superou intervenções sem conteúdo. "
                    "O placebo é o que separa as duas primeiras.",
            rodape="Manual de Validação · métricas 68 a 72 e 139"),
        cards.codigo(
            "Cálculo do PBO sobre uma matriz de configurações",
            ["from wizzlab.metrics import generalizacao as g",
             "",
             "# M: períodos nas linhas, configurações nas colunas",
             "print(g.pbo_cscv(M))",
             "",
             "# p-valor após data snooping",
             "print(g.reality_check(M))"],
            saida=["PBO            0,677",
                   "Reality Check  ver notebook 3"],
            serie="research",
            leitura="O mesmo procedimento aplicado a 40 configurações de ruído "
                    "puro está no notebook 3, e devolve PBO próximo de 0,5.",
            rodape=f"Executável no Colab · {REPO}"),
        cards.em_aberto(
            "O que fica pendente",
            ["Quantas configurações foram efetivamente avaliadas ao longo do "
             "projeto, contando as não registradas?",
             "Com o inventário completo de tentativas, qual é o Deflated "
             "Sharpe da configuração vigente?",
             "Um PBO de 0,677 invalida a configuração, ou invalida o "
             "procedimento de escolha entre configurações?"],
            "research",
            proximo="A terceira é a pergunta que decide se o número muda a "
                    "estratégia ou muda o método de seleção.",
            rodape=f"Conteúdo educacional · {REPO}"),
    ]


ROTEIROS = {
    "post-007-excesso-por-janela": (
        "Excesso ajustado por risco, por janela, com intervalo de confiança",
        "Research", post_007),
    "post-008-pbo-e-placebo": (
        "Probabilidade de overfitting na escolha da configuração",
        "Research", post_008),
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
        print(f"{slug:30} {len(caminhos)} cards · {serie}")

    destino_manifesto = DESTINO / "manifest_carteira.json"
    destino_manifesto.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{destino_manifesto.name} escrito com {len(manifesto)} posts")


if __name__ == "__main__":
    main()
