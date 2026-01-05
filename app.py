import streamlit as st
import pandas as pd
import re

# Configuração da página
st.set_page_config(page_title="Simulador de Margem Pro_02", layout="wide")

st.markdown("<h1 style='text-align: center;'>Simulador de Margem de Lucro Pro</h1>", unsafe_allow_html=True)

# 1. Configurações
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

# 2. Função de Limpeza
def limpar_valor(valor):
    if pd.isna(valor) or valor == "": return 0.0
    if isinstance(valor, str):
        limpo = valor.replace("R$", "").strip()
        if "," in limpo and "." in limpo: limpo = limpo.replace(".", "").replace(",", ".")
        elif "," in limpo: limpo = limpo.replace(",", ".")
        limpo = re.sub(r'[^0-9.-]', '', limpo)
        try: return float(limpo)
        except: return 0.0
    return float(valor)

# 3. Seleção de Mercado e Carregamento
col_h1, col_h2 = st.columns(2)

with col_h1:
    unidade_nome = st.selectbox("Selecione o Mercado:", list(config_unidades.keys()))
    info_unidade = config_unidades[unidade_nome]

@st.cache_data(ttl=60)
def carregar_dados(url):
    try:
        # Lendo colunas 2, 3 e 4 (C, D, E)
        df = pd.read_csv(url, usecols=[2, 3, 4], names=["Produto", "Custo_Ultima", "Venda_Atual"], skiprows=2)
        df["Produto"] = df["Produto"].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return None

df = carregar_dados(info_unidade["url"])

if df is not None:
    lista_produtos = sorted(df["Produto"].unique().tolist())
    
    with col_h2:
        produto_escolhido = st.selectbox("Selecione o Produto:", lista_produtos)
    
    # Busca os dados específicos
    dados_item = df[df["Produto"] == produto_escolhido]
    
    if not dados_item.empty:
        c_base = limpar_valor(dados_item.iloc[0]["Custo_Ultima"])
        v_base = limpar_valor(dados_item.iloc[0]["Venda_Atual"])
    else:
        c_base, v_base = 0.0, 0.0

    st.divider()

    # Layout
    col_sim, col_real = st.columns(2)

    # --- LÓGICA DE CHAVE ÚNICA ---
    # Criamos um sufixo que muda sempre que o mercado ou produto muda
    sufixo_chave = f"{unidade_nome}_{produto_escolhido}"

    with col_sim:
        st.subheader("Simulador (Editável)")
        # Estes campos RESETAM quando o produto muda, mas permitem edição manual
        p_custo_sim = st.number_input("Custo Simulado (R$)", value=c_base, step=0.01, format="%.2f", key=f"sim_c_{sufixo_chave}")
        v_venda_sim = st.number_input("Venda Simulada (R$)", value=v_base, step=0.01, format="%.2f", key=f"sim_v_{sufixo_chave}")
        
        margem_sim = (v_venda_sim - (v_venda_sim * info_unidade["custo_op"]) - p_custo_sim) / v_venda_sim if v_venda_sim > 0 else 0
        st.metric("Margem Simulada", f"{margem_sim*100:.2f}%")

    with col_real:
        st.subheader("Valores Reais (Travados)")
        # Estes campos são desativados e ATUALIZAM automaticamente pela chave única
        st.number_input("Custo Atual (Planilha)", value=c_base, disabled=True, format="%.2f", key=f"real_c_{sufixo_chave}")
        st.number_input("Venda Atual (Planilha)", value=v_base, disabled=True, format="%.2f", key=f"real_v_{sufixo_chave}")
        
        margem_real = (v_base - (v_base * info_unidade["custo_op"]) - c_base) / v_base if v_base > 0 else 0
        st.metric("Margem Real", f"{margem_real*100:.2f}%")
