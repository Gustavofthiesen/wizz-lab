"""Gera as imagens dos carrosséis a partir do roteiro de cada post.

O roteiro fica aqui, em Python, e não em um arquivo de design: assim o texto do
post e o gráfico que o ilustra saem da **mesma fonte de verdade**, e um número
citado no copy não pode divergir do número plotado ao lado.

Rodar:

    python tools/gerar_posts.py

Saída em ``assets/posts/`` mais um ``manifest.json`` com o roteiro de cada card,
que é o que alimenta o planejamento editorial no Notion.
"""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from wizzlab import brand, cards, data, metrics  # noqa: E402
from wizzlab.theme import aplicar_tema  # noqa: E402

DESTINO = RAIZ / "assets" / "posts"
FONTE_PADRAO = "Dados simulados para fins didáticos · github.com/Gustavofthiesen/wizz-lab"
TRANSPARENCIA = brand.bloco_transparencia(
    data_base="20/09/2026", posicao="não possui",
    fontes="simulação própria, reprodutível por semente",
    ultima_revisao="20/09/2026")

aplicar_tema()
EST = data.gerar_estrategia(semente=42)
BENCH = data.gerar_benchmark(EST)
R = EST.trades.r_multiple.values


# =============================================================================
# POST 001 — Concept — "Investir não é prever. É decidir sob incerteza."
# =============================================================================
def post_001():
    def plot_leque(ax):
        caminhos = metrics.evidencia.monte_carlo_equity(R, 0.01, 300, 0)
        x = np.arange(caminhos.shape[1])
        p05, p50, p95 = (np.quantile(caminhos, q, axis=0) for q in (.05, .5, .95))
        ax.fill_between(x, p05, p95, color=brand.VERDE_FLORESTA, alpha=.18, lw=0)
        for linha in caminhos[:45]:
            ax.plot(x, linha, color=brand.VERDE_FLORESTA, alpha=.08, lw=.8)
        ax.plot(x, p50, color=brand.VERDE_FLORESTA, lw=2.4)
        ax.axhline(1, color=brand.LINHA_SUTIL, lw=1)
        ax.set_xlabel("operações", color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Investir não é prever. É decidir sob incerteza.",
            "concept", numero="POST 001",
            apoio="A diferença entre as duas coisas muda tudo que vem depois."),
        cards.conceito(
            "Prever é apostar em um número",
            "Quem prevê precisa acertar o futuro. Quem decide sob incerteza precisa "
            "de outra coisa: saber o que acontece em cada cenário, e conseguir "
            "sobreviver ao pior deles.",
            destaque="A pergunta muda de «o que vai acontecer?» para «o que eu "
                     "aguento se eu estiver errado?»."),
        cards.grafico(
            "O mesmo processo, 300 caminhos",
            plot_leque, "concept",
            leitura="Todos estes caminhos vêm das MESMAS regras. A diferença entre "
                    "eles é só a ordem em que os resultados apareceram.",
            rodape=FONTE_PADRAO),
        cards.conceito(
            "Por que isso importa",
            "O histórico que você viu foi um sorteio entre muitos possíveis. Se a "
            "sua decisão só funciona no caminho que aconteceu, ela não é uma "
            "decisão — é uma coincidência bem contada.",
            destaque="A linha do meio não é previsão. É o centro de uma distribuição."),
        cards.fechamento(
            "Processo antes de performance.", "portfolio",
            chamada="Aqui eu documento o método, os erros e a conta real. O código "
                    "de todos os gráficos é aberto.",
            transparencia=TRANSPARENCIA),
    ]


# =============================================================================
# POST 002 — Concept — "Duas carteiras renderam 15%. Qual foi melhor?"
# =============================================================================
def post_002():
    dd = metrics.risco.serie_drawdown(EST.diario)
    mdd = metrics.risco.max_drawdown(EST.diario)

    def plot_dd(ax):
        ax.fill_between(dd.index, dd.values, 0, color=brand.COBRE, alpha=.25, lw=0)
        ax.plot(dd.index, dd.values, color=brand.COBRE, lw=1.8)
        ax.axhline(0, color=brand.LINHA_SUTIL, lw=1)
        ax.set_ylabel("queda desde o pico", color=brand.CINZA_SALVIA, fontsize=11)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

    return [
        cards.capa(
            "Duas carteiras renderam 15%. Qual foi melhor?",
            "concept", numero="POST 002",
            apoio="A resposta não está no retorno. Está no que foi preciso aguentar "
                  "para chegar lá."),
        cards.conceito(
            "Retorno sozinho não é resultado",
            "Retorno é o que aconteceu. Risco é o que poderia ter acontecido — e "
            "quase aconteceu. Duas carteiras com o mesmo retorno podem ter corrido "
            "riscos completamente diferentes.",
            destaque="A pergunta certa não é «quanto rendeu», e sim «quanto de queda "
                     "foi preciso aguentar para render isso»."),
        cards.grafico(
            "O preço que a carteira cobrou",
            plot_dd, "data",
            leitura=f"Queda máxima de {abs(mdd):.0%}, e "
                    f"{metrics.risco.time_under_water(EST.diario):.0%} do tempo abaixo "
                    "do pico anterior.",
            rodape=FONTE_PADRAO),
        cards.conceito(
            "Profundidade e duração são riscos diferentes",
            "Uma queda de 15% que dura três anos costuma ser mais difícil de "
            "aguentar do que uma de 25% que dura dois meses. E só a segunda aparece "
            "bem em qualquer ranking.",
            destaque="Quase ninguém abandona uma estratégia pela profundidade. "
                     "Abandona pelo tempo."),
        cards.fechamento(
            "Compare o caminho, não só o destino.", "portfolio",
            chamada="No próximo: por que ganhar 50% não desfaz perder 50%.",
            transparencia=TRANSPARENCIA),
    ]


# =============================================================================
# POST 003 — Portfolio — "As regras antes da primeira posição"
# =============================================================================
def post_003():
    return [
        cards.capa(
            "As regras antes da primeira posição",
            "portfolio", numero="POST 003",
            apoio="Escrever a regra depois do resultado não é aprendizado. É "
                  "reescrever a história."),
        cards.conceito(
            "O que eu me comprometo a publicar",
            "Data-base e fontes em toda análise. Faixa de valor, nunca preço-alvo. "
            "Pesos percentuais da carteira. Caixa, concentração e giro. E as "
            "decisões que deram errado, com o mesmo destaque das que deram certo.",
            "portfolio",
            destaque="Toda tese vem com a frase «o que mudaria minha opinião» — "
                     "escrita ANTES, não depois."),
        cards.conceito(
            "O que isto não é",
            "Não é carteira recomendada. Não é ranking de performance. Não é "
            "desafio de enriquecimento. É o registro público de um processo de "
            "decisão, com os erros incluídos.",
            "portfolio",
            destaque="Se eu acertar, quero saber se foi método ou sorte. Sem "
                     "registro prévio, não dá para separar as duas coisas."),
        cards.conceito(
            "Como vou me comparar",
            "Sempre no mesmo período e contra referência adequada: CDI e índice de "
            "ações. Retorno sem benchmark e sem período declarado não é informação — "
            "é propaganda.",
            "portfolio",
            destaque="Um número sem unidade, período e fonte não entra em nenhum "
                     "post daqui."),
        cards.fechamento(
            "Premissas abertas. Riscos explícitos.", "portfolio",
            chamada="A carteira começa pequena e cresce ao vivo. O histórico que "
                    "vale é o que está sendo construído agora.",
            transparencia=TRANSPARENCIA),
    ]


# =============================================================================
# POST 004 — Data — "Perdeu 50%? Ganhar 50% não leva você de volta."
# =============================================================================
def post_004():
    quedas = np.array([.10, .20, .30, .40, .50, .60, .70])
    necessario = quedas / (1 - quedas)

    def plot_assimetria(ax):
        x = np.arange(len(quedas))
        ax.bar(x, quedas, width=.38, color=brand.CINZA_SALVIA,
               edgecolor=brand.MARFIM, lw=2, label="queda sofrida")
        ax.bar(x + .40, necessario, width=.38, color=brand.COBRE,
               edgecolor=brand.MARFIM, lw=2, label="alta necessária")
        ax.set_xticks(x + .20)
        ax.set_xticklabels([f"{q:.0%}" for q in quedas])
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.legend(frameon=False, fontsize=11, labelcolor=brand.AZUL_PETROLEO)
        ax.set_xlabel("tamanho da queda", color=brand.CINZA_SALVIA, fontsize=11)

    return [
        cards.capa(
            "Perdeu 50%? Ganhar 50% não leva você de volta.",
            "data", numero="POST 004",
            apoio="Precisa de 100%. E essa assimetria é o motivo de risco importar "
                  "mais que retorno."),
        cards.numero("+100%", "é o ganho necessário para desfazer uma queda de 50%",
                     "data",
                     contexto="Cair e subir a mesma porcentagem não se cancelam, "
                              "porque a base muda no caminho.",
                     rodape="Aritmética, não opinião."),
        cards.grafico(
            "A conta fica pior rápido",
            plot_assimetria, "data",
            leitura="Até 20% a diferença é pequena. Depois de 40%, ela vira o "
                    "problema principal.",
            rodape=FONTE_PADRAO),
        cards.conceito(
            "O que isso muda na prática",
            "Evitar a queda grande vale mais do que capturar a alta grande. É por "
            "isso que dimensionamento de posição e limite de perda não são detalhes "
            "operacionais — são a estratégia.",
            destaque="Sobreviver não é o prêmio de consolação. É a condição para "
                     "que os juros compostos tenham tempo de trabalhar."),
        cards.fechamento(
            "O primeiro trabalho é não quebrar.", "portfolio",
            chamada="No próximo: por que a média de retorno esconde exatamente isso.",
            transparencia=TRANSPARENCIA),
    ]


# =============================================================================
# POST 005 — Research — "Por que a média de retorno pode enganar?"
# =============================================================================
def post_005():
    media = metrics.trade.expectancy(R)
    mediana = metrics.trade.median_trade(R)
    conc = metrics.sinal.pnl_concentration(R)

    def plot_hist(ax):
        ax.hist(R, bins=38, color=brand.VERDE_FLORESTA, alpha=.78,
                edgecolor=brand.MARFIM, lw=1.2)
        for v, cor, dx in ((media, brand.COBRE, 8), (mediana, brand.AZUL_PETROLEO, 8)):
            ax.axvline(v, color=cor, lw=2, ls="--")
        ax.set_xlabel("resultado por operação (em R)", color=brand.CINZA_SALVIA,
                      fontsize=11)
        ax.annotate(f"média {media:+.2f}R", xy=(media, ax.get_ylim()[1] * .88),
                    xytext=(8, 0), textcoords="offset points", color=brand.COBRE,
                    fontsize=12, fontweight="semibold")
        ax.annotate(f"mediana {mediana:+.2f}R",
                    xy=(mediana, ax.get_ylim()[1] * .66), xytext=(8, 0),
                    textcoords="offset points",
                    color=brand.AZUL_PETROLEO, fontsize=12, fontweight="semibold")

    return [
        cards.capa(
            "Por que a média de retorno pode enganar?",
            "research", numero="POST 005",
            apoio="Porque ela não diz quem sustentou o resultado."),
        cards.grafico(
            "Média positiva, operação típica negativa",
            plot_hist, "research",
            leitura="A maioria das operações perde um pouco. Poucas ganham muito. "
                    "A média fica positiva — e a experiência do dia a dia, não.",
            rodape=FONTE_PADRAO),
        cards.numero(f"{conc.iloc[2]:.0%}",
                     "do lucro bruto vem dos 10% melhores resultados", "research",
                     contexto="Sem esses poucos casos, a estratégia é outra coisa. "
                              "Isso precisa ser uma escolha, não uma surpresa.",
                     rodape=FONTE_PADRAO),
        cards.conceito(
            "Isso é defeito?",
            "Não necessariamente. É o perfil de quem aceita muitas perdas pequenas "
            "em troca de poucos ganhos grandes. O problema não é depender da cauda — "
            "é depender dela sem saber.",
            "research",
            destaque="Teste honesto: remova os cinco melhores resultados. Se o edge "
                     "sumir, você tem eventos, não um processo."),
        cards.fechamento(
            "Leia a distribuição inteira, não o resumo.", "portfolio",
            chamada="O código que gera esta análise está aberto no GitHub.",
            transparencia=TRANSPARENCIA),
    ]


# =============================================================================
# POST 006 — Portfolio — "Como vamos medir desempenho"
# =============================================================================
def post_006():
    def plot_comparado(ax):
        cap = metrics.risco.curva_capital(EST.diario) * 100
        ben = metrics.risco.curva_capital(BENCH) * 100
        ax.plot(cap.index, cap.values, color=brand.VERDE_FLORESTA, lw=2.2)
        ax.plot(ben.index, ben.values, color=brand.COBRE, lw=1.8)
        ax.annotate("carteira", xy=(cap.index[-1], cap.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", color=brand.VERDE_FLORESTA,
                    fontsize=12, fontweight="semibold", va="center")
        ax.annotate("referência", xy=(ben.index[-1], ben.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", color=brand.COBRE, fontsize=12,
                    fontweight="semibold", va="center")
        ax.axhline(100, color=brand.LINHA_SUTIL, lw=1)
        ax.margins(x=.18)

    return [
        cards.capa(
            "Como vamos medir desempenho",
            "portfolio", numero="POST 006",
            apoio="Quatro números, sempre os mesmos, sempre no mesmo período."),
        cards.grafico(
            "Contra o quê, e em que período",
            plot_comparado, "portfolio",
            leitura="Retorno isolado não significa nada. Só a comparação no mesmo "
                    "período, contra referência adequada, é informação.",
            rodape=FONTE_PADRAO),
        cards.conceito(
            "Os quatro que vou publicar",
            "1. Retorno acumulado, contra CDI e índice.\n"
            "2. Queda máxima e tempo abaixo do pico.\n"
            "3. Caixa e concentração da carteira.\n"
            "4. Giro e custo pago no período.",
            "portfolio",
            destaque="Os dois últimos quase nunca aparecem — e são os que mais "
                     "explicam a diferença entre o backtest e a conta."),
        cards.conceito(
            "O que eu não vou fazer",
            "Não vou trocar de benchmark quando ficar conveniente. Não vou começar "
            "a contagem em uma data escolhida depois. Não vou mostrar retorno bruto "
            "onde o líquido é o que importa.",
            "portfolio",
            destaque="Se a régua mudar, eu aviso e explico por quê — no mesmo post."),
        cards.fechamento(
            "A mesma régua, sempre.", "portfolio",
            chamada="A carteira é pequena e cresce ao vivo. É o histórico que está "
                    "sendo construído agora que vai valer.",
            transparencia=TRANSPARENCIA),
    ]


ROTEIROS = {
    "post-001-incerteza": ("Investir não é prever. É decidir sob incerteza.",
                           "Concept", 1, "Terça", post_001),
    "post-002-duas-carteiras": ("Duas carteiras renderam 15%. Qual foi melhor?",
                                "Concept", 1, "Quinta", post_002),
    "post-003-regras": ("Wizz Portfolio — as regras antes da primeira posição",
                        "Portfolio", 1, "Domingo", post_003),
    "post-004-assimetria": ("Perdeu 50%? Ganhar 50% não leva você de volta.",
                            "Data", 2, "Terça", post_004),
    "post-005-media-engana": ("Por que a média de retorno pode enganar?",
                              "Research", 2, "Quinta", post_005),
    "post-006-medir": ("Wizz Portfolio — como vamos medir desempenho",
                       "Portfolio", 2, "Domingo", post_006),
}


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for antigo in DESTINO.glob("teste-*.png"):
        antigo.unlink()

    manifesto = []
    for slug, (titulo, serie, semana, dia, fabrica) in ROTEIROS.items():
        problemas = brand.checar_titulo(titulo)
        if problemas:
            raise SystemExit(f"título de {slug} usa termo banido: {problemas}")
        caminhos = cards.carrossel(fabrica(), slug, str(DESTINO))
        manifesto.append({
            "slug": slug, "titulo": titulo, "serie": serie,
            "semana": semana, "dia": dia, "n_cards": len(caminhos),
            "arquivos": [pathlib.Path(c).name for c in caminhos],
        })
        print(f"{slug:26} {len(caminhos)} cards · {serie} · semana {semana}")

    (DESTINO / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmanifest.json escrito com {len(manifesto)} posts")


if __name__ == "__main__":
    main()
