# infraestrutura/gerenciador_configuracao.py
from typing import Dict, Any, Optional
from returns.result import Result, Success, Failure
from returns.curry import curry
from returns.pipeline import pipe
from returns.pointfree import bind

from repositorio_configuracao import RepositorioConfiguracao
from entidades import Configuracao, ProvedorIA

@curry
def obter_configuracao(
    repositorio: RepositorioConfiguracao
) -> Result[Configuracao, str]:
    """Obtém a configuração atual."""
    resultado = repositorio.obter_configuracoes()
    return resultado.lash(
        lambda erro: Failure(f'Erro ao obter configurações: {erro}')
    )

@curry
def obter_chave_api_para_provedor(
    repositorio: RepositorioConfiguracao,
    provedor: ProvedorIA
) -> Result[str, str]:
    """Obtém a chave API para um provedor específico."""
    resultado = repositorio.obter_chave_api(provedor)
    return resultado.lash(
        lambda erro: Failure(f'Chave API para {provedor.name} não disponível: {erro}')
    )

@curry
def salvar_configuracao(
    repositorio: RepositorioConfiguracao,
    configuracao: Configuracao
) -> Result[bool, str]:
    """Salva a configuração."""
    resultado = repositorio.salvar_configuracoes(configuracao)
    return resultado.lash(
        lambda erro: Failure(f'Erro ao salvar configurações: {erro}')
    )