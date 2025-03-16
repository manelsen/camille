import addonHandler
import sys
import os
from logHandler import log
from .interface_nvda import globalPluginHandler

# Configurar caminho das dependências
ADDON_DIR = os.path.abspath(os.path.dirname(__file__))
DEPS_PATH = os.path.join(ADDON_DIR, "..", "dependencies")
sys.path.insert(0, DEPS_PATH)

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()
        self.load_modules()

    def load_modules(self):
        try:
            from . import adaptador_gemini, adaptador_mistral, casos_uso, entidades, gerenciador_configuracao, repositorio_configuracao_nvd, servico_ia, tratador_erros
            # Inicializa ou configura os módulos conforme necessário
            # Exemplo: adaptador_gemini.iniciar()
        except Exception as e:
            log.error(f"Erro ao carregar módulos: {str(e)}")

    def terminate(self):
        super().terminate()
        # Adicione código para finalizar qualquer recurso usado pelo addon