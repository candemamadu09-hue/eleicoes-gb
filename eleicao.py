import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Eleições GB - Seguro", page_icon="🇬🇼", layout="wide")
ARQUIVO_EXCEL = 'votos_guine_bissau.xlsx'

# --- FUNÇÕES DE BANCO DE DADOS (EXCEL) ---
def carregar_dados():
    if os.path.exists(ARQUIVO_EXCEL):
        try:
            return pd.read_excel(ARQUIVO_EXCEL)
        except:
            return pd.DataFrame(columns=["Círculo", "Partido", "Quantidade"])
    else:
        return pd.DataFrame(columns=["Círculo", "Partido", "Quantidade"])

def salvar_no_excel(df):
    df.to_excel(ARQUIVO_EXCEL, index=False)

# --- INÍCIO DO APP ---
st.title("🇬🇼 Sistema de Contagem (Com Salvamento Automático)")
st.markdown("---")

# Carrega os dados do Excel ao abrir o app
if 'votos' not in st.session_state:
    st.session_state['votos'] = carregar_dados()

# Listas
circulos = ["Círculo 24 (Bissau - SAB)", "Círculo 07 (Bafatá)", "Círculo 10 (Gabú)", "Círculo 05 (Biombo)"]
partidos = ["PAIGC", "MADEM G-15", "PRS", "APU-PDGB", "PTG", "Outros"]

# --- BARRA LATERAL (VOTAÇÃO) ---
with st.sidebar.form(key='form_voto'):
    st.header("🗳️ Inserir Urna")
    circulo = st.selectbox("Círculo Eleitoral", circulos)
    partido = st.selectbox("Partido", partidos)
    qtd = st.number_input("Quantidade de Votos", min_value=1, value=1)
    
    submit = st.form_submit_button('💾 SALVAR VOTOS')

if submit:
    # 1. Cria a nova linha
    novo_voto = pd.DataFrame({"Círculo":[circulo], "Partido":[partido], "Quantidade":[qtd]})
    
    # 2. Adiciona ao estado atual
    st.session_state['votos'] = pd.concat([st.session_state['votos'], novo_voto], ignore_index=True)
    
    # 3. GRAVA NO ARQUIVO EXCEL IMEDIATAMENTE
    salvar_no_excel(st.session_state['votos'])
    
    st.success(f"✅ Salvo no Excel com sucesso! ({qtd} votos para {partido})")

# --- PAINEL DE RESULTADOS ---
if not st.session_state['votos'].empty:
    df = st.session_state['votos']
    
    # Agrupamentos
    total_geral = df["Quantidade"].sum()
    por_partido = df.groupby("Partido")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Total de Votos Apurados", total_geral)
        st.subheader("Ranking")
        st.dataframe(por_partido, use_container_width=True)
        
    with col2:
        st.subheader("Gráfico Nacional")
        fig = px.bar(por_partido, x='Partido', y='Quantidade', color='Partido', text='Quantidade')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption(f"📁 Os dados estão sendo salvos automaticamente em: {os.getcwd()}\{ARQUIVO_EXCEL}")

else:
    st.info("👆 Comece a inserir os votos na barra lateral. Um arquivo Excel será criado automaticamente.")