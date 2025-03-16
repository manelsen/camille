# portas/servico_ia.py
from abc import ABC
from typing import Protocol
from returns.result import Result

from .entidades import CaminhoImagem, DescricaoImagem, ErroIA

class ServicoIA(Protocol):
    """
    Porta que define a interface para serviços de descrição de imagem.
    Seguindo o paradigma funcional, retorna Result[DescricaoImagem, ErroIA].
    """
    def descrever_imagem(self, caminho_imagem: CaminhoImagem) -> Result[DescricaoImagem, ErroIA]:
        """Descreve uma imagem e retorna o resultado ou erro."""
        ...