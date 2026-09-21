"""Wizz Lab — ferramentas de validação de estratégias sistemáticas.

Companheiro de código do *Manual de Validação de Estratégias Sistemáticas* e do
*Manual de Marca Wizz V2*.

    Processo antes de performance. Evidência antes de confiança.

Uso típico::

    from wizzlab import brand, theme, data, metrics, scorecard

    est = data.gerar_estrategia()
    metrics.trade.resumo(est.trades.r_multiple)
    gates = scorecard.avaliar(est.trades.r_multiple, est.diario)
    scorecard.veredito(gates)

Aviso: conteúdo educacional. Não constitui recomendação individualizada,
oferta ou promessa de retorno.
"""
from . import brand, data, metrics, scorecard, theme

__version__ = "0.1.0"
__all__ = ["brand", "data", "metrics", "scorecard", "theme", "charts", "cards"]


def __getattr__(nome):  # imports preguicosos: charts e cards puxam matplotlib
    if nome in ("charts", "cards"):
        import importlib
        return importlib.import_module(f".{nome}", __name__)
    raise AttributeError(nome)
