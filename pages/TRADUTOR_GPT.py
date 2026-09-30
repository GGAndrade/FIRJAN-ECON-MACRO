import streamlit as st
from func import (
    check_password,
    config_page,
    header_firjan,
    footer_firjan,
    to_word_translate,
)
import requests
import json
import locale
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import re
import time

###### CONFIGURAÇÕES INICIAIS

# Configuração da página e identidade visual Firjan
config_page("Tradutor GPT | Firjan - GEE")
header_firjan()

# Especificar locale
with open("pt-BR-format.json", "rb") as f:
    pt_format = json.load(f)
with open("pt-BR-time-format.json", "rb") as f:
    pt_time_format = json.load(f)
locale.setlocale(locale.LC_TIME, locale="pt_BR")


# DEFINIR FUNÇÕES


def concatenate_paragraphs(text):
    """
    Concatenates paragraphs in a string.

    Args:
      text: The input text.

    Returns:
      A string with the paragraphs concatenated.
    """

    paragraphs = text.split("\n\n")
    concatenated_paragraphs = []
    for paragraph in paragraphs:
        if paragraph == "":
            # Skip blank paragraphs.
            continue
        concatenated_paragraphs.append(" ".join(paragraph.split()))
    return "\n\n".join(concatenated_paragraphs)


def remove_short_lines(text):
    """Removes lines from a text string that have less than 3 words.

    Args:
      text: The text string to remove lines from.

    Returns:
      The text string with the short lines removed.
    """

    lines = text.split("\n")
    new_lines = []
    for i in range(len(lines)):
        words = lines[i].split(" ")
        if len(words) >= 3 and len(lines[i]) > 21:
            new_lines.append(lines[i])
        elif lines[i] == "":
            new_lines.append(lines[i])

    return "\n".join(new_lines)


def remove_extra_blank_lines(text):
    # Replace three or more consecutive newline characters with two newline characters
    return re.sub("\n{3,}", "\n\n", text)


def remove_text_after_line(text, line):
    # Find the index of the line
    index = text.find(line)

    # If the line is found, remove everything after it (including the line)
    if index != -1:
        text = text[:index]

    return text


def extract_text_by_page(pdf_path):
    for page_layout in extract_pages(pdf_path):
        texts = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                texts.append(element.get_text())
        yield "\n".join(texts)


def extract_text(pdf):
    text_by_page = []
    for page_text in extract_text_by_page(pdf):
        text_by_page.append(page_text)
    return text_by_page


if check_password():
    # SESSION STATE TRADUÇÃO
    if "traduzido" not in st.session_state:
        st.session_state["traduzido"] = False

    """
    # **Tradutor GPT Econ**
    """

    colA1, colA2, colA3 = st.columns(3)

    with colA1:
        st.markdown(
            """
        ### **O que é?**
        
        O Tradutor GPT Econ é um algoritmo capaz de extrair texto de PDFs e traduzir
        para o inglês usando o ChatGPT da CNI. 
        """,
            unsafe_allow_html=True,
        )

    with colA2:
        st.markdown(
            """
        ### **Como funciona?**
        
        Para funcionar, você precisa fornecer ao algoritmo o ID da sua conversa com
        o bot ChatGPT-CNI e uma chave de acesso para o serviço Microsoft Graph. Mais
        detalhes abaixo.
        """,
            unsafe_allow_html=True,
        )

    with colA3:
        st.markdown(
            """
        ### **Limitações**
        
        Não é capaz de traduzir sentenças muito curtas (até duas palavras ou até 21
        caracteres).
        """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)

    with col1:
        id_teams = st.text_input(label="Link conversa Teams ChatGPT-CNI")

        st.markdown(
            """
        Esse é o link que você obterá ao acessar a janela da sua conversa com o bot
        ChatGPT-CNI no <a href='https://teams.microsoft.com/'>Microsoft Teams</a> 
        através do navegador.
        """,
            unsafe_allow_html=True,
        )

    with col2:
        graph_key = st.text_input(label="Access token Microsoft Graph")
        st.markdown(
            """
        Esse é o token que pode ser obtido através 
        <a href='https://developer.microsoft.com/en-us/graph/graph-explorer'>desse link</a>,
        na aba "Access token", após consentir com as permissões Chat.ReadWrite
        (na lista da esquerda, procurar aba "Microsoft Teams", selecionar a opção
         "create chat", e na tela da direita acessar a aba "Modify permissions"
         e clicar no botão "Consent").     
        """,
            unsafe_allow_html=True,
        )

    # INTERPRETAR FORMULÁRIO

    if id_teams != "" and graph_key != "":
        try:
            id_gpt = id_teams.split("conversations/")[1].split("?")[0]
        except:
            st.write(
                st.error(
                    "Link conversa Teams ChatGPT-CNI inválido! Verifique o link na caixa acima e tente novamente"
                )
            )

    # INTERPRETAR ARQUIVO
    uploaded_file = st.file_uploader(
        "Arquivo PDF",
        type="pdf",
        key="arquivo_traduzir",
        help="Arquivo PDF a ser traduzido.",
    )

    if uploaded_file is not None:
        # EXTRAIR TEXTO E EXECUTAR FUNÇÕES
        original = extract_text(uploaded_file)
        original2 = "\n---------[QUEBRA DE PÁGINA]---------\n".join(original)

        texts = []
        originals = []
        for page in original:
            new = concatenate_paragraphs(page)
            new = remove_short_lines(new)
            new = remove_extra_blank_lines(new)
            originals.append(new)
            new = new.replace("\n\n", "\n[line break]\n")
            texts.append(new)

        original2 = "\n---------[QUEBRA DE PÁGINA]---------\n".join(originals)

        # PEDIR TRADUÇÃO PARA O CHATGPT COM A MICROSOFT GRAPH API

        prompt = 'Translate this from Brazilian Portuguese to English keeping the "[line break]" parts of the text on your translation:'

        if id_teams != "" and graph_key != "":

            def click_button():
                st.session_state["traduzido"] = True

            traduzir = st.button("Traduzir", type="primary", on_click=click_button)

            if st.session_state["traduzido"]:
                with st.status("Traduzindo...", expanded=True) as status:

                    @st.cache_data(ttl=31622400)
                    def invoke_teams_gpt(texts):
                        text_list = []
                        for i, pt in enumerate(texts):
                            if len(pt) > 21:
                                st.write(f"Enviando página {i+1} para o ChatGPT...")

                                url = f"https://graph.microsoft.com/v1.0/me/chats/{id_gpt}/messages"

                                payload = json.dumps(
                                    {"body": {"content": f"{prompt} {pt}"}}
                                )
                                headers = {
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {graph_key}",
                                }

                                response = requests.request(
                                    "POST", url, headers=headers, data=payload
                                )

                                st.write(
                                    f"Aguardando tradução da página {i+1} pelo ChatGPT..."
                                )

                                if (
                                    response.status_code == 200
                                    or response.status_code == 201
                                ):
                                    url = f"https://graph.microsoft.com/v1.0/me/chats/{id_gpt}/messages?$top=1"

                                    payload = {}
                                    headers = {
                                        "Content-Type": "application/json",
                                        "Authorization": f"Bearer {graph_key}",
                                    }

                                    while True:
                                        time.sleep(20)

                                        response = requests.request(
                                            "GET",
                                            url,
                                            headers=headers,
                                            data=payload,
                                        )

                                        if (
                                            response.status_code == 200
                                            or response.status_code == 201
                                        ):
                                            # Convert bytes to string using .decode()
                                            content_string = response.content.decode(
                                                "utf-8"
                                            )

                                            # Convert string to JSON using json.loads()
                                            content_json = json.loads(content_string)

                                            if (
                                                content_json["value"][0]["from"]["user"]
                                                == None
                                            ):
                                                result = (
                                                    content_json["value"][0]["body"][
                                                        "content"
                                                    ]
                                                    .replace("<p>", "")
                                                    .replace("</p>", "")
                                                )
                                                result = result.replace(
                                                    "[line break]", "\n\n"
                                                )
                                                text_list.append(result)
                                                break
                        return text_list

                    text_list = invoke_teams_gpt(texts)

                    text = "\n---------[QUEBRA DE PÁGINA]---------\n".join(text_list)
                    word = to_word_translate(uploaded_file.name, original2, text)
                    status.update(
                        label="Tradução concluída!",
                        state="complete",
                        expanded=False,
                    )
                st.download_button(
                    label="📥 Baixar tradução",
                    data=word,
                    file_name=f"Tradução GPT {uploaded_file.name}.docx",
                    use_container_width=True,
                    key="trad_download",
                )
        else:
            st.info(
                " 🛑 Por favor, insira preencha os parâmetros acima para continuar! 🚫"
            )

# Rodapé oficial Sistema Firjan
footer_firjan()
