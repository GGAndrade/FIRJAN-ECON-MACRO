# -*- coding: utf-8 -*-
"""
Script para geracao do Manual Operacional e Tecnico em PDF do Dashboard Firjan Macro.
Gera um documento PDF elegante com identidade visual Firjan (Cores #002D62, #0072CE, tabelas e fluxogramas).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Paleta Institucional Firjan
AZUL_PRIMARIO = colors.HexColor("#002D62")   # Azul Marinho Firjan
AZUL_SECUNDARIO = colors.HexColor("#0072CE") # Azul Claro Firjan
CINZA_FUNDO = colors.HexColor("#F8FAFC")     # Fundo suave
CINZA_BORDA = colors.HexColor("#CBD5E1")     # Borda sutil
TEXTO_ESCURO = colors.HexColor("#1E293B")    # Grafite escuro
TEXTO_MUTED = colors.HexColor("#64748B")     # Cinza legenda
VERDE_DESTAQUE = colors.HexColor("#16A34A")  # Sucesso/Output

class NumberedCanvas(canvas.Canvas):
    """Canvas de duas passadas para numeracao dinamica de paginas 'Pagina X de Y' e cabecalho/rodape."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXTO_MUTED)
        
        # Se nao for a capa (pagina 1)
        if self._pageNumber > 1:
            # Cabecalho
            self.drawString(54, 800, "FIRJAN | Gerência de Estudos Econômicos (GEE) — Manual do Projeto Dados MACRO")
            self.setStrokeColor(CINZA_BORDA)
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)

            # Rodapé
            self.line(54, 45, 541, 45)
            self.drawString(54, 32, "Uso Interno e Institucional — Atualização Contínua")
            page_text = f"Página {self._pageNumber} de {page_count}"
            self.drawRightString(541, 32, page_text)
            
        self.restoreState()


def gerar_manual_pdf(caminho_saida="MANUAL_PROJETO_FIRJAN_MACRO.pdf"):
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Estilos customizados
    titulo_capa = ParagraphStyle(
        "TituloCapa",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=AZUL_PRIMARIO,
        spaceAfter=10
    )
    
    subtitulo_capa = ParagraphStyle(
        "SubtituloCapa",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=17,
        textColor=AZUL_SECUNDARIO,
        spaceAfter=25
    )

    h1 = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=AZUL_PRIMARIO,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2 = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=AZUL_SECUNDARIO,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    corpo = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=TEXTO_ESCURO,
        spaceAfter=6
    )

    corpo_bold = ParagraphStyle(
        "Body_Bold",
        parent=corpo,
        fontName="Helvetica-Bold"
    )

    tabela_texto = ParagraphStyle(
        "Table_Text",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXTO_ESCURO
    )

    tabela_header = ParagraphStyle(
        "Table_Header",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white
    )

    card_resumo = ParagraphStyle(
        "Card_Text",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=TEXTO_ESCURO
    )

    story = []

    # -------------------------------------------------------------
    # CAPA / CABEÇALHO DO DOCUMENTO
    # -------------------------------------------------------------
    if os.path.exists("firjan_logo.png"):
        logo = Image("firjan_logo.png", width=140, height=45)
        logo.hAlign = 'LEFT'
        story.append(logo)
        story.append(Spacer(1, 15))

    story.append(Paragraph("MANUAL OPERACIONAL E TÉCNICO", titulo_capa))
    story.append(Paragraph("Plataforma Firjan de Dados e Indicadores Macroeconômicos (Streamlit)", subtitulo_capa))
    
    # Box de Metadados do Projeto
    meta_data = [
        [Paragraph("<b>Projeto:</b> Plataforma Dados MACRO", tabela_texto), Paragraph("<b>Unidade:</b> Gerência de Estudos Econômicos (GEE)", tabela_texto)],
        [Paragraph("<b>Responsável Técnica:</b> Gerlane Andrade", tabela_texto), Paragraph("<b>Ambiente:</b> Local (Porta 8501) & Nuvem (Streamlit Cloud)", tabela_texto)],
        [Paragraph("<b>Repositório:</b> GitHub (GGAndrade/FIRJAN-ECON-MACRO)", tabela_texto), Paragraph("<b>Última Atualização:</b> Outubro / 2026", tabela_texto)]
    ]
    t_meta = Table(meta_data, colWidths=[240, 247])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CINZA_FUNDO),
        ('BOX', (0,0), (-1,-1), 1, CINZA_BORDA),
        ('INNERGRID', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_PRIMARIO, spaceAfter=15))

    # -------------------------------------------------------------
    # 1. VISÃO GERAL E ESTRUTURA DO PROJETO
    # -------------------------------------------------------------
    story.append(Paragraph("1. Visão Geral e Estrutura Arquitetural", h1))
    story.append(Paragraph(
        "A aplicação é um portal analítico multipágina construído com <b>Streamlit</b> e <b>Altair</b> para disponibilizar "
        "indicadores macroeconômicos e industriais padronizados com a identidade visual da <b>Firjan</b>. "
        "A plataforma opera de forma híbrida: execução local rápida para análises internas e deploy automatizado no Streamlit Community Cloud para difusão externa.",
        corpo
    ))

    # Tabela com as páginas e módulos
    modulos = [
        [Paragraph("Módulo / Página", tabela_header), Paragraph("Arquivo Fonte", tabela_header), Paragraph("Objetivo & Tema", tabela_header)],
        [Paragraph("<b>Início</b>", tabela_texto), Paragraph("<code>INICIO.py</code>", tabela_texto), Paragraph("Apresentação institucional, equipe técnica e menu de acesso rápido.", tabela_texto)],
        [Paragraph("<b>PIM</b>", tabela_texto), Paragraph("<code>pages/PIM.py</code>", tabela_texto), Paragraph("Produção Física Industrial Integrada: Brasil, RJ, UFs e Comparativo entre Estados.", tabela_texto)],
        [Paragraph("<b>PIM-BR</b>", tabela_texto), Paragraph("<code>pages/PIM_BR.py</code>", tabela_texto), Paragraph("Produção Física Industrial do Brasil detalhada (27 ramos investigados).", tabela_texto)],
        [Paragraph("<b>Indústria no Mundo</b>", tabela_texto), Paragraph("<code>pages/INDUSTRIA_NO_MUNDO.py</code>", tabela_texto), Paragraph("Produção Manufatureira Mundial (UNIDO) e Exportações Mundiais (OCDE / Comtrade).", tabela_texto)],
        [Paragraph("<b>CAC SHWEB</b>", tabela_texto), Paragraph("<code>pages/CAC_SHWEB.py</code>", tabela_texto), Paragraph("Coeficientes de Abertura Comercial (CEX, CPI, CII, CEL) e gerador de planilhas.", tabela_texto)],
    ]
    t_modulos = Table(modulos, colWidths=[110, 130, 247])
    t_modulos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), AZUL_PRIMARIO),
        ('BOX', (0,0), (-1,-1), 1, CINZA_BORDA),
        ('INNERGRID', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, CINZA_FUNDO]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_modulos)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # 2. FLUXO DE ENTRADAS (INPUTS) E SAÍDAS (OUTPUTS)
    # -------------------------------------------------------------
    story.append(Paragraph("2. Mapeamento de Entradas (Inputs) e Saídas (Outputs)", h1))
    story.append(Paragraph(
        "A tabela a seguir orienta detalhadamente o operador sobre o que cada módulo consome e o que entrega aos usuários:",
        corpo
    ))

    io_data = [
        [Paragraph("Módulo", tabela_header), Paragraph("Entradas (Inputs)", tabela_header), Paragraph("Saídas Geradas (Outputs)", tabela_header)],
        [
            Paragraph("<b>PIM / PIM-BR</b><br/>(IBGE)", tabela_texto),
            Paragraph("• Base padrão: <code>PIM_BR/pim_agregado.parquet</code><br/>"
                      "• <b>Upload opcional:</b> arquivo <code>.parquet</code> com colunas <code>DATA, VARIAVEL, SUBGRUPOS, VALOR, LOCAL</code><br/>"
                      "• Filtros de interface: Estado, Setor, Intervalo de Anos.", tabela_texto),
            Paragraph("• Gráficos temporais Altair com marcadores de Máximo, Mínimo e Último.<br/>"
                      "• Cards de destaque com diferenciais de pico.<br/>"
                      "• Ranking setorial em barras.<br/>"
                      "• Exportação de tabela consolidada em <b>Excel (.xlsx)</b>.", tabela_texto)
        ],
        [
            Paragraph("<b>Indústria no Mundo</b><br/>(UNIDO / OCDE)", tabela_texto),
            Paragraph("• <code>IND_MUNDO_UNIDO.parquet</code><br/>"
                      "• <code>IND_MUNDO_OECD.parquet</code><br/>"
                      "• <code>EXP_PARTNERWORLD_COMTRADE.parquet</code><br/>"
                      "• Seleção de País, Setor ISIC e Moeda.", tabela_texto),
            Paragraph("• Curvas de participação relativa do Brasil na produção manufatureira mundial.<br/>"
                      "• Evolução dos fluxos exportadores globais.<br/>"
                      "• Download dos dados tabulados em <b>Excel</b>.", tabela_texto)
        ],
        [
            Paragraph("<b>CAC SHWEB</b><br/>(Abertura Comercial)", tabela_texto),
            Paragraph("• Planilhas base de insumos em <code>cac/</code><br/>"
                      "• <b>Upload no gerador:</b> Planilhas <code>.xlsx</code> de preços constantes/correntes extraídas do MDIC/SHWEB.", tabela_texto),
            Paragraph("• Indicadores de inserção externa (CEX, CPI, CII, CEL).<br/>"
                      "• Planilhas estruturadas prontas para download e carga corporativa Firjan.", tabela_texto)
        ],
    ]
    t_io = Table(io_data, colWidths=[95, 195, 197])
    t_io.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), AZUL_PRIMARIO),
        ('BOX', (0,0), (-1,-1), 1, CINZA_BORDA),
        ('INNERGRID', (0,0), (-1,-1), 0.5, CINZA_BORDA),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, CINZA_FUNDO]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_io)
    story.append(Spacer(1, 14))

    # Quebra de página para o Passo a Passo e Resumo Visual
    story.append(PageBreak())

    # -------------------------------------------------------------
    # 3. PASSO A PASSO OPERACIONAL DO USUÁRIO
    # -------------------------------------------------------------
    story.append(Paragraph("3. Passo a Passo Operacional: Como Usar e Atualizar", h1))

    story.append(Paragraph("3.1 Execução do Ambiente Local (Computador do Usuário)", h2))
    story.append(Paragraph(
        "<b>Para iniciar o dashboard localmente com 1 clique:</b><br/>"
        "1. Abra a pasta do projeto <code>CNI-ECON-GERAL</code>.<br/>"
        "2. Dê dois cliques no arquivo <b><code>INICIAR_LOCAL.bat</code></b>.<br/>"
        "3. Uma janela do terminal será aberta iniciando o servidor e seu navegador abrirá em <b><code>http://localhost:8501</code></b>.<br/>"
        "4. Mantenha essa janela aberta enquanto estiver utilizando o sistema local.",
        corpo
    ))

    story.append(Paragraph("3.2 Atualização da Base de Dados da PIM (IBGE)", h2))
    story.append(Paragraph(
        "Sempre que o IBGE divulgar um novo mês da Pesquisa Industrial Mensal:<br/>"
        "1. Acesse o dashboard na página <b>PIM</b> (ou <b>PIM-BR</b>).<br/>"
        "2. No campo superior <b>'Arquivo Parquet'</b>, faça o upload do arquivo atualizado.<br/>"
        "3. O sistema recalculará imediatamente todos os gráficos, cards, extremos e rankings em memória.<br/>"
        "4. Para tornar o arquivo o padrão permanente do servidor, clique no botão verde <b>'💾 Salvar arquivo como base permanente padrão'</b>.",
        corpo
    ))

    story.append(Paragraph("3.3 Rótulos Amigáveis e Tooltips Oficiais", h2))
    story.append(Paragraph(
        "Os nomes dos setores industriais foram simplificados para melhor leitura visual (ex.: <i>'Couros e calçados'</i> em vez de códigos numéricos extensos). "
        "Para conferir a classificação técnica oficial do IBGE, basta <b>posicionar o cursor do mouse (hover)</b> sobre a linha do gráfico, sobre o ponto extremo ou sobre o card de destaque.",
        corpo
    ))

    story.append(Paragraph("3.4 Arquitetura Keep-Alive (Prevenção de Hibernação na Nuvem)", h2))
    story.append(Paragraph(
        "O aplicativo publicado em <code>https://firjan-macro.streamlit.app</code> possui automação configurada via <b>GitHub Actions</b> "
        "(arquivo <code>.github/workflows/keep_alive.yml</code>), que executa pings automáticos a cada 8 horas diretamente dos servidores do GitHub. "
        "Isso assegura que o aplicativo nunca hiberne por inatividade, permitindo envio direto de links por WhatsApp ou e-mail a qualquer momento.",
        corpo
    ))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 4. RESUMO VISUAL DO FLUXO (ESTRUTURA VISUAL)
    # -------------------------------------------------------------
    story.append(Paragraph("4. Resumo Visual: Diagrama do Fluxo da Informação", h1))
    
    # Criar um painel visual em tabela com blocos estilizados simulando um flowchart
    bloco_inputs = Paragraph("<b>📥 1. ENTRADAS (INPUTS)</b><br/><br/>"
                             "• Parquet Oficial PIM (IBGE)<br/>"
                             "• Bases Globais UNIDO & OCDE<br/>"
                             "• Cargas SHWEB / MDIC (Excel)<br/>"
                             "• Upload interativo do usuário", card_resumo)

    bloco_processo = Paragraph("<b>⚙️ 2. PROCESSAMENTO</b><br/><br/>"
                               "• Filtros temporais & UFs<br/>"
                               "• Mapeamento de Rótulos Concisos<br/>"
                               "• Cálculo de picos (Máx, Mín, Dif)<br/>"
                               "• Cache com TTL & downcasting leve", card_resumo)

    bloco_outputs = Paragraph("<b>📊 3. SAÍDAS (OUTPUTS)</b><br/><br/>"
                              "• Curvas Altair Interativas<br/>"
                              "• Cards de Destaque com Tooltip<br/>"
                              "• Rankings e Tabelas Regionais<br/>"
                              "• Download em Planilhas Excel", card_resumo)

    t_diagrama = Table(
        [[bloco_inputs, Paragraph("<b>➔</b>", ParagraphStyle("Seta", fontName="Helvetica-Bold", fontSize=18, alignment=1, textColor=AZUL_SECUNDARIO)),
          bloco_processo, Paragraph("<b>➔</b>", ParagraphStyle("Seta", fontName="Helvetica-Bold", fontSize=18, alignment=1, textColor=AZUL_SECUNDARIO)),
          bloco_outputs]],
        colWidths=[140, 20, 145, 20, 162]
    )
    t_diagrama.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), CINZA_FUNDO),
        ('BACKGROUND', (2,0), (2,0), CINZA_FUNDO),
        ('BACKGROUND', (4,0), (4,0), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (0,0), 1.5, AZUL_PRIMARIO),
        ('BOX', (2,0), (2,0), 1.5, AZUL_SECUNDARIO),
        ('BOX', (4,0), (4,0), 1.5, VERDE_DESTAQUE),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (3,0), (3,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_diagrama)
    story.append(Spacer(1, 15))

    # Box de Dicas Rápidas
    dicas_texto = Paragraph(
        "<b>💡 Dicas de Suporte e Diagnóstico Rápido:</b><br/>"
        "• <b>Erro de Conexão Recusada no Localhost:</b> Dê dois cliques em <code>INICIAR_LOCAL.bat</code> para subir o servidor.<br/>"
        "• <b>Memória no Streamlit Cloud:</b> A aplicação já conta com liberação de cache a cada 30min (<code>ttl=1800</code>). "
        "Caso necessário, acerte o reinício em <i>Manage app ➔ Reboot app</i>.<br/>"
        "• <b>Publicação de Alterações:</b> Todo <code>git push</code> para a branch <code>main</code> atualiza automaticamente o app online.",
        card_resumo
    )
    t_dicas = Table([[dicas_texto]], colWidths=[487])
    t_dicas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF9C3")), # Amarelo suave
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CA8A04")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_dicas)

    # Construir PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    return caminho_saida

if __name__ == "__main__":
    gerar_manual_pdf()
    print("PDF gerado com sucesso!")
