# portas/repositorio_configuracao.py
from typing import Protocol, Dict, Any
from returns.result import Result

from ..dominio.entidades import Configuracao, ProvedorIA, ChaveAPI, ErroConfiguracao

class RepositorioConfiguracao(Protocol):
    """
    Porta que define a interface para armazenamento e recuperação de configurações.
    """
    def salvar_chave_api(self, provedor: ProvedorIA, chave: ChaveAPI) -> Result[bool, ErroConfiguracao]:
        """Salva a chave de API de forma segura."""
        ...
    
    def obter_chave_api(self, provedor: ProvedorIA) -> Result[ChaveAPI, ErroConfiguracao]:
        """Recupera a chave de API de forma segura."""
        ...
    
    def obter_configuracoes(self) -> Result[Configuracao, ErroConfiguracao]:
        """Obtém todas as configurações."""
        ...
        
    def salvar_configuracoes(self, config: Configuracao) -> Result[bool, ErroConfiguracao]:
        """Salva todas as configurações."""
        ...