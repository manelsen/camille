# dominio/casos_uso.py
from typing import Callable, List
from functools import partial
from returns.result import Result, Success, Failure
from returns.pipeline import pipe
from returns.curry import curry
from returns.pointfree import bind, map_

from servico_ia import ServicoIA
from entidades import (
    Imagem, Descricao, ProvedorIA, CaminhoImagem,
    DescricaoImagem, ErroIA
)

@curry
def validar_imagem(caminho: str) -> Result[Imagem, str]:
    """Valida se a imagem existe e está acessível."""
    from pathlib import Path
    
    if not caminho:
        return Failure('Caminho de imagem vazio')
    
    path = Path(caminho)
    if not path.exists():
        return Failure(f'Imagem não encontrada: {caminho}')
    
    # Extensões de imagem suportadas
    extensoes_validas = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    if not path.suffix.lower() in extensoes_validas:
        return Failure(f'Formato de imagem não suportado: {path.suffix}')
    
    return Success(Imagem(
        caminho=caminho,
        tipo=path.suffix.lower()[1:],  # Remove o ponto da extensão
    ))

@curry
def descrever_com_servico(
    servico_ia: ServicoIA,
    imagem: Imagem
) -> Result[Descricao, str]:
    """Obtém descrição da imagem usando o serviço especificado."""
    return servico_ia.descrever_imagem(CaminhoImagem(imagem.caminho)).map(
        lambda descricao: Descricao(
            texto=descricao,
            provedor=getattr(servico_ia, 'provedor', ProvedorIA.OCR)
        )
    )

@curry
def tentar_servicos_alternativos(
    servicos: List[ServicoIA],
    erro: str,
    imagem: Imagem
) -> Result[Descricao, str]:
    """Tenta serviços alternativos em caso de falha no serviço primário."""
    if not servicos:
        return Failure(f'Todos os serviços falharam. Último erro: {erro}')
    
    # Tenta o próximo serviço na lista
    servico = servicos[0]
    return descrever_com_servico(servico, imagem).lash(
        lambda novo_erro: tentar_servicos_alternativos(
            servicos[1:], 
            novo_erro, 
            imagem
        )
    )

@curry
def gerar_descricao_imagem(
    servico_primario: ServicoIA,
    servicos_alternativos: List[ServicoIA],
    caminho_imagem: str
) -> Result[Descricao, str]:
    """Caso de uso: gera descrição para uma imagem com fallback."""
    pipeline = pipe(
        validar_imagem,
        bind(descrever_com_servico(servico_primario)),
        lambda result: result.lash(
            lambda erro: tentar_servicos_alternativos(
                servicos_alternativos, 
                erro, 
                result.unwrap() if result.is_success() else Imagem(caminho_imagem, "")
            )
        )
    )
    
    return pipeline(caminho_imagem)