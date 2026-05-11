import streamlit as st
import re
import time
import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# --- Configuração da página ---
st.set_page_config(page_title="Universo dos Cookies App", page_icon="🍪", layout="centered")

# --- BANCO DE DADOS TEMPORÁRIO E NAVEGAÇÃO ---
if 'users' not in st.session_state:
    st.session_state['users'] = []
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'login'

ADMIN_USER = "admin"
ADMIN_SENHA = "admin@123"


def mudar_pagina(nome):
    st.session_state['pagina'] = nome
    st.rerun()


# --- VALIDAÇÃO DE SENHA ---
def validar_senha(senha):
    # Nova regra: apenas tamanho, com 6 caracteres. Sem restrições de conteúdo.
    return len(senha) == 6


def gerar_pdf_receita_bytes(receita: dict) -> bytes:
    """Gera um PDF (A4) em memória com as informações da receita."""
    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margem_x = 50
    y = height - 60

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margem_x, y, receita.get("nome", "Receita"))

    y -= 28
    c.setFont("Helvetica", 11)
    c.drawString(margem_x, y, f"⏱️ Tempo: {receita.get('tempo','')}")
    y -= 16
    c.drawString(margem_x, y, f"🍽️ Porções: {receita.get('porcoes','')}")

    y -= 22
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margem_x, y, "Descrição")

    y -= 16
    c.setFont("Helvetica", 10)
    descricao = receita.get("descricao", "") or ""
    for linha in _quebrar_texto(descricao, 85):
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        c.drawString(margem_x, y, linha)
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margem_x, y, "Ingredientes")

    y -= 16
    c.setFont("Helvetica", 10)
    for ing in receita.get("ingredientes", []):
        linha = f"- {str(ing).strip()}"
        for sublinha in _quebrar_texto(linha, 85):
            if y < 80:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 10)
            c.drawString(margem_x, y, sublinha)
            y -= 14

    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margem_x, y, "Nutrição")

    y -= 16
    c.setFont("Helvetica", 10)
    nut = receita.get("nutricao", {}) or {}
    items = list(nut.items())

    # Simples tabela (duas colunas)
    col_valor_x = margem_x + 260
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margem_x, y, "Item")
    c.drawString(col_valor_x, y, "Valor")
    y -= 14
    c.setFont("Helvetica", 10)

    for k, v in items:
        if y < 80:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        c.drawString(margem_x, y, str(k))
        c.drawString(col_valor_x, y, str(v))
        y -= 14

    c.save()
    buffer.seek(0)
    return buffer.read()


def _quebrar_texto(texto: str, max_chars: int):
    """Quebra texto simples para não estourar a linha no canvas."""
    if not texto:
        return []

    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for p in palavras:
        if len(linha_atual) + len(p) + (1 if linha_atual else 0) <= max_chars:
            linha_atual = f"{linha_atual} {p}".strip()
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = p
    if linha_atual:
        linhas.append(linha_atual)
    return linhas


# --- BANCO DE RECEITAS ---
RECEITAS = [
    {
        "nome": "Cookie Americano Crocante",
        "ingredientes": ["125g de Farinha de trigo", "3 colheres de sopa de Açúcar refinado", "3 colheres de sopa de Açúcar mascavo", "1 colher de chá de Fermento", "1 Ponta de colher de café de sal","1 Ovo inteiro", "50ml de margarina", "Gostas de Chocolate a gosto"],
        "tempo": "15 a 30 min",
        "porcoes": 20,
        "imagem": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=7RVQ5HggiVY",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "210 kcal", "Carboidratos": "28g", "Proteinas": "3g", "Gorduras": "10g"},
        "descricao": "O classico cookie americano com bordas crocantes e centro macio, recheado de gotas de chocolate.",
    },
    {
        "nome": "Cookie de Aveia com Uva Passas",
        "ingredientes": ["1/2 xícara  de uva passas", "1/2  xícara  de farinha de trigo", "1/2  colher de chá de sal", "acucar mascavo", "2 ovos", "1/2  colher de chá de canela em pó", "1/2  colher de fermento em pó", "200gr de manteiga", "3 xícaras de aveia", "1 xícara de açúcar refinado", "1 xícara de açúcar mascavo"],
        "tempo": "15 a 30 min",
        "porcoes": 18,
        "imagem": "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=nBjWok-_g9M",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "185 kcal", "Carboidratos": "26g", "Proteinas": "3g", "Gorduras": "7g"},
        "descricao": "Cookie rustico com aveia em flocos e passas, levemente adocicado com acucar mascavo e canela.",
    },
    {
        "nome": "Cookie Double Chocolate",
        "ingredientes": ["farinha", "cacau em po", "chocolate meio amargo", "manteiga", "acucar", "ovo"],
        "tempo": "15 a 30 min",
        "porcoes": 16,
        "imagem": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=aSINeQ8M0i0",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "245 kcal", "Carboidratos": "30g", "Proteinas": "4g", "Gorduras": "13g"},
        "descricao": "Para os amantes de chocolate: massa de cacau recheada com pedacos de chocolate meio amargo.",
    },
    {
        "nome": "Cupcake de Baunilha com Buttercream",
        "ingredientes": ["2 ovos grandes ou 3 pequenos", "1 colher de  fermento em pó", "2 xícaras de trigo", "1 colher de essência de baunilha", "1 1/2 de de açúcar", "1/2 xícara de leite", "1 xícara de óleo", "1 caixa de leite condensado", "chocolate em pó ou chocolate em barra derretido,ou metade de chocolate em pó e metade de achocolatado."],
        "tempo": "Mais de 30 min",
        "porcoes": 12,
        "imagem": "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=vi3HlWayNpE",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "320 kcal", "Carboidratos": "42g", "Proteinas": "4g", "Gorduras": "15g"},
        "descricao": "Cupcake fofinho de baunilha coberto com buttercream cremoso. Perfeito para festas e comemoracoes.",
    },
    {
        "nome": "Cupcake Red Velvet",
        "ingredientes": ["1 potinho de iogurte natural de 170g","corante em gel vermelho natal e vermelho morango", "100g de manteiga sem sal","2 ovos","1 xícara de açúcar refinado", "1 colher de chá de baunilha", "1 xic e 3/4 de farinha de trigo ou 300g","2 col de sopa de cacau em pó 33% ou 50%","1 col de sopa de fermento em pó","1/2 xícara de leite morno ou 100ml","1 col de sopa de vinagre branco","1 col de chá de bicarbonato de sódio","1 pitada de sal opcional"],
        "tempo": "Mais de 30 min",
        "porcoes": 12,
        "imagem": "https://images.unsplash.com/photo-1587668178277-295251f900ce?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=0CGDUHFAnjo",
        "loja": "https://mercado.carrefour.com.br/r",
        "nutricao": {"Calorias": "340 kcal", "Carboidratos": "44g", "Proteinas": "5g", "Gorduras": "16g"},
        "descricao": "O sofisticado red velvet em formato de cupcake, finalizado com cobertura de cream cheese.",
    },
    {
        "nome": "Cookie de Amendoim",
        "ingredientes": ["pasta de amendoim", "acucar", "ovo", "farinha", "baunilha", "sal"],
        "tempo": "Ate 15 min",
        "porcoes": 14,
        "imagem": "https://images.unsplash.com/photo-1616358339222-04c58b30175d?q=80&w=696&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D?q=80&w=400", 
        "video": "https://www.youtube.com/watch?v=5TY8LirmERY",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "195 kcal", "Carboidratos": "20g", "Proteinas": "5g", "Gorduras": "11g"},
        "descricao": "Cookie simples e rapido feito com pasta de amendoim. Naturalmente sem gluten e irresistivel.",
    },
    {
        "nome": "Cupcake de Limao Siciliano",
        "ingredientes": ["farinha", "manteiga", "acucar", "ovo", "limao siciliano", "raspas de limao", "creme de leite"],
        "tempo": "Mais de 30 min",
        "porcoes": 12,
        "imagem": "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=FqsHX5FUYHc",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "290 kcal", "Carboidratos": "38g", "Proteinas": "4g", "Gorduras": "13g"},
        "descricao": "Cupcake refrescante com sabor intenso de limao siciliano, coberto com ganache citrica.",
    },
    {
        "nome": "Cookie de Nutella",
        "ingredientes": ["farinha", "manteiga", "acucar", "ovo", "nutella", "chocolate branco"],
        "tempo": "15 a 30 min",
        "porcoes": 15,
        "imagem": "https://images.unsplash.com/photo-1590080874088-eec64895b423?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=XjIdqAdzGoE",
        "loja": "https://mercado.carrefour.com.br/r",
        "nutricao": {"Calorias": "265 kcal", "Carboidratos": "33g", "Proteinas": "4g", "Gorduras": "14g"},
        "descricao": "Cookie recheado com Nutella no centro, com casca crocante e interior derretido.",
    },
    {
        "nome": "Cookie de Chocolate com Laranja",
        "ingredientes":["3/4 de xícara de açúcar (135g)", "Raspas de uma laranja 1/2 xícara de manteiga ou margarina (100g)", "2 ovos inteiros", "1/2 xícara de farinha de trigo (325g)", "1 colher de sopa de fermento em pó para bolo (12g)", "100g de damascos picados", "1 barra de chocolate meio amargo picado (90g)"],
        "tempo": "15 a 30 min",
        "porcoes": 16,
        "imagem": "https://images.unsplash.com/photo-1464195085758-89f3e55e821e?q=80&w=1169&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=wB92kNhKt8I",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "230 kcal", "Carboidratos": "28g", "Proteinas": "4g", "Gorduras": "12g"},
        "descricao": "Cookie de chocolate com toque cítrico: raspa de laranja realça o sabor e deixa a massa perfumada.",
    },
    {
        "nome": "Cookie Integral de Banana com Aveia",
        "ingredientes": ["banana madura amassada", "aveia em flocos", "farinha integral", "acucar mascavo", "ovo", "manteiga ou óleo", "canela", "fermento em pó", "passas ou nozes"],
        "tempo": "15 a 30 min",
        "porcoes": 18,
        "imagem": "https://plus.unsplash.com/premium_photo-1668784197038-072eff0d0c12?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D?q=80&w=400",
        "video": "https://www.youtube.com/watch?v=y6rizf_QgZI",
        "loja": "https://mercado.carrefour.com.br/",
        "nutricao": {"Calorias": "190 kcal", "Carboidratos": "24g", "Proteinas": "5g", "Gorduras": "7g"},
        "descricao": "Cookie mais saudável com banana e aveia. Macio por dentro e levemente crocante nas bordas.",
    },
]


# --- CSS GLOBAL ---
st.markdown("""
    <style>

    /* Remove espaçamento do topo mesmo em carregamentos iniciais */
    html, body { margin: 0 !important; padding: 0 !important; }
    #root { margin: 0 !important; padding: 0 !important; }
    div[data-testid="stAppViewContainer"] { margin-top: 0 !important; padding-top: 0 !important; }



    /* Fundo da tela */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1548365328-8c6db3220e4c?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NTZ8fGNvb2tpZXN8ZW58MHx8MHx8fDA%3D') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed;
    }


    /* Remove TODA a barra branca do topo */
    #MainMenu { visibility: hidden !important; }
    header { visibility: hidden !important; height: 0 !important; }
    footer { visibility: hidden !important; }

    /* Alguns elementos do Streamlit ainda reservam espaço (top padding) */
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }

    /* Zerar padding/margin do container principal para não sobrar faixa */
    .block-container { padding-top: 0 !important; margin-top: 0 !important; }

    /* Caso exista um gap extra no topo */
    .stApp { padding-top: 0 !important; margin-top: 0 !important; }

    /* Remove também altura mínima que pode criar “faixa” */
    section[data-testid="stVerticalBlock"] { padding-top: 0 !important; margin-top: 0 !important; }
    [data-testid="stMainBlockContainer"] { padding-top: 0 !important; margin-top: 0 !important; }

    /* Card do login */
    .login-wrapper { padding-top: 0 !important; margin-top: 0 !important; }

    /* Avatar circular na tela de login */
    .avatar-wrapper {
        display: flex;
        justify-content: center;
        margin-bottom: 10px;
    }
    .avatar-wrapper {
        overflow: hidden !important;
        border-radius: 9999px !important;
        display: flex !important;
        justify-content: center !important;
        width: 110px !important;
        height: 110px !important;
        margin: 0 auto !important;
    }

    .avatar-wrapper [data-testid="stImage"] {
        width: 110px !important;
        height: 110px !important;
    }

    .avatar-wrapper [data-testid="stImage"] img {
        border-radius: 50% !important;
        width: 110px !important;
        height: 110px !important;
        min-width: 110px !important;
        min-height: 110px !important;
        display: block !important;
        border: 4px solid #c97d2e !important;
        object-fit: cover !important;
        box-shadow: 0 4px 16px rgba(180,120,40,0.25) !important;
    }




    /* Overlay fixo no topo para cobrir a faixa branca no modo login */
.login-top-overlay {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 9999 !important;
        pointer-events: none !important;
        background-image: url('https://images.unsplash.com/photo-1612845575953-f4b1e3d63160?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTZ8fGNvb2tpZXN8ZW58MHx8MHx8fDA%3D') !important;
        background-size: cover !important;
        background-position: center top !important;
    }

    .login-card {
        background: white;
        border-radius: 24px;
        padding: 0px 32px 28px 32px;
        margin-top: 0px;
        box-shadow: 0 8px 32px rgba(160, 100, 40, 0.18);
        margin: 0 auto;
    }

    /* Imagem circular com borda */
    .img-circular {
        display: flex;
        justify-content: center;
        margin-bottom: 10px;
    }
    .img-circular img {
        width: 110px;
        height: 110px;
        object-fit: cover;
        border-radius: 50%;
        border: 4px solid #c97d2e;
        box-shadow: 0 4px 16px rgba(180,120,40,0.25);
    }

    .centered-text { text-align: center; width: 100%; color: #E02427 !important; font-size: 1.55em; text-shadow: none !important; }
    .subtitle { text-align: center; color: #000000; font-size: 2.33em; margin-bottom: 8px; }

    /* Labels dos campos */
    .field-label {
        font-size: 0.88em;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 2px;
        margin-top: 10px;
    }

    /* Labels e placeholder dentro do cadastro (Streamlit) */
    div[data-testid="stForm"] label {
        color: #FFFFFF !important;
    }


    /* Inputs */
    .stTextInput > div > div > input {
        border: 2px solid #d4a86a !important;
        border-radius: 12px !important;
        background-color: #fffdf9 !important;
        color: #3d2800 !important;
        font-size: 1.1em !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }

    /* Textarea/inputs para reforçar tamanho maior no cadastro */
    .stTextArea > div > textarea {
        font-size: 1.1em !important;
    }


    /* Botao primario - ENTRAR (caramelo cheio) */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(90deg, #c97d2e, #e6a84a) !important;
        color: white !important;
        border-radius: 20px !important;
        height: 46px !important;
        font-weight: bold !important;
        width: 100% !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(201,125,46,0.30) !important;
    }

    /* Botao secundario - CRIAR CONTA (contorno) */
    [data-testid="baseButton-secondary"] {
        background: transparent !important;
        color: #c97d2e !important;
        border-radius: 20px !important;
        height: 46px !important;
        font-weight: bold !important;
        width: 100% !important;
        border: 2px solid #c97d2e !important;
    }

    /* Link esqueceu a senha */
    .link-senha {
        text-align: center;
        margin-top: 12px;
        margin-bottom: 4px;
    }
    .link-senha a {
        color: #FFFFFF !important;
        font-size: 1.2em;
        text-decoration: none;
        font-weight: 600;
    }
    .link-senha a:hover { text-decoration: underline; }

    /* Divisor OU */
    .divider-ou {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 14px 0;
        color: #b09070;
        font-size: 0.85em;
    }
    .divider-ou::before, .divider-ou::after {
        content: '';
        flex: 1;
        border-top: 1px solid #dcc9aa;
    }

    /* Botao Google */
    [data-testid="btn_google"] > button {
        background: #d93025 !important;
        color: white !important;
        border: none !important;
    }
    [data-testid="btn_google"] > button:hover {
        background: #c5221f !important;
        color: white !important;
    }

    /* Cards de receita */
    .recipe-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(160,100,40,0.10);
    }

    </style>
""", unsafe_allow_html=True)


# =============================================
# TELA DE LOGIN
# =============================================
def tela_login():
    # Texto fixo no topo para cobrir/compensar a faixa branca
    st.markdown(
        """
        <div class='top-bora'>Bora Comer um Cookie? Porque Comer faz Bem!😊✨</div>
        <style>
            .top-bora{
                position: relative;
                top: 75px;
                left: 0;
                width: 100%;
                z-index: 10000;
                background: transparent;
                color: #000000;
                text-align: center;
                font-weight: 800;
                padding: 10px 0;
                font-size: 1.30em;
                pointer-events: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Força rerender após trocar para a tela inicial e reduz chance de “gap” persistir do layout anterior
    st.empty()

    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)

    st.markdown("<div style='max-width: 520px; margin: 0 auto;'>", unsafe_allow_html=True)

    with st.container(border=False):
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='avatar-wrapper'>", unsafe_allow_html=True)


        col_av1, col_av2, col_av3 = st.columns([1.2, 1, 1.2])
        with col_av2:
            # Avatar: usa URL, mas com fallback para evitar “não aparece” quando a imagem remota falha.
            avatar_url = "https://images.unsplash.com/photo-1608070734668-e74dc3dda037?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTl8fGNvb2tpZXN8ZW58MHx8MHx8fDA%3D"
            try:
                st.image(avatar_url, width=110, caption="")
            except Exception:
                st.image("avatar.png", width=110, caption="")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<h2 class='centered-text'>Universo dos Cookies</h2>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Bem-vindo! Identifique-se para continuar.</p>", unsafe_allow_html=True)
        st.write("")

        # Labels visiveis
        st.markdown("<p class='field-label'>E-mail</p>", unsafe_allow_html=True)
        email_input = st.text_input("email_label", placeholder="seu@email.com",
                                    key="login_email", label_visibility="collapsed")

        st.markdown("<p class='field-label'>Senha</p>", unsafe_allow_html=True)
        senha_input = st.text_input("senha_label", type="password", placeholder="Sua senha",
                                    key="login_senha", label_visibility="collapsed")

        st.write("")

        # Botoes lado a lado com type correto
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("ENTRAR", key="btn_entrar", type="primary", use_container_width=True):
                if email_input == ADMIN_USER and senha_input == ADMIN_SENHA:
                    st.session_state["is_admin"] = True
                    mudar_pagina("home")
                else:
                    st.session_state["is_admin"] = False
                    valido = any(
                        u["email"] == email_input and u["senha"] == senha_input
                        for u in st.session_state["users"]
                    )
                    if valido:
                        mudar_pagina("home")
                    else:
                        st.error("E-mail ou senha incorretos!")

        with col_b2:
            if st.button("CRIAR CONTA", key="btn_criar", use_container_width=True):
                mudar_pagina("cadastro")

        # Link esqueceu a senha
        st.markdown("""
            <div class='link-senha'>
                <a href='#'>Esqueceu a senha?</a>
            </div>
        """, unsafe_allow_html=True)

        # Divisor OU
        st.markdown("<div class='divider-ou'>ou</div>", unsafe_allow_html=True)

        # Botao Google com bolinha vermelha original
        if st.button("🔴  Fazer login com o Google", key="btn_google", use_container_width=False):
            st.markdown(
                """
                <style>
                  /* Tenta estilizar o botão pelo data-testid gerado pelo Streamlit */
                  [data-testid="btn_google"] > button {
                    background-color: #d93025 !important;
                    color: white !important;
                    border: 0 !important;
                  }
                  [data-testid="btn_google"] > button:hover {
                    background-color: #c5221f !important;
                    color: white !important;
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )
            with st.spinner("Conectando com Google..."):


                import time
                time.sleep(2)
                st.session_state["logged_in"] = True
                mudar_pagina("home")

        st.markdown("</div>", unsafe_allow_html=True)  # fecha login-card

    st.markdown("</div>", unsafe_allow_html=True)  # fecha login-wrapper

# =============================================
# TELA DE CADASTRO
# =============================================
def tela_cadastro():
    st.markdown("<h2 class='centered-text'>Cadastro de Usuario</h2>", unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns([1, 3, 1])
    with col_c2:
        with st.form("form_completo"):
            nome = st.text_input("Nome completo*")
            email = st.text_input("E-mail*")
            data_nasc = st.date_input("Data de Nascimento", format="DD/MM/YYYY")
            endereco = st.text_input("Endereco")
            telefone = st.text_input("Telefone")
            senha = st.text_input("Senha*", type="password")
            if st.form_submit_button("FINALIZAR CADASTRO"):
                if not nome or not email or not senha:
                    st.error("Preencha os campos obrigatorios!")
                elif not validar_senha(senha):
                    st.error("Senha fraca! Use exatamente 6 caracteres.")
                else:
                    st.session_state['users'].append({"nome": nome, "email": email, "senha": senha})
                    st.success("Cadastro realizado com sucesso!")
                    time.sleep(1)
                    mudar_pagina('login')
        if st.button("Voltar"):
            mudar_pagina('login')


# =============================================
# TELA DE RECEITAS
# =============================================
def tela_receitas():
    with st.sidebar:
        st.markdown("### Menu de Acesso")
        if st.button("🚪 SAIR", key="sair_btn"):
            mudar_pagina('login')
        st.write("---")
        if st.button("⚠️ Apagar Conta", key="excluir_btn"):
            st.warning("Conta excluida permanentemente.")
            time.sleep(2)
            mudar_pagina('login')

    st.markdown("<h2 class='centered-text'>🧁 Galeria de Receitas 🥨</h2>", unsafe_allow_html=True)

    if st.session_state.get("is_admin"):
        st.info("Modo Admin: acesso a relatório disponível")
        if st.button("📄 Relatório", key="relatorio_admin"):
            st.session_state["relatorio_admin_clicked"] = True

    if st.session_state.get("relatorio_admin_clicked"):
        # Página/relatório fictício para demonstração
        st.markdown("## 📊 Relatório de Atividades ")
        st.caption("Dados fictícios apenas para visualização.")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Acessos (login)", "128")
        col_b.metric("Cadastros (novos usuários)", "37")
        col_c.metric("Downloads de receitas", "214")

        st.divider()

        # Tabela fictícia por receita
        st.subheader("Downloads por receita ")
        receita_rank = [
            ("Cookie Americano Crocante", 62),
            ("Cupcake de Baunilha com Buttercream", 48),
            ("Cookie de Nutella", 41),
            ("Cupcake Red Velvet", 31),
            ("Cookie de Aveia com Passas", 22),
        ]
        st.table({"Receita": [r[0] for r in receita_rank], "Downloads": [r[1] for r in receita_rank]})

        st.subheader("Resumo ")
        st.write(
            "• Acesso total ao app: **128**\n"
            "• Cadastros realizados: **37**\n"
            "• Downloads de receitas (PDF): **214**"
        )

        if st.button("⬅️ Voltar", key="voltar_relatorio_admin"):
            st.session_state["relatorio_admin_clicked"] = False

            st.rerun()

        # Não renderiza a galeria/busca enquanto o relatório estiver aberto
        st.stop()

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        busca_n = st.text_input("Buscar Receita", placeholder="Ex: chocolate, aveia, limao...")
    with col2:
        tempo = st.selectbox("Tempo", ["Todos", "Ate 15 min", "15 a 30 min", "Mais de 30 min"])
    with col3:
        st.write("")
        pesquisar = st.button("🔍 Pesquisar")

    st.divider()

    if not pesquisar:
        st.info("Use os filtros acima e clique em **Pesquisar** para ver as receitas.")
        return

    receitas_filtradas = RECEITAS

    if busca_n:
        termo = busca_n.lower()
        receitas_filtradas = [
            r for r in receitas_filtradas
            if termo in r["nome"].lower()
            or termo in r["descricao"].lower()
            or any(termo in ing.lower() for ing in r["ingredientes"])
        ]
    if tempo != "Todos":
        receitas_filtradas = [r for r in receitas_filtradas if r["tempo"] == tempo]

    total = len(receitas_filtradas)
    if busca_n or tempo != "Todos":
        st.caption(f"🔍 {total} receita(s) encontrada(s)")
    else:
        st.caption(f"✨ Mostrando todas as {total} receitas")

    if total == 0:
        st.info("Nenhuma receita encontrada. Tente outros termos!")
        return

    if not st.session_state.get("is_admin"):
        st.session_state["is_admin"] = False

    for receita in receitas_filtradas:
        with st.container():
            # remove qualquer espaço branco potencial no topo do card
            st.markdown("<div class='recipe-card' style='margin-top:0; padding-top:0;'>", unsafe_allow_html=True)


            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image(receita["imagem"], width=300)
            with col_info:
                st.markdown(f"### {receita['nome']}")
                st.markdown(f"⏱️ **Tempo:** {receita['tempo']}  |  🍽️ **Porcoes:** {receita['porcoes']}")
                st.caption(receita["descricao"])
                badges = " ".join([f"`{ing}`" for ing in receita["ingredientes"][:4]])
                st.markdown(f"**Ingredientes principais:** {badges}")

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎥 Video", "📝 Ingredientes", "📊 Nutricao", "💬 Feedback", "⬇️ Baixar Receita (PDF)"])

            with tab1:
                st.video(receita["video"])
            with tab2:
                st.info("Ingredientes sugeridos para esta receita:")
                st.markdown("\n".join([f"- {i.capitalize()}" for i in receita["ingredientes"]]))
                st.link_button("🛒 Comprar na Loja Parceira", receita["loja"])
            with tab3:
                nutri_items = list(receita["nutricao"].items())
                st.table({"Item": [i[0] for i in nutri_items], "Valor": [i[1] for i in nutri_items]})
            with tab4:
                fk = f"feedback_{receita['nome'].replace(' ', '_')}"
                texto_feedback = st.text_area("O que achou da receita?", key=fk)

                def _feedback_valido(texto: str) -> tuple[bool, str]:
                    # Validação mínima apenas para não enviar vazio.
                    if not texto or not texto.strip():
                        return False, "Escreva um feedback antes de enviar."
                    return True, ""

                if st.button("Enviar Feedback", key=f"btn_{fk}"):
                    texto_atual = st.session_state.get(fk, "")
                    ok, msg = _feedback_valido(texto_atual)
                    if not ok:
                        st.error(msg)
                        # garante que o texto continue no campo
                        st.session_state[fk] = texto_atual
                    else:
                        st.success("Feedback enviado! Obrigado 😊")
                        st.session_state[fk] = ""

            with tab5:
                pdf_bytes = gerar_pdf_receita_bytes(receita)
                nome_arquivo = f"receita_{receita['nome'].lower().replace(' ', '_')}.pdf"
                st.download_button(
                    label="⬇️ Baixar Receita em PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")


# --- NAVEGACAO ---
if st.session_state['pagina'] == 'login':
    tela_login()
elif st.session_state['pagina'] == 'cadastro':
    tela_cadastro()
elif st.session_state['pagina'] == 'home':
    tela_receitas()
