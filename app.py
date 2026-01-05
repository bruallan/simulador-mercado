import streamlit as st
import pandas as pd
import re

# Configuração da página
st.set_page_config(page_title="Simulador de Margem de Lucro Pro", layout="wide")

# Título centralizado
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
        # Limpeza de caracteres não numéricos, mantendo o ponto decimal
        limpo = valor.replace("R$", "").strip()
        if "," in limpo and "." in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        elif "," in limpo:
            limpo = limpo.replace(",", ".")
        limpo = re.sub(r'[^0-9.-]', '', limpo)
        try:
            return float(limpo)
        except ValueError:
            return 0.0
    return float(valor)

# 3. Seleção de Mercado
col_header1, col_header2 = st.columns(2)

with col_header1:
    unidade_nome = st.selectbox("Selecione o Mercado:", list(config_unidades.keys()))
    info_unidade = config_unidades[unidade_nome]
    custo_op_percentual = info_unidade["custo_op"]
    st.caption(f"*Custo Operacional aplicado: {custo_op_percentual*100:.0f}%")

# 4. Carregamento de Dados
@st.cache_data(ttl=60)
def carregar_dados(url):
    try:
        # Lendo colunas específicas: Produto, Custo e Venda
        df = pd.read_csv(url, usecols=[2, 3, 4], names=["Produto", "Custo_Ultima", "Venda_Atual"], skiprows=2)
        df["Produto"] = df["Produto"].str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return None

df = carregar_dados(info_unidade["url"])

if df is not None:
    lista_produtos = sorted(df["Produto"].unique().tolist())
    
    with col_header2:
        produto_escolhido = st.selectbox("Selecione o Produto:", lista_produtos)
    
    # Filtragem dos dados do produto selecionado
    dados_filtrados = df[df["Produto"] == produto_escolhido]
    
    if not dados_filtrados.empty:
        item = dados_filtrados.iloc[0]
        custo_base = limpar_valor(item["Custo_Ultima"])
        venda_base = limpar_valor(item["Venda_Atual"])
    else:
        custo_base = 0.0
        venda_base = 0.0

    st.divider()

    # Cálculo do Lucro Real (vindo da planilha)
    # Fórmula: (Venda - Impostos - Custo) / Venda
    lucro_real_val = (venda_base - (venda_base * custo_op_percentual) - custo_base) / venda_base if venda_base > 0 else 0

    # 5. Layout das Colunas
    col_simulador, col_valores_reais = st.columns(2)

    # --- COLUNA: SIMULADOR (Onde o usuário mexe) ---
    with col_simulador:
        st.subheader("💡 Simulador")
        
        # A chave dinâmica força o reset do valor quando mudar mercado ou produto
        chave_sim = f"sim_{unidade_nome}_{produto_escolhido}"
        
        p_custo_sim = st.number_input(
            "Custo Simulado (R$)", 
            min_value=0.0, 
            value=custo_base,
            step=0.01, 
            format="%.2f",
            key=f"input_c_{chave_sim}"
        )
        
        v_venda_sim = st.number_input(
            "Venda Simulada (R$)", 
            min_value=0.0, 
            value=venda_base, 
            step=0.01, 
            format="%.2f",
            key=f"input_v_{chave_sim}"
        )

        # Cálculo da Margem Simulada
        lucro_sim_val = (v_venda_sim - (v_venda_sim * custo_op_percentual) - p_custo_sim) / v_venda_sim if v_venda_sim > 0 else 0
        delta_val = (lucro_sim_val - lucro_real_val) * 100
        
        st.metric(
            label="Margem Simulada (%)", 
            value=f"{lucro_sim_val * 100:.2f}%", 
            delta=f"{delta_val:.2f}%"
        )

    # --- COLUNA: VALORES REAIS (Baseados na Planilha - Travados) ---
    with col_valores_reais:
        st.subheader("📋 Valores Reais (Base)")
        
        # Chave dinâmica também aqui para garantir a atualização visual
        chave_real = f"real_{unidade_nome}_{produto_escolhido}"
        
        st.number_input(
            "Custo da Última Compra (R$)", 
            value=custo_base, 
            disabled=True, 
            format="%.2f",
            key=f"real_c_{chave_real}"
        )
        
        st.number_input(
            "Preço de Venda Atual (R$)", 
            value=venda_base, 
            disabled=True, 
            format="%.2f",
            key=f"real_v_{chave_real}"
        )
        
        st.metric(label="Margem Real Atual (%)", value=f"{lucro_real_val * 100:.2f}%")

else:
    st.error("Não foi possível carregar os dados. Verifique os links das planilhas.")
