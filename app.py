import streamlit as st
import pandas as pd
import re

# Configuração da página
st.set_page_config(page_title="Simulador de Margem de Lucro Pro", layout="wide")

# Título centralizado e limpo
st.markdown("<h1 style='text-align: center;'>Simulador de Margem de Lucro Pro</h1>", unsafe_allow_html=True)

# 1. Configurações das Unidades
config_unidades = {
    "Porto Sollare": {
        "url": "https://docs.google.com/spreadsheets/d/1fH_fKBmoLCge05pXrKCiUFqklOJSL5Ue/export?format=csv",
        "custo_op": 0.20
    },
    "Villa dos Pássaros": {
        "url": "https://docs.google.com/spreadsheets/d/1UDU-2AXJJGEFZUz52KYm8uDR3EldIDx8/export?format=csv",
        "custo_op": 0.26
    }
}

# 2. Função de Limpeza de Dados
def limpar_valor(valor):
    if pd.isna(valor) or valor == "":
        return 0.0
    if isinstance(valor, str):
        limpo = valor.replace("R$", "").strip()
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        limpo = re.sub(r'[^0-9.-]', '', limpo)
        try:
            return float(limpo)
        except ValueError:
            return 0.0
    return float(valor)

# 3. Gerenciamento de Estado
if 'produto_selecionado' not in st.session_state:
    st.session_state.produto_selecionado = None

# 4. Seleção de Mercado e Cabeçalho
col_header1, col_header2 = st.columns(2)

with col_header1:
    unidade_nome = st.selectbox("Selecione o Mercado:", list(config_unidades.keys()))
    info_unidade = config_unidades[unidade_nome]
    custo_op_percentual = info_unidade["custo_op"]
    st.caption(f"*Custo Operacional de {custo_op_percentual*100:.0f}%")

@st.cache_data(ttl=60)
def carregar_dados(url):
    try:
        # skiprows=2 pula a linha 'DESCRIÇÃO...' e a linha de cabeçalho das colunas
        df = pd.read_csv(url, usecols=[2, 3, 4], names=["Produto", "Custo_Ultima", "Venda_Atual"], skiprows=2)
        return df
    except:
        return None

df = carregar_dados(info_unidade["url"])

if df is not None:
    lista_produtos = df["Produto"].unique().tolist()
    index_atual = 0
    if st.session_state.produto_selecionado in lista_produtos:
        index_atual = lista_produtos.index(st.session_state.produto_selecionado)
    
    with col_header2:
        produto_escolhido = st.selectbox("Selecione o Produto:", lista_produtos, index=index_atual)
        st.session_state.produto_selecionado = produto_escolhido
    
    # Extração de dados reais
    dados = df[df["Produto"] == produto_escolhido].iloc[0]
    custo_ultima_real = limpar_valor(dados["Custo_Ultima"])
    venda_atual_real = limpar_valor(dados["Venda_Atual"])

    st.divider()

    # 5. Cálculos
    lucro_real_val = (venda_atual_real - (venda_atual_real * custo_op_percentual) - custo_ultima_real) / venda_atual_real if venda_atual_real > 0 else 0

    # 6. Layout Simétrico e Alinhado
    col_simulador, col_valores_reais = st.columns(2)

    # --- COLUNA: SIMULADOR ---
    with col_simulador:
        st.subheader("Simulador")
        
        # Preço da Prateleira (Auto-preenchido e com Step 1.0)
        preco_prateleira = st.number_input(
            "Preço da Prateleira (R$)", 
            min_value=0.0, 
            value=custo_ultima_real,
            step=1.0, 
            format="%.2f",
            key=f"sim_prat_{produto_escolhido}"
        )
        
        # Preço de Venda Simulado
        venda_simulada = st.number_input(
            "Preço de Venda Simulado (R$)", 
            min_value=0.0, 
            value=venda_atual_real, 
            step=1.0, 
            format="%.2f",
            key=f"sim_venda_{produto_escolhido}"
        )

        if venda_simulada > 0:
            lucro_simulado_val = (venda_simulada - (venda_simulada * custo_op_percentual) - preco_prateleira) / venda_simulada
        else:
            lucro_simulado_val = 0.0

        delta_val = (lucro_simulado_val - lucro_real_val) * 100
        
        st.metric(
            label="Margem de Lucro Simulada (%)", 
            value=f"{lucro_simulado_val * 100:.2f}%", 
            delta=f"{delta_val:.2f}%"
        )

    # --- COLUNA: VALORES REAIS ---
    with col_valores_reais:
        st.subheader("Valores Reais")
        
        # Chaves dinâmicas f"real_..." garantem a atualização ao trocar o produto
        st.number_input(
            "Custo da Última Compra (R$)", 
            value=custo_ultima_real, 
            disabled=True, 
            format="%.2f",
            key=f"real_custo_{produto_escolhido}"
        )
        
        st.number_input(
            "Preço de Venda Atual (R$)", 
            value=venda_atual_real, 
            disabled=True, 
            format="%.2f",
            key=f"real_venda_{produto_escolhido}"
        )
        
        st.metric(
            label="Lucro Real Atual (%)", 
            value=f"{lucro_real_val * 100:.2f}%"
        )

else:
    st.error("Erro ao carregar a planilha. Verifique a conexão.")
