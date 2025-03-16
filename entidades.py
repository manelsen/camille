# dominio/entidades.py
from dataclasses import dataclass
from typing import Optional, NewType, Dict, Any
from enum import Enum, auto

# Tipos de domínio
CaminhoImagem = NewType('CaminhoImagem', str)
DescricaoImagem = NewType('DescricaoImagem', str)
ChaveAPI = NewType('ChaveAPI', str)
ErroIA = NewType('ErroIA', str)
ErroConfiguracao = NewType('ErroConfiguracao', str)

class ProvedorIA(Enum):
    """Enumera os provedores de IA disponíveis."""
    GEMINI = auto()
    MISTRAL = auto()

@dataclass(frozen=True)
class Imagem:
    """Entidade imutável que representa uma imagem."""
    caminho: str
    tipo: str
    largura: Optional[int] = None
    altura: Optional[int] = None

@dataclass(frozen=True)
class Descricao:
    """Entidade imutável que representa uma descrição de imagem."""
    texto: str
    provedor: ProvedorIA
    confianca: float = 1.0

@dataclass(frozen=True)
class Configuracao:
    """Entidade imutável que representa configurações do addon."""
    provedor_primario: ProvedorIA
    timeout_api: int
    modo_offline: bool
    chaves_api: Dict[ProvedorIA, Optional[str]]
    
    def com_chave_alterada(self, provedor: ProvedorIA, chave: str) -> 'Configuracao':
        """Retorna uma nova configuração com a chave API alterada."""
        novas_chaves = dict(self.chaves_api)
        novas_chaves[provedor] = chave
        return Configuracao(
            provedor_primario=self.provedor_primario,
            timeout_api=self.timeout_api,
            modo_offline=self.modo_offline,
            chaves_api=novas_chaves
        )