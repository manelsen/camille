# infraestrutura/tratador_erros.py
from typing import Dict, Any, Callable
from returns.result import Result, Success, Failure
from returns.curry import curry

@curry
def tratar_erro(
    manipuladores: Dict[str, Callable[[str], Result[Any, str]]],
    erro: str
) -> Result[Any, str]:
    """
    Trata erros baseado em manipuladores registrados.
    Usa pattern matching funcional para determinar o manipulador correto.
    """
    for padrao, manipulador in manipuladores.items():
        if padrao in erro:
            return manipulador(erro)
    
    # Manipulador padrão se nenhum padrão corresponder
    return Failure(f'Erro não tratado: {erro}')

# Exemplo de uso do tratador de erros
manipuladores_erro = {
    'Imagem não encontrada': lambda erro: Failure('A imagem solicitada não pôde ser localizada.'),
    'chave API': lambda erro: Failure('Problema com a chave de API. Verifique suas configurações.'),
    'conexão': lambda erro: Failure('Erro de conexão. Verifique sua internet.'),
}

tratar_erro_padronizado = tratar_erro(manipuladores_erro)