import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURAÇÕES DO SISTEMA ---
st.set_page_config(page_title="CNE - Monitoramento 2025", page_icon="🇬🇼", layout="wide")
ARQUIVO_EXCEL = 'votos_guine_bissau.xlsx'

# --- DADOS OFICIAIS (MESAS POR CÍRCULO) ---
# Aqui definimos o total de mesas esperado para cada círculo
META_MESAS = {
    "Círculo 05": 189,
    "Círculo 07": 114,
    "Círculo 10": 154,
    "Círculo 25": 168
}

PARTIDOS_2025 = [
    "PAIGC (PAI - Terra Ranka)", "MADEM G-15", "PRS", "PTG", "APU-PDGB", 
    "PSTGB", "PND", "UM", "RGB-MB", "PUSD", "PSD", "PDS", 
    "FREPASNA", "MDG", "Outros / Brancos / Nulos"
]

# --- FUNÇÕES ---
def carregar_dados():
    colunas = ["Círculo", "Mesa", "Partido", "Quantidade"]
    if os.path.exists(ARQUIVO_EXCEL):
        try:
            df = pd.read_excel(ARQUIVO_EXCEL)
            # Garante que as colunas existam
            for col in colunas:
                if col not in df.columns: df[col] = "N/A" if col == "Mesa" else 0
            # Garante que a coluna Mesa seja texto (para não dar erro com mesa '01A')
            df['Mesa'] = df['Mesa'].astype(str)
            return df
        except:
            return pd.DataFrame(columns=colunas)
    else:
        return pd.DataFrame(columns=colunas)

def salvar_no_excel(df):
    try:
        df.to_excel(ARQUIVO_EXCEL, index=False)
        return True
    except:
        return False

# --- INÍCIO DA INTERFACE ---
st.title("🇬🇼 Painel de Controle Eleitoral - Guiné-Bissau")
st.markdown("**Status da Apuração:** Acompanhamento em Tempo Real das Mesas de Voto")

if 'votos' not in st.session_state:
    st.session_state['votos'] = carregar_dados()

df = st.session_state['votos']

# --- BARRA SUPERIOR (RESUMO DE PROGRESSO) ---
# Calcula quantas mesas únicas já foram lançadas por círculo
if not df.empty:
    mesas_apuradas = df.groupby("Círculo")["Mesa"].nunique()
else:
    mesas_apuradas = pd.Series()

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
metrics_cols = [col_kpi1, col_kpi2, col_kpi3, col_kpi4]

# Exibe os cartões de progresso no topo
for i, (circulo, total_previsto) in enumerate(META_MESAS.items()):
    ja_contadas = mesas_apuradas.get(circulo, 0)
    percentual = (ja_contadas / total_previsto) * 100 if total_previsto > 0 else 0
    pendentes = total_previsto - ja_contadas
    
    with metrics_cols[i]:
        st.metric(
            label=f"{circulo}",
            value=f"{ja_contadas}/{total_previsto} Mesas",
            delta=f"{percentual:.1f}% Concluído"
        )
        if pendentes > 0:
            st.warning(f"Faltam {pendentes} mesas")
        else:
            st.success("100% Finalizado!")

st.markdown("---")

# --- ÁREA LATERAL (LANÇAMENTO) ---
with st.sidebar.form(key='form_lancamento'):
    st.header("🗳️ Recebimento de Atas")
    
    circulo_sel = st.selectbox("Círculo Eleitoral", list(META_MESAS.keys()))
    
    # Mostra quantas mesas tem o círculo selecionado para ajudar o digitador
    total_deste_circulo = META_MESAS[circulo_sel]
    st.caption(f"ℹ️ Este círculo possui {total_deste_circulo} mesas.")
    
    mesa_input = st.text_input("Número da Mesa", placeholder="Ex: 01, 150, 05A")
    partido_sel = st.selectbox("Partido", PARTIDOS_2025)
    qtd_votos = st.number_input("Votos", min_value=0, step=1)
    
    btn_salvar = st.form_submit_button("💾 SALVAR DADOS")

if btn_salvar:
    if mesa_input == "":
        st.error("⚠️ Erro: Informe o número da Mesa.")
    else:
        novo = pd.DataFrame([{
            "Círculo": circulo_sel,
            "Mesa": mesa_input.upper(),
            "Partido": partido_sel,
            "Quantidade": qtd_votos
        }])
        st.session_state['votos'] = pd.concat([st.session_state['votos'], novo], ignore_index=True)
        salvar_no_excel(st.session_state['votos'])
        st.success(f"✅ Voto computado: {partido_sel} na Mesa {mesa_input} ({circulo_sel})")
        st.rerun() # Atualiza a tela imediatamente para mudar os gráficos

# --- ABAS DE RESULTADO ---
tab1, tab2, tab3 = st.tabs(["📊 TOTAL NACIONAL", "📍 DETALHE POR MESA", "📝 AUDITORIA"])

# 1. VISÃO NACIONAL
with tab1:
    if not df.empty:
        total_nac = df.groupby("Partido")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.dataframe(total_nac, hide_index=True, use_container_width=True)
        with c2:
            fig = px.bar(total_nac, x='Quantidade', y='Partido', orientation='h', text='Quantidade', title="Ranking Nacional")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando início da apuração.")

# 2. DETALHE POR MESA (MATRIZ)
with tab2:
    st.subheader("Mapa de Calor das Mesas")
    filtro_c = st.selectbox("Selecione o Círculo para ver as Mesas:", list(META_MESAS.keys()))
    
    df_c = df[df["Círculo"] == filtro_c]
    
    if not df_c.empty:
        # Tabela Cruzada: Linha=Partido, Coluna=Número da Mesa
        piv = df_c.pivot_table(index="Partido", columns="Mesa", values="Quantidade", aggfunc="sum", fill_value=0, margins=True, margins_name="TOTAL")
        st.write(f"Resultados detalhados: {filtro_c}")
        st.dataframe(piv, use_container_width=True)
    else:
        st.warning(f"Nenhuma mesa lançada ainda no {filtro_c}.")

# 3. EDIÇÃO
with tab3:
    st.info("Para corrigir um erro, altere o valor na tabela abaixo e clique em Salvar.")
    if not df.empty:
        df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="edit_grid")
        if st.button("💾 CONFIRMAR CORREÇÕES"):
            st.session_state['votos'] = df_edit
            salvar_no_excel(df_edit)
            st.success("Base de dados corrigida!")
            st.rerun()