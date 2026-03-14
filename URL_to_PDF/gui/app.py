from utils import load_config, safe_filename, save_config
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import json
import subprocess
import tempfile
import sys
from urllib.parse import urlparse
import os
from datetime import datetime
import base64
from engine.converter import convert_url


class URLToPDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de URL para PDF")
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        
        # Carrega configurações
        self.config = load_config()
        
        # Verifica se playwright está instalado
        self.playwright_ready = self.check_playwright()
        
        # Setup UI
        self.setup_ui()



    #verifica o playwright para habilitar ou não a função de conversão, caso não esteja instalado, exibe o botão para instalação
    def check_playwright(self):
        
        try:
            import playwright
            return True
        except ImportError:
            return False
            
    def setup_ui(self):
        #Interface com abas
        
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(expand=True)
        
        ctk.CTkLabel(
            title_frame, 
            text="🌐→📄", 
            font=("Arial", 40)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            title_frame, 
            text="Conversor URL para PDF", 
            font=("Arial", 24, "bold")
        ).pack(side="left")
        
        # ========== STATUS INSTALAÇÃO ==========
        if not self.playwright_ready:
            install_frame = ctk.CTkFrame(self.root, fg_color="#2c3e50", height=40)
            install_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            ctk.CTkLabel(
                install_frame,
                text="📦 Playwright não encontrado. Clique para instalar componentes necessários.",
                font=("Arial", 12),
                text_color="#f1c40f"
            ).pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(
                install_frame,
                text="Instalar Agora",
                command=self.instalar_playwright,
                width=120,
                height=30,
                fg_color="#3498db",
                hover_color="#2980b9"
            ).pack(side="right", padx=10)
        
        # ========== TABVIEW ==========
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Aba 1: Conversão
        self.tab_converter = self.tabview.add("🚀 Converter")
        self.setup_converter_tab()
        
        # Aba 2: Configurações
        self.tab_config = self.tabview.add("⚙️ Configurações")
        self.setup_config_tab()
        
        # Status inicial
        self.atualizar_status_inicial()
        
    def atualizar_status_inicial(self):
       # Atualiza status baseado na instalação
        if self.playwright_ready:
            self.stats_label.configure(text="✅ Pronto para converter!")
            self.btn_converter.configure(state="normal")
        else:
            self.stats_label.configure(text="⚠️ Instale o Playwright primeiro")
            self.btn_converter.configure(state="disabled")

            
    #função que recebe a lista de urls e chama a função de conversão para cada uma delas, atualizando o status a cada conversão
    def converter_lista(self, urls):
       # Converte lista de URLs com feedback silencioso
        total = len(urls)
        
        # Inicializa contador do lote
        self.batch_counter = {
            'total': total,
            'success': 0,
            'failed': 0
        }
        
        # Configura status inicial
        self.stats_label.configure(
            text=f"✅ {self.batch_counter['success']} sucessos | ❌ {self.batch_counter['failed']} falhas"
        )
        self.progress_bar.set(0)
        
        for i, url in enumerate(urls):
            # Atualiza status
            self.root.after(
                0,
                lambda current=i+1, u=url:
                self.stats_label.configure(
                    text=f"📄 [{current}/{total}] {u[:50]}...",
                    text_color="#f39c12"
                )
            )
            
            # Atualiza progresso
            self.root.after(0, lambda p=(i/total): self.progress_bar.set(p))
            
            # Cria config temporária
            temp_config = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False
            )
            json.dump(self.config, temp_config)
            temp_config.close()
            
            # Converte (agora o processar_pdf vai incrementar o contador)
            self.converter_em_processo(url, temp_config.name)
        
        # Progresso final
        self.root.after(0, lambda: self.progress_bar.set(1.0))
    #função pra carregar a lista das urls

    def carregar_lista_urls(self):

        arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo de URLs",
            filetypes=[("Arquivo de texto", "*.txt")]
        )

        if not arquivo:
            return

        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                urls = [linha.strip() for linha in f if linha.strip()]

            if not urls:
                messagebox.showwarning("Aviso", "Arquivo vazio")
                return

            confirmar = messagebox.askyesno(
                "Confirmar",
                f"{len(urls)} URLs encontradas.\nDeseja converter todas?"
            )

            if confirmar:
                thread = threading.Thread(
                    target=self.converter_lista,
                    args=(urls,)
                )
                thread.daemon = True
                thread.start()

        except Exception as e:
            messagebox.showerror("Erro", str(e))
        


    #aba principal de conversão
    def setup_converter_tab(self):
        
        
        # URL Input
        url_frame = ctk.CTkFrame(self.tab_converter, fg_color="transparent")
        url_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(
            url_frame, 
            text="📌 URL da página:", 
            font=("Arial", 14)
        ).pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://exemplo.com",
            height=45,
            font=("Arial", 12)
        )
        self.url_entry.pack(fill="x", pady=(5, 0))
        self.url_entry.insert(0, "https://")
        self.url_entry.bind('<Return>', lambda e: self.iniciar_conversao())
        
        # Botão converter
        self.btn_converter = ctk.CTkButton(
            self.tab_converter,
            text="⚡ Converter para PDF",
            command=self.iniciar_conversao,
            height=50,
            font=("Arial", 16, "bold"),
            state="normal" if self.playwright_ready else "disabled",
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.btn_converter.pack(pady=20, padx=20, fill="x")
        self.btn_batch = ctk.CTkButton(
            self.tab_converter,
            text="📂 Converter lista (.txt)",
            command=self.carregar_lista_urls,
            height=40
        )
        self.btn_batch.pack(pady=(0, 20), padx=20, fill="x")
        
        # STATUS E PROGRESSO
        status_frame = ctk.CTkFrame(self.tab_converter)
        status_frame.pack(fill="x", pady=10, padx=20)
        
        self.stats_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 11),
            text_color="#7f8c8d"
        )
        self.stats_label.pack(pady=(0, 5))
        self.stats_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(status_frame, width=600, height=15)
        self.progress_bar.pack(pady=(5, 10))
        self.progress_bar.set(0)
        
        # PREVIEW DAS CONFIGURAÇÕES
        preview_frame = ctk.CTkFrame(self.tab_converter)
        preview_frame.pack(fill="both", expand=True, pady=10, padx=20)
        
        ctk.CTkLabel(
            preview_frame,
            text="📋 Configurações atuais:",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Scrollable frame para o preview
        self.preview_scroll = ctk.CTkScrollableFrame(preview_frame, height=100)
        self.preview_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.config_preview = ctk.CTkLabel(
            self.preview_scroll,
            text=self.get_config_text(),
            font=("Arial", 11),
            justify="left",
            anchor="w",
            wraplength=600
        )
        self.config_preview.pack(anchor="w", fill="x", padx=5, pady=5)
        
    def setup_config_tab(self):
        #Aba de configurações
        
        self.config_scroll = ctk.CTkScrollableFrame(self.tab_config)
        self.config_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ========== SEÇÃO 1: APARÊNCIA ==========
        self._criar_secao_config("📱 APARÊNCIA")
        self._criar_switch_config("🎨 Remover cores de fundo", 'remove_bg')
        
        # ========== SEÇÃO 2: CONTEÚDO ==========
        self._criar_secao_config("📄 CONTEÚDO")
        self._criar_switch_config("🖼️ Incluir logo", 'include_logo')
        self._criar_switch_config("📝 Mostrar fonte da URL", 'show_source')
        
        # ========== SEÇÃO 3: LINKS ==========
        self._criar_secao_config("🔗 LINKS")
        ctk.CTkLabel(
            self.config_scroll,
            text="Nota: Links do índice sempre ativos para navegação",
            font=("Arial", 11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        self._criar_switch_config("🔌 Desativar links do conteúdo", 'disable_links')
        self._criar_switch_config("📏 Sublinhar links", 'underline_links')
        
        # ========== SEÇÃO 4: ROLAGEM ==========
        self._criar_secao_config("🔄 ROLAGEM DA PÁGINA")
        
        scroll_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        scroll_frame.pack(fill="x", pady=5)
        
        self.scroll_pages = ctk.CTkSwitch(
            scroll_frame,
            text="📜 Scroll automático (carrega conteúdo lazy)",
            command=self.on_config_change,
            onvalue=True,
            offvalue=False
        )
        self.scroll_pages.pack(side="left")
        if self.config.get('scroll_pages'):
            self.scroll_pages.select()
            
        delay_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        delay_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(delay_frame, text="  ⏱️ Delay entre scrolls (ms):", anchor="w").pack(side="left", padx=(20, 10))
        self.scroll_delay = ctk.CTkComboBox(
            delay_frame,
            values=["200", "500", "1000", "2000"],
            width=100,
            command=lambda choice: self.on_config_change()
        )
        self.scroll_delay.pack(side="left")
        self.scroll_delay.set(str(self.config.get('scroll_delay', 500)))
        
        # ========== SEÇÃO 5: ÍNDICE ==========
        self._criar_secao_config("📑 ÍNDICE")
        
        index_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        index_frame.pack(fill="x", pady=5)
        
        self.add_index = ctk.CTkSwitch(
            index_frame,
            text="📇 Adicionar índice automático",
            command=self.on_config_change,
            onvalue=True,
            offvalue=False
        )
        self.add_index.pack(side="left")
        if self.config.get('add_index'):
            self.add_index.select()
            
        self.depth_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        
        ctk.CTkLabel(self.depth_frame, text="  📊 Profundidade:", anchor="w").pack(side="left", padx=(20, 10))
        self.index_depth = ctk.CTkComboBox(
            self.depth_frame,
            values=["Apenas H1", "H1 e H2", "H1, H2 e H3", "Todos (H1-H6)"],
            width=200,
            command=lambda choice: self.on_config_change()
        )
        self.index_depth.pack(side="left")
        self.index_depth.set(self.config.get('index_depth_text', 'H1 e H2'))
        
        self.pos_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        
        ctk.CTkLabel(self.pos_frame, text="  📌 Posição:", anchor="w").pack(side="left", padx=(20, 10))
        self.index_position = ctk.CTkComboBox(
            self.pos_frame,
            values=["Início do documento", "Final do documento"],
            width=200,
            command=lambda choice: self.on_config_change()
        )
        self.index_position.pack(side="left")
        self.index_position.set(self.config.get('index_position', 'Início do documento'))
        
        if self.config.get('add_index'):
            self.depth_frame.pack(fill="x", pady=5)
            self.pos_frame.pack(fill="x", pady=5)
        
        # ========== SEÇÃO 6: SALVAMENTO ==========
        self._criar_secao_config("💾 SALVAMENTO")
        
        auto_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        auto_frame.pack(fill="x", pady=5)
        
        self.auto_save = ctk.CTkSwitch(
            auto_frame,
            text="💾 Salvar automaticamente",
            command=self.on_config_change,
            onvalue=True,
            offvalue=False
        )
        self.auto_save.pack(side="left")
        if self.config.get('auto_save'):
            self.auto_save.select()
            
        self.folder_frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        
        folder_row = ctk.CTkFrame(self.folder_frame, fg_color="transparent")
        folder_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(folder_row, text="  📁 Pasta:", anchor="w").pack(side="left", padx=(20, 10))
        
        self.folder_path = ctk.CTkEntry(
            folder_row, 
            placeholder_text="Selecione uma pasta...",
            width=300
        )
        self.folder_path.pack(side="left", padx=(0, 5))
        self.folder_path.insert(0, self.config.get('save_folder', ''))
        
        ctk.CTkButton(
            folder_row,
            text="📂",
            width=40,
            command=self.select_folder
        ).pack(side="left")
        
        if self.config.get('auto_save'):
            self.folder_frame.pack(fill="x", pady=5)
            
    def _criar_secao_config(self, titulo):
       # Cria cabeçalho de seção
        frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        frame.pack(fill="x", pady=(20, 10))
        
        ctk.CTkLabel(
            frame, 
            text=titulo, 
            font=("Arial", 16, "bold"),
            text_color="#3a7ebf"
        ).pack(anchor="w")
        
        linha = ctk.CTkFrame(frame, height=2, fg_color="#3a7ebf")
        linha.pack(fill="x", pady=(5, 5))
        
    def _criar_switch_config(self, texto, config_key):
       # Cria um switch de configuração
        frame = ctk.CTkFrame(self.config_scroll, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        switch = ctk.CTkSwitch(
            frame,
            text=texto,
            command=self.on_config_change,
            onvalue=True,
            offvalue=False
        )
        switch.pack(side="left")
        
        if self.config.get(config_key):
            switch.select()
            
        setattr(self, f"switch_{config_key}", switch)
        
    def select_folder(self):
       # Seleciona pasta para salvamento
        folder = filedialog.askdirectory(title="Selecione a pasta para salvar PDFs")
        if folder:
            self.folder_path.delete(0, 'end')
            self.folder_path.insert(0, folder)
            self.on_config_change()
            
    def on_config_change(self):
       # Atualiza configurações
        # Coleta valores dos switches
        switches = ['remove_bg', 'include_logo', 'show_source', 'disable_links', 'underline_links']
        for switch in switches:
            if hasattr(self, f'switch_{switch}'):
                self.config[switch] = getattr(self, f'switch_{switch}').get()
        
        # Scroll
        if hasattr(self, 'scroll_pages'):
            self.config['scroll_pages'] = self.scroll_pages.get()
        if hasattr(self, 'scroll_delay'):
            self.config['scroll_delay'] = int(self.scroll_delay.get())
        
        # Índice
        if hasattr(self, 'add_index'):
            self.config['add_index'] = self.add_index.get()
            
            if self.config['add_index']:
                self.depth_frame.pack(fill="x", pady=5)
                self.pos_frame.pack(fill="x", pady=5)
            else:
                self.depth_frame.pack_forget()
                self.pos_frame.pack_forget()
                
        if hasattr(self, 'index_depth'):
            self.config['index_depth_text'] = self.index_depth.get()
            depth_map = {
                "Apenas H1": 1,
                "H1 e H2": 2,
                "H1, H2 e H3": 3,
                "Todos (H1-H6)": 6
            }
            self.config['index_depth'] = depth_map.get(self.index_depth.get(), 2)
            
        if hasattr(self, 'index_position'):
            self.config['index_position'] = self.index_position.get()
            
        # Auto-save
        if hasattr(self, 'auto_save'):
            self.config['auto_save'] = self.auto_save.get()
            
            if self.config['auto_save']:
                self.folder_frame.pack(fill="x", pady=5)
            else:
                self.folder_frame.pack_forget()
                
        if hasattr(self, 'folder_path'):
            self.config['save_folder'] = self.folder_path.get()
            
        # Salva configurações
        save_config(self.config)
        self.update_config_preview()
        
    def get_config_text(self):
        #Retorna texto formatado das configurações
        configs = []
        
        if self.config.get('remove_bg'):
            configs.append("🎨 Remover cores de fundo")
        if self.config.get('include_logo'):
            configs.append("🖼️ Com logo")
        if self.config.get('show_source'):
            configs.append("📝 Mostrar fonte")
        if self.config.get('disable_links'):
            configs.append("🔌 Links do conteúdo desativados")
        if self.config.get('underline_links'):
            configs.append("📏 Links sublinhados")
        if self.config.get('scroll_pages'):
            configs.append(f"🔄 Scroll automático ({self.config.get('scroll_delay')}ms)")
        if self.config.get('add_index'):
            pos = "início" if "Início" in self.config.get('index_position', '') else "final"
            configs.append(f"📇 Índice: {self.config.get('index_depth_text', 'H1 e H2')} ({pos})")
        if self.config.get('auto_save'):
            configs.append("💾 Auto-save ativo")
            
        return "   " + "\n   ".join(configs) if configs else "   ⚙️ Configurações padrão"
        
    def update_config_preview(self):
        #Atualiza preview das configurações
        self.config_preview.configure(text=self.get_config_text())
        
    def instalar_playwright(self):
       # Instala Playwright em processo separado
        def install():
            self.root.after(0, lambda: self.stats_label.configure(text="📦 Instalando Playwright..."))
            self.root.after(0, lambda: self.progress_bar.set(0.3))
            
            try:
                # Instala o pacote
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], 
                             check=True, capture_output=True)
                
                self.root.after(0, lambda: self.progress_bar.set(0.6))
                self.root.after(0, lambda: self.stats_label.configure(text="📦 Instalando Chromium..."))
                
                # Instala o Chromium
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                             check=True, capture_output=True)
                
                self.root.after(0, lambda: self.progress_bar.set(1.0))
                self.root.after(0, lambda: self.stats_label.configure(text="✅ Instalação concluída!"))
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Playwright instalado com sucesso!"))
                
                # Atualiza status
                self.playwright_ready = True
                self.root.after(0, self.atualizar_status_inicial)
                
            except Exception as e:
                self.root.after(0, lambda: self.stats_label.configure(text=f"❌ Erro: {str(e)[:50]}"))
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na instalação:\n{str(e)}"))
            
            self.root.after(0, lambda: self.progress_bar.set(0))
        
        thread = threading.Thread(target=install)
        thread.daemon = True
        thread.start()
        
    def validar_url(self, url):
       # Valida URL
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
        
    def iniciar_conversao(self):
       # Inicia conversão em processo separado
        if not self.playwright_ready:
            messagebox.showinfo("Aguarde", "Instale o Playwright primeiro")
            return
            
        url = self.url_entry.get().strip()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)
            
        if not self.validar_url(url):
            messagebox.showwarning("Aviso", "URL inválida")
            return
            
        # Salva configurações temporárias
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.config, temp_config)
        temp_config.close()
        
        # Desabilita interface
        self.btn_converter.configure(state="disabled", text="⏳ Convertendo...")
        self.stats_label.configure(text="🔄 Iniciando conversão...")
        self.progress_bar.set(0.1)
        
        # Inicia processo separado
        thread = threading.Thread(target=self.converter_em_processo, args=(url, temp_config.name))
        thread.daemon = True
        thread.start()
        
    def converter_em_processo(self, url, config_file):
        #Executa conversão
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            from engine.converter import convert_url
            pdf_bytes = convert_url(url, config)
            
            self.root.after(0, lambda: self.processar_pdf(pdf_bytes, url))
            
        except Exception as e:
            # Em caso de erro, incrementa contador de falhas se for lote
            if hasattr(self, 'batch_counter'):
                self.batch_counter['failed'] += 1
                self.root.after(0, lambda: self.stats_label.configure(
                    text=f"⚠️ Erro: {str(e)[:50]}",
                    text_color="#e74c3c"
                ))
            else:
                self.root.after(0, lambda e=e: self.erro_conversao(str(e)))
        finally:
            try:
                os.unlink(config_file)
            except:
                pass
            
            # Só reseta o botão se NÃO for lote
            if not hasattr(self, 'batch_counter'):
                self.root.after(0, lambda: self.btn_converter.configure(
                    state="normal", 
                    text="Converter para PDF"
                ))
            


    #função de feedback do processo de conversão
    def processar_pdf(self, pdf_bytes, url):
        #Salva PDF com feedback silencioso
        self.progress_bar.set(1.0)
        
        parsed = urlparse(url)
        domain = safe_filename(parsed.netloc.replace('www.', ''))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.pdf"
        
        # Verifica se é conversão em lote
        is_batch = hasattr(self, 'batch_counter')
        
        if self.config.get('auto_save') and self.config.get('save_folder'):
            save_path = os.path.join(self.config['save_folder'], filename)
            try:
                with open(save_path, 'wb') as f:
                    f.write(pdf_bytes)
                
                # FEEDBACK SILENCIOSO PARA BATCH
                if is_batch:
                    self.batch_counter['success'] += 1
                    self.stats_label.configure(
                        text=f"✅ Lote: {self.batch_counter['success']}/{self.batch_counter['total']} concluídos",
                        text_color="#2ecc71"
                    )
                else:
                    # URL única: mostra mensagem
                    messagebox.showinfo("Sucesso", f"PDF salvo em:\n{save_path}")
                    
            except Exception as e:
                if is_batch:
                    self.batch_counter['failed'] += 1
                    self.stats_label.configure(
                        text=f"⚠️ Erro em {self.batch_counter['success'] + self.batch_counter['failed']}/{self.batch_counter['total']}",
                        text_color="#e74c3c"
                    )
                else:
                    messagebox.showerror("Erro", f"Não foi possível salvar:\n{str(e)}")
        else:
            # Modo manual (perguntar onde salvar)
            if is_batch:
                # Em lote, ignora modo manual e salva na pasta atual
                with open(filename, 'wb') as f:
                    f.write(pdf_bytes)
                self.batch_counter['success'] += 1
                self.stats_label.configure(
                    text=f"✅ Lote: {self.batch_counter['success']}/{self.batch_counter['total']} salvos em {filename}",
                    text_color="#2ecc71"
                )
            else:
                arquivo = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF", "*.pdf")],
                    initialfile=filename
                )
                if arquivo:
                    with open(arquivo, 'wb') as f:
                        f.write(pdf_bytes)
                    messagebox.showinfo("Sucesso", "PDF salvo com sucesso!")
        
        # Se for o último do lote, mostra resumo
        if is_batch and (self.batch_counter['success'] + self.batch_counter['failed'] == self.batch_counter['total']):
            messagebox.showinfo(
                "Lote Concluído", 
                f"✅ {self.batch_counter['success']} PDFs gerados com sucesso\n"
                f"❌ {self.batch_counter['failed']} falhas\n"
                f"📁 Pasta: {self.config.get('save_folder', 'pasta atual')}"
            )
            # Limpa contador
            delattr(self, 'batch_counter')
        
        # Reseta interface
        self.progress_bar.set(0)
        self.btn_converter.configure(state="normal", text="Converter para PDF")
    


    # função pra retornar o erro
    def erro_conversao(self, erro):
        #Trata erro
        self.progress_bar.set(0)
        self.btn_converter.configure(state="normal", text="🚀 Converter para PDF")
        self.stats_label.configure(text=f"❌ Erro: {erro[:50]}", text_color="#e74c3c")
        messagebox.showerror("Erro", f"Falha na conversão:\n{erro}")