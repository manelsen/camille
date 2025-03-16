# adaptadores/adaptador_mistral.py
import base64
from typing import Dict, Any, Optional, Union
from returns.result import Result, Success, Failure
import os
import re
from PIL import Image

# Importando o SDK do Mistral
from mistralai import Mistral

from entidades import CaminhoImagem, DescricaoImagem, ErroIA, ProvedorIA
from servico_ia import ServicoIA

class AdaptadorMistral(ServicoIA):
    """Adaptador para o serviço de IA do Mistral AI com suporte a imagens locais e URLs."""
    
    provedor = ProvedorIA.MISTRAL
    
    def __init__(self, chave_api: str):
        """Inicializa o adaptador com a chave API."""
        self.chave_api = chave_api
        self.modelo = "pixtral-12b-2409"  # Modelo com suporte a visão
        self.cliente = None
        
        if self.chave_api:
            try:
                # Inicializa o cliente Mistral com a chave API
                self.cliente = Mistral(api_key=self.chave_api)
            except Exception:
                self.cliente = None
    
    def _codificar_imagem(self, caminho_imagem: str) -> Optional[str]:
        """Codifica a imagem para base64."""
        try:
            with open(caminho_imagem, "rb") as arquivo_imagem:
                return base64.b64encode(arquivo_imagem.read()).decode('utf-8')
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _eh_url_web(self, caminho: str) -> bool:
        """Verifica se o caminho é uma URL web."""
        return caminho.startswith(('http://', 'https://'))
    
    def descrever_imagem(self, caminho_imagem: CaminhoImagem) -> Result[DescricaoImagem, ErroIA]:
        """
        Descreve uma imagem usando o Mistral AI.
        Funciona com caminhos locais ou URLs da web.
        """
        if not self.chave_api or not self.cliente:
            return Failure(ErroIA('Chave API do Mistral não configurada ou cliente não inicializado'))
        
        try:
            # Verifica se é uma URL web ou um caminho local
            if self._eh_url_web(caminho_imagem):
                return self.descrever_imagem_url(caminho_imagem)
            
            # Processamento para arquivo local
            base64_imagem = self._codificar_imagem(caminho_imagem)
            if not base64_imagem:
                return Failure(ErroIA(f'Não foi possível ler ou codificar a imagem: {caminho_imagem}'))
            
            # Obtendo o tipo MIME da imagem
            mime_type = self._obter_mime_type(caminho_imagem)
            
            # Criando a mensagem para o Mistral com data URL
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Descreva detalhadamente esta imagem para uma pessoa com deficiência visual."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:{mime_type};base64,{base64_imagem}"
                        }
                    ]
                }
            ]
            
            # Enviando a requisição para a API usando o SDK
            chat_response = self.cliente.chat.complete(
                model=self.modelo,
                messages=mensagens
            )
            
            # Extraindo a resposta
            if chat_response and chat_response.choices and len(chat_response.choices) > 0:
                texto_resposta = chat_response.choices[0].message.content
                return Success(DescricaoImagem(texto_resposta))
            else:
                return Failure(ErroIA('Resposta vazia da API Mistral'))
                
        except Exception as e:
            return Failure(ErroIA(f'Erro ao descrever imagem com Mistral: {str(e)}'))
    
    def descrever_imagem_url(self, url_imagem: str) -> Result[DescricaoImagem, ErroIA]:
        """Descreve uma imagem a partir de uma URL web usando o Mistral AI."""
        if not self.chave_api or not self.cliente:
            return Failure(ErroIA('Chave API do Mistral não configurada ou cliente não inicializado'))
        
        if not self._eh_url_web(url_imagem):
            return Failure(ErroIA('URL inválida. Deve começar com http:// ou https://'))
        
        try:
            # Criando a mensagem para o Mistral com URL direta
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Descreva detalhadamente esta imagem para uma pessoa com deficiência visual."
                        },
                        {
                            "type": "image_url",
                            "image_url": url_imagem
                        }
                    ]
                }
            ]
            
            # Enviando a requisição para a API usando o SDK
            chat_response = self.cliente.chat.complete(
                model=self.modelo,
                messages=mensagens
            )
            
            # Extraindo a resposta
            if chat_response and chat_response.choices and len(chat_response.choices) > 0:
                texto_resposta = chat_response.choices[0].message.content
                return Success(DescricaoImagem(texto_resposta))
            else:
                return Failure(ErroIA('Resposta vazia da API Mistral'))
                
        except Exception as e:
            return Failure(ErroIA(f'Erro ao descrever imagem com URL usando Mistral: {str(e)}'))
    
    def descrever_imagem_bytes(self, imagem_bytes: bytes, mime_type: str) -> Result[DescricaoImagem, ErroIA]:
        """Descreve uma imagem a partir de bytes usando o Mistral AI."""
        if not self.chave_api or not self.cliente:
            return Failure(ErroIA('Chave API do Mistral não configurada ou cliente não inicializado'))
        
        try:
            # Codificando a imagem em base64
            base64_imagem = base64.b64encode(imagem_bytes).decode('utf-8')
            
            # Criando a mensagem para o Mistral
            mensagens = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Descreva detalhadamente esta imagem para uma pessoa com deficiência visual."
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:{mime_type};base64,{base64_imagem}"
                        }
                    ]
                }
            ]
            
            # Enviando a requisição para a API usando o SDK
            chat_response = self.cliente.chat.complete(
                model=self.modelo,
                messages=mensagens
            )
            
            # Extraindo a resposta
            if chat_response and chat_response.choices and len(chat_response.choices) > 0:
                texto_resposta = chat_response.choices[0].message.content
                return Success(DescricaoImagem(texto_resposta))
            else:
                return Failure(ErroIA('Resposta vazia da API Mistral'))
                
        except Exception as e:
            return Failure(ErroIA(f'Erro ao descrever imagem com Mistral: {str(e)}'))
    
    def _obter_mime_type(self, caminho_imagem: str) -> str:
        """Obtém o MIME type da imagem baseado na extensão do arquivo."""
        extensao = os.path.splitext(caminho_imagem)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_types.get(extensao, 'image/jpeg')