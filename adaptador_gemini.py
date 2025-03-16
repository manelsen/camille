# adaptadores/adaptador_gemini.py
from typing import Dict, Any, Optional
from returns.result import Result, Success, Failure
import os
from PIL import Image
from google import genai
from google.genai.types import Part

from entidades import CaminhoImagem, DescricaoImagem, ErroIA, ProvedorIA
from servico_ia import ServicoIA

class AdaptadorGemini(ServicoIA):
    """Adaptador para o serviço de IA do Google Gemini utilizando o SDK oficial."""
    
    provedor = ProvedorIA.GEMINI
    
    def __init__(self, chave_api: str):
        """Inicializa o adaptador com a chave API."""
        self.chave_api = chave_api
        self.modelo = "gemini-2.0-flash"
        self.cliente = None
        
        if self.chave_api:
            try:
                # Inicializa o cliente Gemini com a chave API
                self.cliente = genai.Client(api_key=self.chave_api)
            except Exception:
                self.cliente = None
    
    def descrever_imagem(self, caminho_imagem: CaminhoImagem) -> Result[DescricaoImagem, ErroIA]:
        """Descreve uma imagem usando o Google Gemini."""
        if not self.chave_api or not self.cliente:
            return Failure(ErroIA('Chave API do Gemini não configurada ou cliente não inicializado'))
        
        try:
            # Carregando a imagem usando PIL
            imagem = Image.open(caminho_imagem)
            
            # Construindo o prompt para descrição detalhada
            prompt = "Descreva detalhadamente esta imagem para uma pessoa com deficiência visual."
            
            # Enviando a requisição para a API usando o SDK
            response = self.cliente.models.generate_content(
                model=self.modelo,
                contents=[prompt, imagem]
            )
            
            # Verificando a resposta
            if response.text:
                return Success(DescricaoImagem(response.text))
            else:
                return Failure(ErroIA('Resposta vazia da API Gemini'))
                
        except Exception as e:
            return Failure(ErroIA(f'Erro ao descrever imagem com Gemini: {str(e)}'))
    
    def descrever_imagem_bytes(self, imagem_bytes: bytes, mime_type: str) -> Result[DescricaoImagem, ErroIA]:
        """Descreve uma imagem a partir de bytes usando o Google Gemini."""
        if not self.chave_api or not self.cliente:
            return Failure(ErroIA('Chave API do Gemini não configurada ou cliente não inicializado'))
        
        try:
            # Construindo o prompt para descrição detalhada
            prompt = "Descreva detalhadamente esta imagem para uma pessoa com deficiência visual."
            
            # Criando a parte para a imagem em bytes
            imagem_part = Part.from_bytes(data=imagem_bytes, mime_type=mime_type)
            
            # Enviando a requisição para a API usando o SDK
            response = self.cliente.models.generate_content(
                model=self.modelo,
                contents=[prompt, imagem_part]
            )
            
            # Verificando a resposta
            if response.text:
                return Success(DescricaoImagem(response.text))
            else:
                return Failure(ErroIA('Resposta vazia da API Gemini'))
                
        except Exception as e:
            return Failure(ErroIA(f'Erro ao descrever imagem com Gemini: {str(e)}'))