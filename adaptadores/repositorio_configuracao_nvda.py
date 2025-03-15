# adaptadores/repositorio_configuracao_nvda.py
import os
import json
from typing import Dict, Any, Optional
from returns.result import Result, Success, Failure
from cryptography.fernet import Fernet

from ..dominio.entidades import (
    ProvedorIA, ChaveAPI, ErroConfiguracao,
    Configuracao
)
from ..portas.repositorio_configuracao import RepositorioConfiguracao

class RepositorioConfiguracaoNVDA(RepositorioConfiguracao):
    """Adaptador para armazenamento de configurações no NVDA."""
    
    def __init__(self, caminho_configuracao: str):
        self.caminho_configuracao = caminho_configuracao
        self._inicializar_criptografia()
        self._carregar_ou_criar_configuracoes()
    
    def _inicializar_criptografia(self) -> None:
        """Inicializa ou carrega a chave de criptografia."""
        caminho_chave = os.path.join(os.path.dirname(self.caminho_configuracao), 'crypto.key')
        
        if os.path.exists(caminho_chave):
            with open(caminho_chave, 'rb') as arquivo:
                self.chave_cripto = arquivo.read()
        else:
            self.chave_cripto = Fernet.generate_key()
            os.makedirs(os.path.dirname(caminho_chave), exist_ok=True)
            with open(caminho_chave, 'wb') as arquivo:
                arquivo.write(self.chave_cripto)
        
        self.cipher = Fernet(self.chave_cripto)
    
    def _carregar_ou_criar_configuracoes(self) -> None:
        """Carrega configurações existentes ou cria novas."""
        self.configuracoes_dict = {
            'chaves_api': {},
            'configuracoes': {
                'provedor_primario': ProvedorIA.GEMINI.name,
                'timeout_api': 3,
                'modo_offline': False
            }
        }
        
        if os.path.exists(self.caminho_configuracao):
            try:
                with open(self.caminho_configuracao, 'r', encoding='utf-8') as arquivo:
                    self.configuracoes_dict = json.load(arquivo)
            except Exception:
                self._salvar_configuracoes_dict()
        else:
            self._salvar_configuracoes_dict()
    
    def _salvar_configuracoes_dict(self) -> Result[bool, ErroConfiguracao]:
        """Salva as configurações no arquivo."""
        try:
            os.makedirs(os.path.dirname(self.caminho_configuracao), exist_ok=True)
            with open(self.caminho_configuracao, 'w', encoding='utf-8') as arquivo:
                json.dump(self.configuracoes_dict, arquivo, indent=2)
            return Success(True)
        except Exception as e:
            return Failure(ErroConfiguracao(f'Erro ao salvar configurações: {str(e)}'))
    
    def salvar_chave_api(self, provedor: ProvedorIA, chave: ChaveAPI) -> Result[bool, ErroConfiguracao]:
        """Salva a chave de API de forma criptografada."""
        try:
            chave_criptografada = self.cipher.encrypt(chave.encode()).decode('utf-8')
            self.configuracoes_dict['chaves_api'][provedor.name] = chave_criptografada
            return self._salvar_configuracoes_dict()
        except Exception as e:
            return Failure(ErroConfiguracao(f'Erro ao criptografar chave: {str(e)}'))
    
    def obter_chave_api(self, provedor: ProvedorIA) -> Result[ChaveAPI, ErroConfiguracao]:
        """Recupera e descriptografa a chave de API."""
        try:
            provedor_str = provedor.name
            if provedor_str not in self.configuracoes_dict['chaves_api']:
                return Failure(ErroConfiguracao(f'Chave API para {provedor_str} não encontrada'))
            
            chave_criptografada = self.configuracoes_dict['chaves_api'][provedor_str]
            chave_descriptografada = self.cipher.decrypt(chave_criptografada.encode()).decode('utf-8')
            return Success(ChaveAPI(chave_descriptografada))
        except Exception as e:
            return Failure(ErroConfiguracao(f'Erro ao descriptografar chave: {str(e)}'))
    
    def obter_configuracoes(self) -> Result[Configuracao, ErroConfiguracao]:
        """Obtém todas as configurações."""
        try:
            config_dict = self.configuracoes_dict['configuracoes']
            chaves_api = {}
            
            # Converter strings de enum para valores de enum
            provedor_primario = ProvedorIA[config_dict['provedor_primario']]
            
            # Inicializar todas as chaves como None
            for provedor in ProvedorIA:
                chaves_api[provedor] = None
            
            # Carregar chaves existentes
            for provedor_str, chave_criptografada in self.configuracoes_dict['chaves_api'].items():
                try:
                    provedor = ProvedorIA[provedor_str]
                    chave_descriptografada = self.cipher.decrypt(chave_criptografada.encode()).decode('utf-8')
                    chaves_api[provedor] = chave_descriptografada
                except Exception:
                    # Ignorar chaves que não podem ser descriptografadas
                    pass
            
            return Success(Configuracao(
                provedor_primario=provedor_primario,
                timeout_api=config_dict['timeout_api'],
                modo_offline=config_dict['modo_offline'],
                chaves_api=chaves_api
            ))
        except Exception as e:
            return Failure(ErroConfiguracao(f'Erro ao obter configurações: {str(e)}'))
    
    def salvar_configuracoes(self, config: Configuracao) -> Result[bool, ErroConfiguracao]:
        """Salva todas as configurações."""
        try:
            # Atualizar configurações gerais
            self.configuracoes_dict['configuracoes'] = {
                'provedor_primario': config.provedor_primario.name,
                'timeout_api': config.timeout_api,
                'modo_offline': config.modo_offline
            }
            
            # Atualizar chaves API (apenas as que não são None)
            for provedor, chave in config.chaves_api.items():
                if chave is not None:
                    resultado = self.salvar_chave_api(provedor, ChaveAPI(chave))
                    if resultado.is_failure():
                        return resultado
            
            return self._salvar_configuracoes_dict()
        except Exception as e:
            return Failure(ErroConfiguracao(f'Erro ao salvar configurações: {str(e)}'))