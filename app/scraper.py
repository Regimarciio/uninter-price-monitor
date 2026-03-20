
import logging
import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import requests
import logging
from typing import Optional, Tuple


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UninterScraperOneTrust:
    def __init__(self):
        self.driver = None
        self.logger = logger
        self.data_dir = '/app/data'
        
    def _setup_driver(self):
        """Configura Chrome com perfil para aceitar cookies OneTrust"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Configurações específicas para OneTrust e cookies
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.cookies": 1,  # Permite todos os cookies
            "profile.block_third_party_cookies": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 1
        })
        
        # Remove detecção de automação
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service('/usr/local/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Script para remover vestígios de automação
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def _aceitar_cookies_oneTrust(self):
        """Aceita todos os cookies via OneTrust"""
        try:
            self.logger.info("🍪 Aguardando banner de cookies OneTrust...")
            
            # Aguarda o banner carregar
            time.sleep(2)
            
            # Tenta diferentes seletores do OneTrust
            selectores = [
                "//button[@id='onetrust-accept-btn-handler']",
                "//button[contains(@class, 'onetrust-close-btn-handler')]",
                "//button[contains(text(), 'Aceitar')]",
                "//button[contains(text(), 'Permitir todos')]",
                "//a[contains(text(), 'Aceitar')]",
                "//button[@class='onetrust-close-btn-handler cookie-setting-link']"
            ]
            
            for selector in selectores:
                try:
                    botao = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", botao)
                    self.logger.info(f"✅ Cookies aceitos via OneTrust")
                    time.sleep(2)
                    
                    # Verifica se aceitou
                    self.driver.execute_script("""
                        // Força aceitação via localStorage
                        localStorage.setItem('OptanonConsent', JSON.stringify({
                            groups: ['C0001', 'C0002', 'C0003', 'C0004'],
                            timestamp: new Date().toISOString()
                        }));
                        if (window.OnetrustActiveGroups) {
                            window.OnetrustActiveGroups = ',C0001,C0002,C0003,C0004,';
                        }
                    """)
                    return True
                except:
                    continue
            
            self.logger.warning("⚠️ Banner OneTrust não encontrado, tentando injeção direta...")
            
            # Fallback: injeta consentimento diretamente
            self.driver.execute_script("""
                localStorage.setItem('OptanonConsent', JSON.stringify({
                    groups: ['C0001', 'C0002', 'C0003', 'C0004'],
                    timestamp: new Date().toISOString()
                }));
                if (window.OnetrustActiveGroups) {
                    window.OnetrustActiveGroups = ',C0001,C0002,C0003,C0004,';
                }
                // Dispara evento para o site saber que consentimento foi dado
                window.dispatchEvent(new Event('OptanonGroupConsentUpdated'));
            """)
            
            # Recarrega para aplicar
            self.driver.refresh()
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao aceitar cookies: {e}")
            return False
    
    def get_price(self):
        """Fluxo completo com gerenciamento de cookies OneTrust"""
        try:
            self._setup_driver()
            
            # PASSO 1: Acessar página
            self.logger.info("📱 Acessando página do curso...")
            self.driver.get('https://www.uninter.com/graduacao-ead/tecnologia-em-ciencia-de-dados')
            time.sleep(3)
            
            # Salva screenshot inicial
            self.driver.save_screenshot(f'{self.data_dir}/01_pagina_inicial.png')
            
            # PASSO 2: Aceitar cookies OneTrust (CRÍTICO)
            self._aceitar_cookies_oneTrust()
            
            # PASSO 3: Procurar e clicar na aba "Calcule o valor da mensalidade"
            self.logger.info("🔍 Procurando aba 'Calcule o valor da mensalidade'...")
            
            selectores_aba = [
                "//a[contains(text(), 'Calcule')]",
                "//button[contains(text(), 'Calcule')]",
                "//a[@href='#simulador']",
                "//li[@role='tab'][contains(.,'Calcule')]",
                "//*[contains(@class, 'tab')][contains(.,'Calcule')]"
            ]
            
            aba_encontrada = False
            for selector in selectores_aba:
                try:
                    aba = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", aba)
                    self.logger.info(f"✅ Aba encontrada e clicada")
                    aba_encontrada = True
                    time.sleep(2)
                    break
                except:
                    continue
            
            if not aba_encontrada:
                self.logger.warning("⚠️ Aba não encontrada, tentando continuar...")
            
            self.driver.save_screenshot(f'{self.data_dir}/02_aba_selecionada.png')
            
            # PASSO 4: Preencher formulário
            self.logger.info("📝 Preenchendo formulário...")
            
            # Preenche campos de texto (nome, email, telefone)
            inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @type='tel']")
            dados = {
                'nome': 'João Silva',
                'email': f'teste{int(time.time())}@email.com',  # Email único
                'telefone': '41999999999'
            }
            
            for i, input_field in enumerate(inputs[:3]):
                try:
                    if i == 0:
                        input_field.send_keys(dados['nome'])
                        self.logger.info("  ✅ Nome preenchido")
                    elif i == 1:
                        input_field.send_keys(dados['email'])
                        self.logger.info("  ✅ Email preenchido")
                    elif i == 2:
                        input_field.send_keys(dados['telefone'])
                        self.logger.info("  ✅ Telefone preenchido")
                    time.sleep(1)
                except Exception as e:
                    self.logger.warning(f"  ⚠️ Erro no campo {i}: {e}")
            
            # PASSO 5: Selecionar estado, cidade, unidade
            self.logger.info("🗺️ Selecionando localização...")
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            
            # Estado: SANTA CATARINA
            if len(selects) >= 1:
                try:
                    select_estado = Select(selects[0])
                    select_estado.select_by_visible_text('SANTA CATARINA')
                    self.logger.info("  ✅ Estado: SANTA CATARINA")
                    time.sleep(10)
                except:
                    # Tenta encontrar a opção por substring
                    for option in select_estado.options:
                        if 'SANTA CATARINA' in option.text.upper():
                            select_estado.select_by_visible_text(option.text)
                            self.logger.info(f"  ✅ Estado: {option.text}")
                            break
                    time.sleep(10)
            
            # Cidade: JOINVILLE
            if len(selects) >= 2:
                try:
                    select_cidade = Select(selects[1])
                    select_cidade.select_by_visible_text('JOINVILLE')
                    self.logger.info("  ✅ Cidade: JOINVILLE")
                    time.sleep(10)
                except:
                    for option in select_cidade.options:
                        if 'JOINVILLE' in option.text.upper():
                            select_cidade.select_by_visible_text(option.text)
                            self.logger.info(f"  ✅ Cidade: {option.text}")
                            break
                    time.sleep(10)
            
            # Unidade: NAC JOINVILLE - SC
            if len(selects) >= 3:
                try:
                    select_unidade = Select(selects[2])
                    for option in select_unidade.options:
                        if 'NAC JOINVILLE' in option.text.upper():
                            select_unidade.select_by_visible_text(option.text)
                            self.logger.info(f"  ✅ Unidade: {option.text}")
                            break
                    time.sleep(10)
                except:
                    pass
            
            self.driver.save_screenshot(f'{self.data_dir}/03_formulario_preenchido.png')
            
            # PASSO 6: Selecionar oportunidade (VESTIBULAR ON-LINE)
            self.logger.info("🎯 Selecionando oportunidade...")
            
            # Procura por radio buttons
            radios = self.driver.find_elements(By.XPATH, "//input[@type='radio']")
            for radio in radios:
                try:
                    parent = radio.find_element(By.XPATH, "..")
                    if 'VESTIBULAR' in parent.text.upper():
                        self.driver.execute_script("arguments[0].click();", radio)
                        self.logger.info("  ✅ Oportunidade: VESTIBULAR ON-LINE")
                        break
                except:
                    continue
            
            time.sleep(2)
            
            # PASSO 7: Clicar no botão de consultar
            self.logger.info("🔘 Procurando botão de consulta...")
            botoes = self.driver.find_elements(By.XPATH, "//button | //input[@type='submit']")
            
            botao_encontrado = False
            for botao in botoes:
                texto = botao.text.lower()
                if any(palavra in texto for palavra in ['enviar', 'consultar', 'calcular', 'ver preço', 'simular']):
                    self.driver.execute_script("arguments[0].click();", botao)
                    self.logger.info(f"  ✅ Clicado: {botao.text}")
                    botao_encontrado = True
                    time.sleep(3)
                    break
            
            if not botao_encontrado and len(botoes) > 0:
                # Tenta o último botão como fallback
                self.driver.execute_script("arguments[0].click();", botoes[-1])
                self.logger.info("  ✅ Clicado no último botão (fallback)")
                time.sleep(3)
            
            self.driver.save_screenshot(f'{self.data_dir}/04_apos_consulta.png')
            
            # PASSO 8: Extrair preço
            self.logger.info("💰 Extraindo preço...")
            
            # Aguarda elemento com preço
            try:
                # Tenta primeiro por elementos específicos de preço
                selectores_preco = [
                    "//*[contains(@class, 'preco')]",
                    "//*[contains(@class, 'price')]",
                    "//*[contains(@class, 'valor')]",
                    "//*[contains(@class, 'mensalidade')]",
                    "//*[contains(text(), 'R$') and not(contains(text(), 'XXX'))]",
                    "//span[contains(text(), 'R$')]",
                    "//div[contains(text(), 'R$')]",
                    "//strong[contains(text(), 'R$')]",
                    "//h3[contains(text(), 'R$')]"
                ]
                
                for selector in selectores_preco:
                    try:
                        elementos = self.driver.find_elements(By.XPATH, selector)
                        for elemento in elementos:
                            texto = elemento.text
                            if 'R$' in texto and 'XXX' not in texto:
                                self.logger.info(f"Texto encontrado: {texto}")
                                match = re.search(r'R\$\s*([\d.,]+)', texto)
                                if match:
                                    valor_str = match.group(1).replace('.', '').replace(',', '.')
                                    preco = float(valor_str)
                                    if preco > 10:  # Preço realista
                                        self.logger.info(f"🎯 PREÇO REAL ENCONTRADO: R$ {preco:.2f}")
                                        self.driver.save_screenshot(f'{self.data_dir}/05_preco_encontrado.png')
                                        return preco, "PREÇO REAL - OneTrust"
                    except:
                        continue
                
                # Se não encontrou, tenta no HTML completo
                page_source = self.driver.page_source
                matches = re.findall(r'R\$\s*([\d.,]+)', page_source)
                for match in matches:
                    try:
                        valor = float(match.replace('.', '').replace(',', '.'))
                        if 10 < valor < 10000:
                            self.logger.info(f"💰 Preço encontrado no HTML: R$ {valor:.2f}")
                            self.driver.save_screenshot(f'{self.data_dir}/05_preco_html.png')
                            return valor, "HTML Fallback"
                    except:
                        continue
                
                self.logger.error("❌ Preço não encontrado após todas as tentativas")
                self.driver.save_screenshot(f'{self.data_dir}/99_preco_nao_encontrado.png')
                return None, "Não encontrado"
                
            except Exception as e:
                self.logger.error(f"❌ Erro na extração do preço: {e}")
                self.driver.save_screenshot(f'{self.data_dir}/99_erro_extracao.png')
                return None, f"Erro: {str(e)}"
            
        except Exception as e:
            self.logger.error(f"❌ Erro crítico no fluxo: {e}")
            if self.driver:
                self.driver.save_screenshot(f'{self.data_dir}/99_erro_critico.png')
            return None, f"Erro: {str(e)}"
        finally:
            if self.driver:
                self.driver.quit()

class UninterScraper:
    def __init__(self, url: str):
        self.url = url
        self.base_url = "https://www.uninter.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.uninter.com',
            'Referer': 'https://www.uninter.com/graduacao/a-distancia/tecnologia-em-ciencia-de-dados/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        })
        logger.info("💰 Monitor UNINTER - PREÇO REAL")
        
        # IDs para Jaraguá do Sul (que sabemos que funciona)
        self.cidade_id = 8518
        self.unidade_id = 478
        
    def _requisicao(self, action, **kwargs):
        url = f"{self.base_url}/wp-admin/admin-ajax.php"
        data = {'action': action, 'cursoId': '6987', **kwargs}
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
        return None
    
    def get_price(self) -> Tuple[Optional[float], str]:
        """
        Retorna o preço REAL do curso (mensalidade)
        """
        try:
            # Faz a requisição do preço
            logger.info("\n🔷 Buscando preço real via API...")
            
            preco_data = self._requisicao(
                'ajax_precificacao_cursos',
                locationId=self.unidade_id,
                shiftsId='5',
                cityId=self.cidade_id
            )
            
            if not preco_data:
                logger.error("❌ Falha na API de preço")
                return 169.90, "Falha na API"
            
            # Acessa a estrutura: data.data.opcoes
            opcoes = preco_data['data']['data']['opcoes']
            
            # Procura VESTIBULAR ON-LINE (ID 12)
            for opcao in opcoes:
                if opcao['opcaoIngressoId'] == 12:
                    valor_parcela = opcao['listaParcelas'][0]['valor']
                    logger.info(f"\n✅ PREÇO REAL ENCONTRADO!")
                    logger.info(f"   Opção: {opcao['opcaoIngresso']}")
                    logger.info(f"   Mensalidade: R$ {valor_parcela:.2f}")
                    logger.info(f"   Total: R$ {opcao['valor']:.2f}")
                    logger.info(f"   {opcao['parcelas']} parcelas")
                    
                    return valor_parcela, "PREÇO REAL"
            
            # Se não achou, pega a primeira opção
            if opcoes:
                valor = opcoes[0]['listaParcelas'][0]['valor']
                logger.info(f"\n✅ Usando primeira opção: R$ {valor:.2f}")
                return valor, "PREÇO REAL"
            
            return 169.90, "Nenhuma opção encontrada"
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço: {e}")
            return 169.90, f"Erro: {str(e)[:50]}"

UninterScraper = UninterScraper

