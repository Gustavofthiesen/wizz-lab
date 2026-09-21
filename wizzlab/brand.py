"""Tokens da marca Wizz.

Fonte: *Manual de Marca Wizz V2* (secoes 5 e 6) e *Manual de Validacao de
Estrategias Sistematicas v5*. Este modulo e a unica fonte de verdade de cor e
tipografia do pacote; nada aqui deve ser redefinido em outro arquivo.
"""
from __future__ import annotations

# --- Paleta oficial (Manual de Marca V2, secao 5) ---------------------------
AZUL_PETROLEO = "#102A2A"  # base, texto, autoridade, fundos escuros
VERDE_FLORESTA = "#2F5D50"  # longo prazo, destaques, dados e ensino
COBRE = "#B66A3C"           # personalidade, valor e pontos de atencao
MARFIM = "#F3EFE5"          # fundo principal, calma e legibilidade
BRONZE = "#A9854F"          # acento raro para marcos e alertas
CINZA_SALVIA = "#66736D"    # metadados, datas e informacao secundaria

PALETA = {
    "azul_petroleo": AZUL_PETROLEO,
    "verde_floresta": VERDE_FLORESTA,
    "cobre": COBRE,
    "marfim": MARFIM,
    "bronze": BRONZE,
    "cinza_salvia": CINZA_SALVIA,
}

#: Proporcao de uso recomendada pelo manual (secao 5).
PROPORCAO_USO = {"marfim": 0.60, "azul_petroleo": 0.25, "verde_floresta": 0.10,
                 "cobre_e_bronze": 0.05}

# --- Superficies -------------------------------------------------------------
SUPERFICIE_CLARA = MARFIM
SUPERFICIE_ESCURA = AZUL_PETROLEO
SUPERFICIE_SUTIL = "#ECE7DA"   # marfim um passo mais escuro, para caixas
LINHA_SUTIL = "#D8D2C4"        # grades e reguas

# --- Papeis de texto ---------------------------------------------------------
TEXTO_PRIMARIO = AZUL_PETROLEO
TEXTO_SECUNDARIO = "#4A5A55"
TEXTO_METADADO = CINZA_SALVIA
TEXTO_SOBRE_ESCURO = MARFIM
TEXTO_METADADO_ESCURO = "#8FA099"

# --- Series de grafico -------------------------------------------------------
# O manual proibe cores saturadas ("evitar neon, fundos saturados, azul
# eletrico, roxo intenso"). Isso limita quantas series podem ser distinguidas
# so por cor. A regra do pacote, portanto:
#
#   * duas series por cor, no maximo -- verde floresta e cobre;
#   * a terceira em diante NAO ganha matiz nova: vira degrau de luminosidade
#     do verde, small multiple, ou entra como "Outros";
#   * rotulo direto sempre presente, para que identidade nunca dependa so de cor;
#   * salvia e reservado a grade, eixo e metadado -- nunca e uma serie.
#
# Medicao do par canonico contra o marfim (ver `wizzlab.palette_check`):
#   dE normal 22.0 | dE protan/deutan 11.6 | contraste ok | croma do verde
#   abaixo do piso de 0.10 -- desvio deliberado da marca, compensado por
#   rotulo direto e pelo numero baixo de series.
SERIE_PRINCIPAL = VERDE_FLORESTA   # a estrategia, a tese, o objeto do post
SERIE_COMPARACAO = COBRE           # o benchmark, o contrafactual, o alerta
SERIES = (SERIE_PRINCIPAL, SERIE_COMPARACAO)

#: Degraus de luminosidade do verde, para quando forem precisas 3+ faixas
#: ordenadas (quantis, decis, faixas de um mesmo indicador).
RAMPA_VERDE = ("#1B3B32", "#2F5D50", "#4C7F70", "#7BA79A", "#B2CCC3", "#DCE7E3")

#: Rampa divergente: cobre <-> verde com cinza neutro no meio.
RAMPA_DIVERGENTE = ("#8E4A2A", "#B66A3C", "#D3A98B", "#CFCEC6",
                    "#8FB0A5", "#4C7F70", "#1B3B32")

# --- Cores semanticas --------------------------------------------------------
# Reservadas. Nunca reutilizar como "serie 3". Sempre com rotulo ou icone.
POSITIVO = VERDE_FLORESTA
NEGATIVO = "#8E4A2A"
ATENCAO = COBRE
NEUTRO = CINZA_SALVIA

# --- Tipografia (Manual de Marca V2, secao 6) --------------------------------
#: Titulos: Aptos Display Semibold. Alternativas digitais: Manrope, Inter.
FONTES_TITULO = ("Aptos Display", "Manrope", "Inter", "Segoe UI", "DejaVu Sans")
#: Texto: Aptos Regular. Alternativas digitais: Inter, Source Sans 3.
FONTES_TEXTO = ("Aptos", "Inter", "Source Sans 3", "Segoe UI", "DejaVu Sans")

# --- Textos institucionais ---------------------------------------------------
ASSINATURA = "WIZZ  ·  VALUATION & ALOCAÇÃO"
FRASE_PRINCIPAL = "Entender o negócio antes de olhar a cotação."
PRINCIPIO = "Processo antes de performance. Evidência antes de confiança."

AVISO_EDUCACIONAL = (
    "Conteúdo educacional. Não constitui recomendação individualizada, oferta "
    "ou promessa de retorno. Premissas podem estar erradas e resultados "
    "passados não garantem resultados futuros."
)


def bloco_transparencia(data_base: str, posicao: str, fontes: str,
                        ultima_revisao: str, conflitos: str = "nenhum") -> str:
    """Monta o bloco padrao de transparencia (Manual de Marca V2, secao 9).

    Toda publicacao analitica da Wizz deve carregar este bloco.
    """
    return (f"Data-base: {data_base} | Posição do autor: {posicao} | "
            f"Natureza: educacional | Principais fontes: {fontes} | "
            f"Última revisão: {ultima_revisao} | Conflitos relevantes: {conflitos}")


#: Termos banidos pela regra de nomenclatura (Manual de Marca V2, secao 4).
TERMOS_BANIDOS = ("trading", "signals", "calls", "alpha", "preço-alvo garantido",
                  "vai explodir", "antes que seja tarde")


def checar_titulo(titulo: str) -> list[str]:
    """Devolve os termos banidos encontrados em um titulo de post.

    A marca deve envelhecer bem: nada que prometa velocidade, previsao ou
    superioridade.
    """
    baixo = titulo.lower()
    return [t for t in TERMOS_BANIDOS if t in baixo]
