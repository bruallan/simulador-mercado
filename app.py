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
        # Remove R$, espaços e ajusta separadores decimais
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
    st.caption(f"*Custo Operacional de {custo_op_percentual*100:.0f}%")

# 4. Carregamento de Dados
@st.cache_data(ttl=60) # Aumentei um pouco o tempo para estabilidade
def carregar_dados(url):
    try:
        # skiprows=2 pula as linhas iniciais se necessário
        df = pd.read_csv(url, usecols=[2, 3, 4], names=["Produto", "Custo_Ultima", "Venda_Atual"], skiprows=2)
        df["Produto"] = df["Produto"].str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados(info_unidade["url"])

if df is not None:
    lista_produtos = sorted(df["Produto"].unique().tolist())
    
    with col_header2:
        produto_escolhido = st.selectbox("Selecione o Produto:", lista_produtos, key="sb_produto")
    
    # Busca dos dados do produto selecionado
    dados_filtrados = df[df["Produto"] == produto_escolhido]
    
    if not dados_filtrados.empty:
        item = dados_filtrados.iloc[0]
        custo_ultima_real = limpar_valor(item["Custo_Ultima"])
        venda_atual_real = limpar_valor(item["Venda_Atual"])
    else:
        custo_ultima_real = 0.0
        venda_atual_real = 0.0

    st.divider()

    # Cálculo do Lucro Real Atual (Fórmula: (Venda - Impostos/Custos - Custo Produto) / Venda)
    lucro_real_val = (venda_atual_real - (venda_atual_real * custo_op_percentual) - custo_ultima_real) / venda_atual_real if venda_atual_real > 0 else 0

    # 5. Layout Simétrico
    col_simulador, col_valores_reais = st.columns(2)

    # --- COLUNA: SIMULADOR (ENTRADA) ---
    with col_simulador:
        st.subheader("Simulador")
        
        # Chave dinâmica para resetar quando mudar o produto
        p_prateleira = st.number_input(
            "Preço de Custo Simulado (R$)", 
            min_value=0.0, 
            value=custo_ultima_real,
            step=0.01, 
            format="%.2f",
            key=f"input_custo_{unidade_nome}_{produto_escolhido}"
        )
        
        v_simulada = st.number_input(
            "Preço de Venda Simulado (R$)", 
            min_value=0.0, 
            value=venda_atual_real, 
            step=0.01, 
            format="%.2f",
            key=f"input_venda_{unidade_nome}_{produto_escolhido}"
        )

        lucro_sim_val = (v_simulada - (v_simulada * custo_op_percentual) - p_prateleira) / v_simulada if v_simulada > 0 else 0
        delta_val = (lucro_sim_val - lucro_real_val) * 100
        
        st.metric(label="Margem de Lucro Simulada (%)", value=f"{lucro_sim_val * 100:.2f}%", delta=f"{delta_val:.2f}%")

    # --- COLUNA: VALORES REAIS (BASE) ---
    with col_valores_reais:
        st.subheader("Valores Reais")
        
        # AQUI ESTÁ A CORREÇÃO: Adicionamos chaves únicas baseadas no produto e mercado
        st.number_input(
            "Custo da Última Compra (R$)", 
            value=custo_ultima_real, 
            disabled=True, 
            format="%.2f",
            key=f"real_custo_{unidade_nome}_{produto_escolhido}"
        )
        
        st.number_input(
            "Preço de Venda Atual (R$)", 
            value=venda_atual_real, 
            disabled=True, 
            format="%.2f",
            key=f"real_venda_{unidade_nome}_{produto_escolhido}"
        )
        
        st.metric(label="Lucro Real Atual (%)", value=f"{lucro_real_val * 100:.2f}%")

else:
    st.error("Não foi possível carregar a planilha. Verifique a conexão ou os links.")
