# interface_nvda.py
import os
import globalPluginHandler
import addonHandler
import gui
import wx
from typing import Dict, List, Any, Optional
import globalVars
import ui
import api
import controlTypes
import scriptHandler
import config

from returns.result import Result, Success, Failure

from casos_uso import gerar_descricao_imagem
from entidades import Configuracao, ProvedorIA
from servico_ia import ServicoIA
from adaptador_gemini import AdaptadorGemini
from adaptador_mistral import AdaptadorMistral
from adaptador_ocr import AdaptadorOCR
from repositorio_configuracao_nvda import RepositorioConfiguracaoNVDA
from gerenciador_configuracao import (
    obter_configuracao, obter_chave_api_para_provedor,
    salvar_configuracao
)

addonHandler.initTranslation()

class ConfiguracaoDialog(wx.Dialog):
    """Diálogo de configuração para o complemento."""
    
    def __init__(self, parent, configuracao_atual, on_salvar):
        super(ConfiguracaoDialog, self).__init__(parent, title=_("Configurações de Descrição de Imagem por IA"))
        self.configuracao_atual = configuracao_atual
        self.on_salvar = on_salvar
        
        # Criar layout
        painel_principal = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Provedor primário
        sizer_provedor = wx.BoxSizer(wx.HORIZONTAL)
        self.label_provedor = wx.StaticText(painel_principal, label=_("Provedor de IA:"))
        sizer_provedor.Add(self.label_provedor, 0, wx.ALL, 5)
        
        self.choice_provedor = wx.Choice(painel_principal, choices=[p.name for p in ProvedorIA])
        for idx, p in enumerate(ProvedorIA):
            if p == configuracao_atual.provedor_primario:
                self.choice_provedor.SetSelection(idx)
                break
        sizer_provedor.Add(self.choice_provedor, 0, wx.ALL, 5)
        sizer.Add(sizer_provedor, 0, wx.EXPAND, 5)
        
        # Chave API Gemini
        sizer_chave_gemini = wx.BoxSizer(wx.HORIZONTAL)
        self.label_chave_gemini = wx.StaticText(painel_principal, label=_("Chave API Gemini:"))
        sizer_chave_gemini.Add(self.label_chave_gemini, 0, wx.ALL, 5)
        
        self.text_chave_gemini = wx.TextCtrl(painel_principal, 
                                            value=configuracao_atual.chaves_api.get(ProvedorIA.GEMINI, "") or "",
                                            style=wx.TE_PASSWORD)
        sizer_chave_gemini.Add(self.text_chave_gemini, 1, wx.ALL, 5)
        sizer.Add(sizer_chave_gemini, 0, wx.EXPAND, 5)
        
        # Chave API Mistral
        sizer_chave_mistral = wx.BoxSizer(wx.HORIZONTAL)
        self.label_chave_mistral = wx.StaticText(painel_principal, label=_("Chave API Mistral:"))
        sizer_chave_mistral.Add(self.label_chave_mistral, 0, wx.ALL, 5)
        
        self.text_chave_mistral = wx.TextCtrl(painel_principal, 
                                            value=configuracao_atual.chaves_api.get(ProvedorIA.MISTRAL, "") or "",
                                            style=wx.TE_PASSWORD)
        sizer_chave_mistral.Add(self.text_chave_mistral, 1, wx.ALL, 5)
        sizer.Add(sizer_chave_mistral, 0, wx.EXPAND, 5)
        
        # Timeout API
        sizer_timeout = wx.BoxSizer(wx.HORIZONTAL)
        self.label_timeout = wx.StaticText(painel_principal, label=_("Timeout API (segundos):"))
        sizer_timeout.Add(self.label_timeout, 0, wx.ALL, 5)
        
        self.spin_timeout = wx.SpinCtrl(painel_principal, min=1, max=30, initial=configuracao_atual.timeout_api)
        sizer_timeout.Add(self.spin_timeout, 0, wx.ALL, 5)
        sizer.Add(sizer_timeout, 0, wx.EXPAND, 5)
        
        # Modo offline
        self.check_modo_offline = wx.CheckBox(painel_principal, label=_("Modo offline"))
        self.check_modo_offline.SetValue(configuracao_atual.modo_offline)
        sizer.Add(self.check_modo_offline, 0, wx.ALL, 5)
        
        # Botões
        sizer_botoes = wx.StdDialogButtonSizer()
        self.btn_ok = wx.Button(painel_principal, wx.ID_OK)
        self.btn_cancel = wx.Button(painel_principal, wx.ID_CANCEL)
        sizer_botoes.AddButton(self.btn_ok)
        sizer_botoes.AddButton(self.btn_cancel)
        sizer_botoes.Realize()
        sizer.Add(sizer_botoes, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        painel_principal.SetSizer(sizer)
        sizer.Fit(self)
        
        # Eventos
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        
    def on_ok(self, event):
        """Salva as configurações e fecha o diálogo."""
        # Obtém valores da interface
        indice_provedor = self.choice_provedor.GetSelection()
        provedores = [p for p in ProvedorIA]
        provedor_primario = provedores[indice_provedor]
        
        chave_gemini = self.text_chave_gemini.GetValue()
        chave_mistral = self.text_chave_mistral.GetValue()
        timeout_api = self.spin_timeout.GetValue()
        modo_offline = self.check_modo_offline.GetValue()
        
        # Atualiza chaves de API
        chaves_api = dict(self.configuracao_atual.chaves_api)
        chaves_api[ProvedorIA.GEMINI] = chave_gemini if chave_gemini else None
        chaves_api[ProvedorIA.MISTRAL] = chave_mistral if chave_mistral else None
        
        # Cria nova configuração
        nova_configuracao = Configuracao(
            provedor_primario=provedor_primario,
            timeout_api=timeout_api,
            modo_offline=modo_offline,
            chaves_api=chaves_api
        )
        
        # Chama o callback de salvar
        self.on_salvar(nova_configuracao)
        
        # Fecha o diálogo
        self.EndModal(wx.ID_OK)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """Plugin global NVDA para descrição de imagens por IA."""
    
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        
        # Inicializa o repositório de configuração
        caminho_config = os.path.join(globalVars.appArgs.configPath, 'addons', 'Camille', 'config.json')
        self.repositorio = RepositorioConfiguracaoNVDA(caminho_config)
        
        # Inicializa adaptadores
        self.adaptadores: Dict[ProvedorIA, Optional[ServicoIA]] = {
            ProvedorIA.GEMINI: None,
            ProvedorIA.MISTRAL: None
        }
        
        # Carrega configurações e inicializa serviços
        self._inicializar_servicos()
        
        # Adiciona item de menu
        self._criar_menu()
    
    def _inicializar_servicos(self) -> None:
        """Inicializa os serviços de IA com base nas configurações."""
        resultado_config = obter_configuracao(self.repositorio)
        if isinstance(resultado_config, Success):
            self.configuracao = resultado_config.unwrap()
            
            # Se não estiver no modo offline, inicializa os serviços
            if not self.configuracao.modo_offline:
                self._inicializar_servico(ProvedorIA.GEMINI)
                self._inicializar_servico(ProvedorIA.MISTRAL)
        else:
            # Fallback para configuração padrão em caso de erro
            self.configuracao = Configuracao(
                provedor_primario=ProvedorIA.GEMINI,
                timeout_api=3,
                modo_offline=False,
                usar_fallback_ocr=True,
                chaves_api={}
            )
    
    def _inicializar_servico(self, provedor: ProvedorIA) -> None:
        """Inicializa um serviço de IA específico."""
        resultado_chave = obter_chave_api_para_provedor(self.repositorio, provedor)
        
        if isinstance(resultado_chave, Success):
            chave_api = resultado_chave.unwrap()
            
            if provedor == ProvedorIA.GEMINI:
                self.adaptadores[provedor] = AdaptadorGemini(chave_api)
            elif provedor == ProvedorIA.MISTRAL:
                self.adaptadores[provedor] = AdaptadorMistral(chave_api)
    
def _criar_menu(self) -> None:
    """Cria o item de menu para as configurações do plugin."""
    try:
        self.menu = gui.mainFrame.sysTrayIcon.preferencesMenu
        self.item_menu = self.menu.Append(
            wx.ID_ANY, 
            _("&Descrição de Imagem por IA..."),
            _("Configurar o complemento de descrição de imagem por IA")
        )
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.on_exibir_configuracoes, self.item_menu)
        print("Menu de configurações criado com sucesso.")
    except Exception as e:
        print(f"Erro ao criar menu: {e}")
    
    def on_exibir_configuracoes(self, evt) -> None:
        """Exibe o diálogo de configurações."""
        dialog = ConfiguracaoDialog(
            gui.mainFrame, 
            self.configuracao, 
            self.on_salvar_configuracoes
        )
        gui.mainFrame.prePopup()
        dialog.ShowModal()
        gui.mainFrame.postPopup()
    
    def on_salvar_configuracoes(self, nova_configuracao: Configuracao) -> None:
        """Salva a nova configuração e reinicializa os serviços."""
        resultado = salvar_configuracao(self.repositorio, nova_configuracao)
        
        if isinstance(resultado, Success):
            # Atualiza a configuração local
            self.configuracao = nova_configuracao
            
            # Reinicializa os serviços
            if not nova_configuracao.modo_offline:
                self._inicializar_servico(ProvedorIA.GEMINI)
                self._inicializar_servico(ProvedorIA.MISTRAL)
            
            ui.message(_("Configurações salvas com sucesso."))
        else:
            ui.message(_("Erro ao salvar configurações: {0}").format(resultado.failure()))
    
    @scriptHandler.script(
        description=_("Descreve a imagem em foco usando IA"),
        gesture="kb:NVDA+alt+d"
    )
    def script_descrever_imagem(self, gesture) -> None:
        """Manipulador de comando para descrever a imagem em foco."""
        obj = api.getFocusObject()
        
        # Verifica se o objeto é uma imagem
        if (
            controlTypes.State.GRAPHIC in obj.states or
            obj.role == controlTypes.Role.GRAPHIC
        ):
            # Aqui você obteria o caminho/URL da imagem do objeto NVDA
            # Isso é um placeholder - a implementação real dependeria da API do NVDA
            caminho_imagem = self._obter_caminho_imagem(obj)
            
            if not caminho_imagem:
                ui.message(_("Não foi possível encontrar a imagem para descrever"))
                return
            
            # Obtém os serviços disponíveis
            servicos = self._obter_servicos_disponiveis()
            if not servicos:
                ui.message(_("Nenhum serviço de descrição disponível"))
                return
            
            servico_primario = servicos[0]
            servicos_alternativos = servicos[1:] if len(servicos) > 1 else []
            
            # Informa que está processando
            ui.message(_("Processando imagem, aguarde..."))
            
            # Gera a descrição
            resultado = gerar_descricao_imagem(
                servico_primario,
                servicos_alternativos,
                caminho_imagem
            )
            
            # Processa o resultado
            if isinstance(resultado, Success):
                descricao = resultado.unwrap()
                ui.message(descricao.texto)
            else:
                ui.message(_("Erro ao descrever imagem: ") + resultado.failure())
        else:
            ui.message(_("Não há imagem em foco"))
    
    def _obter_caminho_imagem(self, obj) -> Optional[str]:
        """
        Obtém o caminho da imagem do objeto NVDA.
        Esta é uma implementação de placeholder - a real dependeria 
        de como o NVDA expõe caminhos de imagem.
        """
        # Placeholder - isso precisaria ser implementado de acordo com a API do NVDA
        # Por exemplo, poderia usar obj.src ou obj.value ou outra propriedade
        # dependendo do tipo de controle
        
        # Para fins de demonstração, vamos considerar alguns atributos comuns
        if hasattr(obj, 'src'):
            return obj.src
        elif hasattr(obj, 'value') and obj.value.startswith(('http', 'file')):
            return obj.value
        elif hasattr(obj, 'IAccessibleObject'):
            try:
                # Tenta obter uma propriedade MSAA que pode conter o caminho da imagem
                value = obj.IAccessibleObject.accValue(0)
                if value and (value.startswith(('http', 'file', 'C:', '/', '\\'))):
                    return value
            except:
                pass
        
        # Para fins de teste, podemos retornar um caminho para uma imagem local
        # Em uma implementação real, isso seria removido
        return None
    
    def _obter_servicos_disponiveis(self) -> List[ServicoIA]:
        """Obtém a lista de serviços disponíveis de acordo com a configuração."""
        servicos: List[ServicoIA] = []
        
        # Se não estiver no modo offline e o serviço primário estiver configurado
        if not self.configuracao.modo_offline:
            servico_primario = self.adaptadores.get(self.configuracao.provedor_primario)
            if servico_primario:
                servicos.append(servico_primario)
            
            # Adiciona outros serviços configurados, exceto o primário
            for provedor, servico in self.adaptadores.items():
                if (
                    provedor != self.configuracao.provedor_primario and 
                    servico is not None
                ):
                    servicos.append(servico)
        
        return servicos
    
    def terminate(self):
        """Finaliza o plugin."""
        super(GlobalPlugin, self).terminate()
        # Remove o item de menu
        try:
            self.menu.Remove(self.item_menu)
        except Exception:
            pass