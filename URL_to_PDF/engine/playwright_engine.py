import time
from playwright.sync_api import sync_playwright

def scroll_page(page, config):
    if config.get('scroll_pages', True):
        delay = config.get('scroll_delay', 500) / 1000
        # Reduz attempts e usa evaluate mais rápido
        last_height = page.evaluate('document.body.scrollHeight')
        for _ in range(3):  
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(delay)
            new_height = page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height
        # Só volta se necessário
        if config.get('reset_scroll', True):
            page.evaluate('window.scrollTo(0, 0)')
            time.sleep(0.1)  

def wait_content(page):
    # Selector mais rápido primeiro
    try:
        page.wait_for_selector("main, article, .content", timeout=5000)  
    except:
        page.wait_for_timeout(1000)  #

def gerar_pdf(url, config):
    with sync_playwright() as p:
        # Lançamento mais rápido
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',  # Reduz uso de RAM
                '--no-sandbox',  # Mais rápido em alguns sistemas
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'  # Acelera em headless
            ]
        )

        #Contexto mais leve
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 720},  # Reduz resolução 
            locale="pt-BR",
            device_scale_factor=1,  # Evita renderização em alta resolução
            has_touch=False,
            java_script_enabled=True  # Só desabilite se realmente não precisar
        )

        page = context.new_page()
        
        # Timeouts inteligentes
        page.set_default_navigation_timeout(30000)  
        page.set_default_timeout(30000)

        # Carregamento progressivo
        try:
            # Primeiro carrega rápido, depois espera conteúdo
            response = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            if response and response.ok:
                # Se página carregou, espera um pouco pelo conteúdo
                page.wait_for_timeout(1000)
                wait_content(page)
                scroll_page(page, config)
            else:
                # Se falhou, tenta com mais calma
                page.goto(url, wait_until="networkidle", timeout=30000)
                
        except Exception as e:
            print(f"Erro leve: {e}")  # Não trava, tenta continuar

        
        # Aplica configurações só se necessário
        if any([config.get('remove_bg'), config.get('disable_links'), 
                config.get('underline_links'), config.get('add_index'),
                config.get('include_logo'), config.get('show_source')]):
            
            page.evaluate("""
                ({config, url}) => {
                    // Aplica tudo de uma vez
                    if (config.remove_bg) {
                        const style = document.createElement('style');
                        style.textContent = '*{background:transparent!important;background-image:none!important}body{background:white!important}';
                        document.head.appendChild(style);
                    }
                    
                    if (config.disable_links) {
                        document.querySelectorAll('a').forEach(a => {
                            if (!a.getAttribute('href')?.includes('#heading-')) {
                                a.removeAttribute('href');
                            }
                        });
                    }
                    
                    if (config.underline_links) {
                        const style = document.createElement('style');
                        style.textContent = 'a{text-decoration:underline!important}';
                        document.head.appendChild(style);
                    }
                    
                    if (config.add_index) {
                        const headings = [];
                        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach((el, idx) => {
                            const level = parseInt(el.tagName[1]);
                            if (level <= config.index_depth) {
                                const text = el.textContent.trim();
                                if (text && text.length > 3) {
                                    const id = `h-${idx}`;
                                    el.id = id;
                                    headings.push({ level, text, id });
                                }
                            }
                        });
                        
                        if (headings.length) {
                            const toc = document.createElement('div');
                            toc.style.cssText = 'background:#f8f9fa;padding:15px;margin:15px 0;border:1px solid #dee2e6;';
                            toc.innerHTML = '<h3>📑 Índice</h3><ul style="list-style:none;padding:0;">' +
                                headings.map(h => 
                                    `<li style="margin-left:${(h.level-1)*15}px;margin-bottom:5px;">
                                        <a href="#${h.id}" style="color:#0066cc;">${h.text}</a>
                                    </li>`
                                ).join('') + '</ul>';
                            
                            if (config.index_position.includes('Início')) {
                                document.body.insertBefore(toc, document.body.firstChild);
                            } else {
                                document.body.appendChild(toc);
                            }
                        }
                    }
                    
                    if (config.include_logo) {
                        const logo = document.createElement('div');
                        logo.style.cssText = 'text-align:center;margin:10px 0;font-size:24px;border-bottom:1px solid #3498db;padding:5px;';
                        logo.innerHTML = '🌐➡️📄';
                        document.body.insertBefore(logo, document.body.firstChild);
                    }
                    
                    if (config.show_source) {
                        const source = document.createElement('div');
                        source.style.cssText = 'text-align:right;font-size:8px;color:#999;margin-top:15px;';
                        source.textContent = 'Fonte: ' + url;
                        document.body.appendChild(source);
                    }
                }
            """, {"config": config, "url": url})
        
        
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"}
        )

        
        context.close()
        browser.close()

        return pdf_bytes