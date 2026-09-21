"""Metricas do *Manual de Validacao de Estrategias Sistematicas* (Wizz Lab).

Os modulos seguem a ordem de validacao do manual, nao a ordem alfabetica --
porque a ordem e o conteudo:

======================  ===========  ==========================================
Modulo                  Metricas     Pergunta do bloco
======================  ===========  ==========================================
:mod:`trade`            1-14         Como os trades ganham e perdem?
:mod:`risco`            15-42        Quanto risco custou, e da para sobreviver?
:mod:`evidencia`        43-62        Quanto disso pode ser sorte?
:mod:`generalizacao`    63-81        Sobrevive fora da amostra e a perturbacao?
:mod:`sinal`            82-107       O indicador tem informacao de verdade?
:mod:`execucao`         108-153      Sobrevive ao mercado real?
======================  ===========  ==========================================

Uso rapido::

    from wizzlab import metrics
    metrics.trade.resumo(trades.r_multiple)
"""
from . import trade, risco, evidencia, generalizacao, sinal, execucao

__all__ = ["trade", "risco", "evidencia", "generalizacao", "sinal", "execucao"]
