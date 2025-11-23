import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="Eleições GB 2025", page_icon="🇬🇼", layout="wide")
ARQUIVO_EXCEL = 'votos_guine_bissau.xlsx'

# --- FUNÇÕES DE ARQUIVO ---
def carregar_dados():
    if os.path.exists(ARQUIVO_EXCEL):
        try:
            df = pd.read_excel(ARQUIVO_EXCEL)
            # Garante que as colunas existem mesmo se o arquivo for antigo
            if 'Círculo' not in df.columns: df = pd.DataFrame(columns=["Círculo", "Partido", "Quantidade"])
            return df
        except:
            return pd.DataFrame(columns=["Círculo", "Partido", "Quantidade"])
    else:
        return pd.DataFrame(columns=["Círculo", "Partido", "Quantidade"])

def salvar_no_excel(df):
    try:
        df.to_excel(ARQUIVO_EXCEL, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- LISTAS DE DADOS (ATUALIZADAS 2025) ---
circulos_oficiais = [
    "Círculo 05", 
    "Círculo 07", 
    "Círculo 10", 
    "Círculo 25"
]

# Lista expandida de partidos para 2025
partidos_2025 = [
    "PAIGC (PAI - Terra Ranka)",
    "MADEM G-15",
    "PRS (Partido da Renovação Social)",
    "PTG (Partido dos Trabalhadores)",
    "APU-PDGB",
    "PSTGB",
    "PND (Nova Democracia)",
    "UM (União para a Mudança)",
    "RGB-MB",
    "PUSD",
    "PSD",
    "PDS",
    "FREPASNA",
    "MDG",
    "Outros / Brancos / Nulos"
]

# --- INÍCIO DO APLICATIVO ---
st.title("🇬🇼 Apuração Eleitoral 2025 - Guiné-Bissau")
st.markdown("---")

# Carregar dados na memória (Session State)
if 'votos' not in st.session_state:
    st.session_state['votos'] = carregar_dados()

# --- BARRA LATERAL (LANÇAMENTO) ---
with st.sidebar.form(key='form_voto'):
    st.header("🗳️ Novo Lançamento")
    circulo_sel = st.selectbox("Selecione o Círculo", circulos_oficiais)
    partido_sel = st.selectbox("Selecione o Partido", partidos_2025)
    qtd_votos = st.number_input("Quantidade de Votos", min_value=1, value=1, step=1)
    
    btn_lancar = st.form_submit_button('💾 SALVAR NOVO VOTO')

if btn_lancar:
    # Cria novo registro
    novo_dado = pd.DataFrame({
        "Círculo": [circulo_sel],
        "Partido": [partido_sel],
        "Quantidade": [qtd_votos]
    })
    # Adiciona e Salva
    st.session_state['votos'] = pd.concat([st.session_state['votos'], novo_dado], ignore_index=True)
    if salvar_no_excel(st.session_state['votos']):
        st.success(f"✅ Voto registrado: {partido_sel} ({qtd_votos})")

# --- ÁREA PRINCIPAL ---

# Abas para separar Edição de Resultados
aba1, aba2 = st.tabs(["📝 TABELA DE DADOS (EDITAR/CORRIGIR)", "📊 RESULTADOS E GRÁFICOS"])

with aba1:
    st.subheader("Correção de Dados")
    st.info("💡 Dica: Clique duas vezes em qualquer célula abaixo para corrigir. Se quiser apagar uma linha, selecione-a e aperte DEL.")
    
    # EDITOR DE DADOS (A novidade!)
    if not st.session_state['votos'].empty:
        df_editado = st.data_editor(
            st.session_state['votos'],
            num_rows="dynamic",    # Permite adicionar/remover linhas
            use_container_width=True,
            key="editor_dados"
        )
        
        # Botão para salvar as edições manuais
        if st.button("💾 SALVAR CORREÇÕES DA TABELA"):
            st.session_state['votos'] = df_editado
            salvar_no_excel(df_editado)
            st.success("Tabela atualizada e salva no Excel!")
    else:
        st.warning("Nenhum voto lançado ainda.")

with aba2:
    if not st.session_state['votos'].empty:
        df = st.session_state['votos']
        
        # Cria a Tabela Cruzada (Matriz)
        # Mostra Círculos nas colunas e Partidos nas linhas
        tabela_matriz = df.pivot_table(
            index="Partido", 
            columns="Círculo", 
            values="Quantidade", 
            aggfunc="sum", 
            fill_value=0,
            margins=True, 
            margins_name="TOTAL GERAL"
        )
        
        st.subheader("Mapa Geral (Tabela Cruzada)")
        st.dataframe(tabela_matriz, use_container_width=True)
        
        st.markdown("---")
        
        # Gráficos
        col_graf1, col_graf2 = st.columns(2)
        
        # Dados somados apenas por partido (para o gráfico)
        total_partido = df.groupby("Partido")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
        
        with col_graf1:
            st.subheader("Ranking por Partido")
            fig_bar = px.bar(total_partido, x='Quantidade', y='Partido', orientation='h', text='Quantidade', title="Votos Totais")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_graf2:
            st.subheader("Distribuição (Pizza)")
            fig_pie = px.pie(total_partido, values='Quantidade', names='Partido', title="Percentual")
            st.plotly_chart(fig_pie, use_container_width=True)
            
    else:
        st.info("Vá na barra lateral para lançar os primeiros votos.")