import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURAÇÕES VISUAIS E DE SISTEMA ---
st.set_page_config(
    page_title="Central de Apuração 2025", 
    page_icon="🇬🇼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

ARQUIVO_EXCEL = 'votos_guine_bissau.xlsx'

# Cores oficiais e estilo
CORES_PARTIDOS = px.colors.qualitative.Bold

# --- 2. DADOS E METAS (CNE) ---
META_MESAS = {
    "Círculo 05": 189,
    "Círculo 07": 114,
    "Círculo 10": 154,
    "Círculo 25": 168
}

PARTIDOS = [
    "PAIGC (PAI - Terra Ranka)", "MADEM G-15", "PRS", "PTG", "APU-PDGB", 
    "PSTGB", "PND", "UM", "RGB-MB", "PUSD", "PSD", "PDS", 
    "FREPASNA", "MDG", "Outros / Brancos / Nulos"
]

# --- 3. FUNÇÕES ROBUSTAS ---
def carregar_dados():
    colunas = ["Círculo", "Mesa", "Partido", "Quantidade"]
    if os.path.exists(ARQUIVO_EXCEL):
        try:
            df = pd.read_excel(ARQUIVO_EXCEL)
            for col in colunas:
                if col not in df.columns: df[col] = 0 if col == "Quantidade" else "N/A"
            df['Mesa'] = df['Mesa'].astype(str).str.upper()
            return df
        except:
            return pd.DataFrame(columns=colunas)
    else:
        return pd.DataFrame(columns=colunas)

def salvar_no_excel(df):
    try:
        df.to_excel(ARQUIVO_EXCEL, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {e}")
        return False

# --- INÍCIO DO APP ---
if 'votos' not in st.session_state:
    st.session_state['votos'] = carregar_dados()

df = st.session_state['votos']

# --- BARRA LATERAL (LANÇAMENTO) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Flag_of_Guinea-Bissau.svg/320px-Flag_of_Guinea-Bissau.svg.png", width=100)
    st.title("Lançamento de Atas")
    st.markdown("---")
    
    # MODO RÁPIDO
    modo_rapido = st.checkbox("⚡ Modo Rápido (Travar Mesa)", value=True, help="Mantém o número da mesa preenchido para lançar vários partidos seguidos.")

    with st.form(key='form_principal', clear_on_submit=not modo_rapido):
        st.subheader("📝 Dados da Urna")
        
        # Recupera últimos valores se modo rápido estiver ativo
        default_circulo = st.session_state.get('last_circulo', list(META_MESAS.keys())[0])
        default_mesa = st.session_state.get('last_mesa', "") if modo_rapido else ""
        
        circulo_sel = st.selectbox("Círculo Eleitoral", list(META_MESAS.keys()), index=list(META_MESAS.keys()).index(default_circulo) if default_circulo in META_MESAS else 0)
        mesa_input = st.text_input("Nº da Mesa", value=default_mesa, placeholder="Ex: 01, 10A")
        
        st.markdown("---")
        partido_sel = st.selectbox("Partido / Candidato", PARTIDOS)
        qtd_votos = st.number_input("Votos Válidos", min_value=0, step=1)
        
        btn_lancar = st.form_submit_button("💾 CONFIRMAR LANÇAMENTO", type="primary")

    if btn_lancar:
        if not mesa_input:
            st.error("⚠️ O número da Mesa é obrigatório!")
        else:
            # Salva e Atualiza
            novo_reg = pd.DataFrame([{
                "Círculo": circulo_sel,
                "Mesa": mesa_input.upper(),
                "Partido": partido_sel,
                "Quantidade": qtd_votos
            }])
            st.session_state['votos'] = pd.concat([st.session_state['votos'], novo_reg], ignore_index=True)
            salvar_no_excel(st.session_state['votos'])
            
            # Guarda estado
            st.session_state['last_circulo'] = circulo_sel
            st.session_state['last_mesa'] = mesa_input
            
            st.success(f"✅ Voto computado com sucesso!")
            st.rerun()

# --- PAINEL DE INTELIGÊNCIA ---
st.title("🇬🇼 Central de Totalização Oficial 2025")

# KPI CARDS
if not df.empty:
    total_geral = df["Quantidade"].sum()
    mesas_unicas = df["Mesa"].nunique()
    # Partido Líder
    ranking_rapido = df.groupby("Partido")["Quantidade"].sum().sort_values(ascending=False)
    lider = ranking_rapido.index[0] if not ranking_rapido.empty else "-"
    votos_lider = ranking_rapido.iloc[0] if not ranking_rapido.empty else 0
else:
    total_geral = 0
    mesas_unicas = 0
    lider = "-"
    votos_lider = 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🗳️ Total de Votos", f"{total_geral:,.0f}")
kpi2.metric("📍 Mesas Processadas", mesas_unicas)
kpi3.metric("🏆 Liderança Atual", f"{lider} ({votos_lider})")

st.markdown("---")

# ABAS
aba_matriz, aba_graf, aba_dados = st.tabs(["📋 MATRIZ GERAL (NOVA)", "📊 GRÁFICOS", "🔧 AUDITORIA"])

# --- ABA 1: MATRIZ TOTALIZADORA (O QUE VOCÊ PEDIU) ---
with aba_matriz:
    st.subheader("Matriz de Apuração por Mesa")
    st.info("Esta tabela cruza todas as Mesas com todos os Partidos e calcula os totais automaticamente.")
    
    # Filtro de Círculo (Importante para não ficar gigante)
    filtro_c = st.selectbox("Filtrar Visualização por Círculo:", ["Todos"] + list(META_MESAS.keys()))
    
    if not df.empty:
        if filtro_c != "Todos":
            df_view = df[df["Círculo"] == filtro_c]
        else:
            df_view = df

        if not df_view.empty:
            # PIVOT TABLE COM TOTAIS (MARGINS=TRUE)
            # Isso cria a coluna 'All' e a linha 'All' que renomeamos para 'TOTAL'
            matriz = df_view.pivot_table(
                index="Partido", 
                columns="Mesa", 
                values="Quantidade", 
                aggfunc="sum", 
                fill_value=0,
                margins=True,             # <--- O SEGREDO: Cria totais de linha e coluna
                margins_name="TOTAL GERAL" # <--- Nome da coluna/linha de soma
            )
            
            # Ordenar para que o partido com mais votos fique no topo (exceto o Total Geral que deve ficar por último)
            # Removemos o TOTAL GERAL temporariamente para ordenar e depois colocamos de volta
            total_row = matriz.loc["TOTAL GERAL"]
            matriz_sem_total = matriz.drop("TOTAL GERAL")
            matriz_ordenada = matriz_sem_total.sort_values("TOTAL GERAL", ascending=False)
            matriz_final = pd.concat([matriz_ordenada, pd.DataFrame(total_row).T])
            
            st.dataframe(matriz_final, use_container_width=True, height=600)
            
            # Barra de Progresso deste círculo
            if filtro_c != "Todos":
                total_esperado = META_MESAS[filtro_c]
                mesas_feitas = df_view["Mesa"].nunique()
                prog = mesas_feitas / total_esperado if total_esperado > 0 else 0
                st.progress(prog, text=f"Status do {filtro_c}: {mesas_feitas} de {total_esperado} mesas apuradas.")
        else:
            st.warning("Sem dados para este filtro.")
    else:
        st.info("Aguardando lançamento de dados.")

# --- ABA 2: GRÁFICOS ---
with aba_graf:
    col1, col2 = st.columns([2,1])
    if not df.empty:
        # Dados agrupados
        total_partido = df.groupby("Partido")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
        
        with col1:
            st.subheader("Distribuição Nacional")
            fig = px.bar(total_partido, x='Partido', y='Quantidade', color='Partido', text='Quantidade', color_discrete_sequence=CORES_PARTIDOS)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Ranking Percentual")
            fig_pie = px.pie(total_partido, values='Quantidade', names='Partido', hole=0.4, color_discrete_sequence=CORES_PARTIDOS)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.write("Gráficos aparecerão após o primeiro voto.")

# --- ABA 3: AUDITORIA E EDIÇÃO ---
with aba_dados:
    st.subheader("Editor de Base de Dados")
    st.markdown("Use esta tabela para **corrigir** erros de digitação ou **excluir** lançamentos duplicados.")
    
    if not df.empty:
        df_editavel = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_principal"
        )
        
        if st.button("💾 SALVAR CORREÇÕES", type="primary"):
            st.session_state['votos'] = df_editavel
            salvar_no_excel(df_editavel)
            st.success("Banco de dados atualizado com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum registro encontrado.")