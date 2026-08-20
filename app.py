import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import glob
import os
from datetime import datetime

# =====================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN SYSTEM ESTAPAR
# =====================================================================
st.set_page_config(
    page_title="ESTAPAR | Dashboard Executivo de Operações & NFs",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Estável e Limpa
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8fafc;
    }
    
    /* Sidebar Estapar */
    [data-testid="stSidebar"] {
        background-color: #002b49;
        color: #ffffff;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Header Corporativo */
    .estapar-header {
        background: linear-gradient(90deg, #002b49 0%, #00406c 100%);
        padding: 20px 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 43, 73, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .estapar-header h1 {
        color: #ffffff !important;
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }
    .estapar-header p {
        color: #cbd5e1 !important;
        margin: 4px 0 0 0;
        font-size: 13px;
    }
    
    /* Cards de KPI Executivos */
    .kpi-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px 20px;
        border-left: 5px solid #008753;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    .kpi-title {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 24px;
        color: #002b49;
        font-weight: 700;
        line-height: 1.2;
    }
    .kpi-subtext {
        font-size: 12px;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Badges de Status */
    .badge-green {
        background-color: #dcfce7; color: #15803d; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 12px; display: inline-block;
    }
    .badge-yellow {
        background-color: #fef9c3; color: #a16207; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 12px; display: inline-block;
    }
    .badge-red {
        background-color: #fee2e2; color: #b91c1c; font-weight: 700; padding: 4px 10px; border-radius: 20px; font-size: 12px; display: inline-block;
    }
    
    /* Ajustes em Botões */
    .stButton>button {
        background-color: #008753 !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100%;
        padding: 8px 16px !important;
    }
    .stButton>button:hover {
        background-color: #00663f !important;
    }
</style>
""", unsafe_allow_html=True)

# Logo Handler com Fallback seguro
LOCAL_LOGO_PATH = "assets/estapar_logo.png"

if os.path.exists(LOCAL_LOGO_PATH):
    st.sidebar.image(LOCAL_LOGO_PATH, use_container_width=True)
else:
    st.sidebar.markdown("## 🚗 **ESTAPAR**")

st.sidebar.markdown("---")

# =====================================================================
# 2. ENGINE DE CARREGAMENTO & TRATAMENTO DE DADOS MULTI-PLANILHA
# =====================================================================
@st.cache_data(ttl=300)
def carregar_e_tratar_dados(caminho_pasta="."):
    arquivos_excel = glob.glob(os.path.join(caminho_pasta, "*.xlsx")) + glob.glob(os.path.join(caminho_pasta, "*.xls"))
    
    if not arquivos_excel:
        return pd.DataFrame()

    lista_dfs = []
    
    for arquivo in arquivos_excel:
        nome_arquivo = os.path.basename(arquivo)
        try:
            excel_file = pd.ExcelFile(arquivo)
            for aba in excel_file.sheet_names:
                df_aba = pd.read_excel(excel_file, sheet_name=aba)
                if not df_aba.empty:
                    df_aba['Origem_Arquivo'] = nome_arquivo
                    df_aba['Origem_Aba'] = aba
                    lista_dfs.append(df_aba)
        except Exception:
            pass

    if not lista_dfs:
        return pd.DataFrame()

    df_raw = pd.concat(lista_dfs, ignore_index=True)

    # Padronização e Normalização de Colunas
    cols_map = {}
    for col in df_raw.columns:
        c_lower = str(col).lower().strip()
        if 'fornecedor' in c_lower or 'razao' in c_lower or 'razão' in c_lower:
            cols_map[col] = 'Fornecedor'
        elif 'valor' in c_lower or 'total' in c_lower or 'montante' in c_lower:
            cols_map[col] = 'Valor_Total'
        elif 'emiss' in c_lower or 'data' in c_lower:
            cols_map[col] = 'Data_Emissao'
        elif 'diverg' in c_lower or 'inconsist' in c_lower or 'erro' in c_lower:
            cols_map[col] = 'Divergencia'
        elif 'numero' in c_lower or 'número' in c_lower or 'nf' in c_lower or c_lower == 'id':
            cols_map[col] = 'Numero_NF'

    df_clean = df_raw.rename(columns=cols_map)
    df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

    # Tratamento de Colunas Essenciais
    if 'Fornecedor' not in df_clean.columns:
        df_clean['Fornecedor'] = 'Não Informado'
    else:
        if isinstance(df_clean['Fornecedor'], pd.DataFrame):
            df_clean['Fornecedor'] = df_clean['Fornecedor'].iloc[:, 0]
        df_clean['Fornecedor'] = df_clean['Fornecedor'].fillna('Não Informado').astype(str).str.strip()

    if 'Valor_Total' in df_clean.columns:
        if isinstance(df_clean['Valor_Total'], pd.DataFrame):
            df_clean['Valor_Total'] = df_clean['Valor_Total'].iloc[:, 0]
        df_clean['Valor_Limpo'] = (
            df_clean['Valor_Total']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df_clean['Valor_Limpo'] = pd.to_numeric(df_clean['Valor_Limpo'], errors='coerce').fillna(0.0)
    else:
        df_clean['Valor_Limpo'] = 0.0

    if 'Data_Emissao' in df_clean.columns:
        if isinstance(df_clean['Data_Emissao'], pd.DataFrame):
            df_clean['Data_Emissao'] = df_clean['Data_Emissao'].iloc[:, 0]
        df_clean['Data_Emissao'] = pd.to_datetime(df_clean['Data_Emissao'], dayfirst=True, errors='coerce')
        df_clean['Ano_Mes'] = df_clean['Data_Emissao'].dt.to_period('M').astype(str).replace('NaT', 'S/D')
        df_clean['Ano'] = df_clean['Data_Emissao'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'S/D')
    else:
        df_clean['Data_Emissao'] = pd.NaT
        df_clean['Ano_Mes'] = 'S/D'
        df_clean['Ano'] = 'S/D'

    if 'Divergencia' in df_clean.columns:
        if isinstance(df_clean['Divergencia'], pd.DataFrame):
            df_clean['Divergencia'] = df_clean['Divergencia'].iloc[:, 0]
        df_clean['Tem_Divergencia'] = (
            df_clean['Divergencia'].notnull() & 
            (df_clean['Divergencia'].astype(str).str.strip().str.lower() != 'sem divergência') &
            (df_clean['Divergencia'].astype(str).str.strip() != '') &
            (df_clean['Divergencia'].astype(str).str.strip() != 'nan')
        )
        df_clean['Divergencia_Classificada'] = np.where(
            df_clean['Tem_Divergencia'], 
            df_clean['Divergencia'].astype(str).str.strip(), 
            'Sem Divergência'
        )
    else:
        df_clean['Tem_Divergencia'] = False
        df_clean['Divergencia_Classificada'] = 'Sem Divergência'

    return df_clean

df_master = carregar_e_tratar_dados()

if df_master.empty:
    st.error("Nenhuma planilha válida foi encontrada na pasta. Adicione os arquivos .xlsx ou .xls para continuar.")
    st.stop()

# =====================================================================
# 3. SISTEMA DE FILTROS INTELIGENTE
# =====================================================================
st.sidebar.title("⚙️ Filtros Operacionais")

def reset_filtros():
    for key in list(st.session_state.keys()):
        if key.startswith("fltr_"):
            st.session_state[key] = ["Todos"]

if st.sidebar.button("🔄 Restaurar Filtros Padrão"):
    reset_filtros()

anos_disponiveis = ["Todos"] + sorted([a for a in df_master['Ano'].unique() if a != 'S/D'], reverse=True)
sel_ano = st.sidebar.multiselect("Ano de Emissão:", anos_disponiveis, default=["Todos"], key="fltr_ano")

meses_disponiveis = ["Todos"] + sorted([m for m in df_master['Ano_Mes'].unique() if m != 'S/D'], reverse=True)
sel_mes = st.sidebar.multiselect("Mês/Ano de Referência:", meses_disponiveis, default=["Todos"], key="fltr_mes")

fornecedores_unicos = ["Todos"] + sorted(df_master['Fornecedor'].unique().tolist())
sel_fornecedor = st.sidebar.multiselect("Fornecedor:", fornecedores_unicos, default=["Todos"], key="fltr_fornecedor")

div_unicas = ["Todos"] + sorted(df_master['Divergencia_Classificada'].unique().tolist())
sel_div = st.sidebar.multiselect("Classificação da Divergência:", div_unicas, default=["Todos"], key="fltr_div")

# Aplicação Integrada dos Filtros ao DataFrame
df_filtrado = df_master.copy()

if "Todos" not in sel_ano and len(sel_ano) > 0:
    df_filtrado = df_filtrado[df_filtrado['Ano'].isin(sel_ano)]

if "Todos" not in sel_mes and len(sel_mes) > 0:
    df_filtrado = df_filtrado[df_filtrado['Ano_Mes'].isin(sel_mes)]

if "Todos" not in sel_fornecedor and len(sel_fornecedor) > 0:
    df_filtrado = df_filtrado[df_filtrado['Fornecedor'].isin(sel_fornecedor)]

if "Todos" not in sel_div and len(sel_div) > 0:
    df_filtrado = df_filtrado[df_filtrado['Divergencia_Classificada'].isin(sel_div)]

# =====================================================================
# 4. CABEÇALHO EXECUTIVO E KPIS PRINCIPAIS
# =====================================================================
st.markdown(f"""
<div class="estapar-header">
    <div>
        <h1>ESTAPAR — Gestão de Operações & Entrada de NFs</h1>
        <p>Monitoramento de Conformidade Fiscal, Retrabalho e Performance de Fornecedores</p>
    </div>
    <div style="text-align: right;">
        <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            🟢 Base Sincronizada: {len(df_filtrado):,} registros
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Cálculo dos Indicadores Globais
total_nfs = len(df_filtrado)
valor_total_bruto = df_filtrado['Valor_Limpo'].sum()
com_div = df_filtrado['Tem_Divergencia'].sum()
sem_div = total_nfs - com_div

pct_ftt = (sem_div / total_nfs * 100) if total_nfs > 0 else 0.0
pct_retrabalho = (com_div / total_nfs * 100) if total_nfs > 0 else 0.0

if pct_retrabalho < 18:
    status_badge = '<span class="badge-green">🟢 PROCESSO SAUDÁVEL</span>'
elif pct_retrabalho <= 25:
    status_badge = '<span class="badge-yellow">🟡 REQUER ATENÇÃO</span>'
else:
    status_badge = '<span class="badge-red">🔴 CRÍTICO</span>'

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Total de NFs Processadas</div>
        <div class="kpi-value">{total_nfs:,}</div>
        <div class="kpi-subtext" style="color:#64748b;">Volume Total Filtrado</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Montante Total (R$)</div>
        <div class="kpi-value">R$ {valor_total_bruto:,.2f}</div>
        <div class="kpi-subtext" style="color:#64748b;">Valor Bruto de Entradas</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Conformidade (FTT)</div>
        <div class="kpi-value" style="color: #008753;">{pct_ftt:.1f}%</div>
        <div class="kpi-subtext" style="color:#15803d;">Primeira Passagem Direta</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Taxa de Retrabalho</div>
        <div class="kpi-value" style="color: #b91c1c;">{pct_retrabalho:.1f}%</div>
        <div class="kpi-subtext" style="color:#b91c1c;">{com_div:,} NFs c/ Divergência</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Saúde Operacional</div>
        <div style="margin-top: 8px;">{status_badge}</div>
        <div class="kpi-subtext" style="color:#64748b;">Métrica Consolidada</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 5. NAVEGAÇÃO PRINCIPAL (ABAS DA APLICAÇÃO)
# =====================================================================
tab_names = [
    "🏠 Visão Geral & IA", 
    "🔎 Divergências (Pareto)", 
    "🏢 Fornecedores", 
    "📈 Evolução Temporal", 
    "🎯 Plano de Ação", 
    "⚙️ Base de Dados Integração"
]
t_geral, t_div, t_forn, t_evol, t_acao, t_data = st.tabs(tab_names)

# ---------------------------------------------------------------------
# ABA 1: VISÃO GERAL & DIAGNÓSTICO IA
# ---------------------------------------------------------------------
with t_geral:
    st.subheader("💡 Diagnóstico Estratégico do Analista Virtual de Operações")
    
    st.info(f"""
    * **[DADO REVELADO]:** A amostra analisada contém **{total_nfs:,} NFs** somando **R$ {valor_total_bruto:,.2f}**. Deste total, **{pct_retrabalho:.1f}% ({com_div} NFs)** apresentaram divergências exigindo tratamento ou refatoração do Pedido de Compras.
    * **[INTERPRETAÇÃO DE CAUSA]:** As desconformidades concentram-se na ausência de inclusão antecipada da tag `<xPed>` pelos fornecedores recorrentes e em inconsistências na Conta Integrador Compras do ERP.
    * **[RECOMENDAÇÃO PRÁTICA]:** Estabelecer trava de pré-validação na entrada da API para parceiros com taxa de retrabalho superior a 20%.
    """)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Distribuição de Processamento (FTT vs Retrabalho)**")
        df_pie = pd.DataFrame({
            'Status': ['Sem Divergência (FTT)', 'Com Divergência'],
            'Qtd': [sem_div, com_div]
        })
        fig_pie = px.pie(
            df_pie, names='Status', values='Qtd', hole=0.45,
            color='Status', color_discrete_map={'Sem Divergência (FTT)': '#008753', 'Com Divergência': '#dc2626'}
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("**Top 5 Fornecedores por Volume Financeiro**")
        top_val_forn = df_filtrado.groupby('Fornecedor')['Valor_Limpo'].sum().reset_index().sort_values('Valor_Limpo', ascending=False).head(5)
        fig_top_val = px.bar(
            top_val_forn, x='Valor_Limpo', y='Fornecedor', orientation='h', text_auto='.2s',
            color_discrete_sequence=['#002b49']
        )
        fig_top_val.update_layout(
            yaxis=dict(autorange="reversed"), xaxis_title="Valor Total (R$)", yaxis_title="", 
            margin=dict(t=20, b=20, l=20, r=20), height=300
        )
        st.plotly_chart(fig_top_val, use_container_width=True)

# ---------------------------------------------------------------------
# ABA 2: DIVERGÊNCIAS (PARETO)
# ---------------------------------------------------------------------
with t_div:
    st.subheader("🔎 Análise de Divergências e Diagrama de Pareto")
    
    df_div_only = df_filtrado[df_filtrado['Tem_Divergencia']]
    
    if df_div_only.empty:
        st.success("🎉 Nenhuma divergência encontrada no recorte de dados selecionado!")
    else:
        div_counts = df_div_only['Divergencia_Classificada'].value_counts().reset_index()
        div_counts.columns = ['Motivo', 'Quantidade']
        div_counts['Pct'] = (div_counts['Quantidade'] / div_counts['Quantidade'].sum()) * 100
        div_counts['Pct_Acumulado'] = div_counts['Pct'].cumsum()

        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=div_counts['Motivo'], y=div_counts['Quantidade'],
            name="Qtd Divergências", marker_color="#002b49"
        ))
        fig_pareto.add_trace(go.Scatter(
            x=div_counts['Motivo'], 
            y=div_counts['Pct_Acumulado'],
            name="% Acumulado", 
            yaxis="y2", 
            mode="lines+markers+text",
            line=dict(color="#ea580c"),
            marker=dict(color="#ea580c"),
            text=[f"{v:.1f}%" for v in div_counts['Pct_Acumulado']], 
            textposition="top center"
        ))
        fig_pareto.update_layout(
            title="Pareto de Causa Raiz de Divergências",
            yaxis=dict(title="Quantidade de NFs"),
            yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110]),
            legend=dict(x=0.01, y=1.15, orientation="h"),
            margin=dict(t=40, b=20, l=20, r=20), height=400
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

        top_3_pct = div_counts.head(3)['Pct'].sum()
        st.warning(f"⚡ **Regra de Impacto 80/20:** As 3 principais razões respondem por **{top_3_pct:.1f}%** de todo o retrabalho operacional.")

# ---------------------------------------------------------------------
# ABA 3: FORNECEDORES (Sem dependência de matplotlib / background_gradient)
# ---------------------------------------------------------------------
with t_forn:
    st.subheader("🏢 Ranking e Performance da Base de Fornecedores")
    
    forn_df = df_filtrado.groupby('Fornecedor').agg(
        Total_NFs=('Valor_Limpo', 'count'),
        NFs_Divergentes=('Tem_Divergencia', 'sum'),
        Valor_Total=('Valor_Limpo', 'sum')
    ).reset_index()
    
    forn_df['Pct_Retrabalho'] = (forn_df['NFs_Divergentes'] / forn_df['Total_NFs']) * 100
    forn_df = forn_df.sort_values(by='Total_NFs', ascending=False)

    st.dataframe(
        forn_df.style.format({
            'Total_NFs': '{:,}',
            'NFs_Divergentes': '{:,}',
            'Valor_Total': 'R$ {:,.2f}',
            'Pct_Retrabalho': '{:.2f}%'
        }),
        use_container_width=True, height=400
    )

# ---------------------------------------------------------------------
# ABA 4: EVOLUÇÃO TEMPORAL
# ---------------------------------------------------------------------
with t_evol:
    st.subheader("📈 Evolução Histórica e Tendência MoM")
    
    df_temp = df_filtrado[df_filtrado['Ano_Mes'] != 'S/D']
    
    if df_temp.empty:
        st.warning("Não há informações temporais suficientes para exibir a evolução.")
    else:
        monthly_hist = df_temp.groupby('Ano_Mes').agg(
            Total_NFs=('Valor_Limpo', 'count'),
            Divergentes=('Tem_Divergencia', 'sum')
        ).reset_index().sort_values('Ano_Mes')
        
        monthly_hist['Pct_Retrabalho'] = (monthly_hist['Divergentes'] / monthly_hist['Total_NFs']) * 100
        monthly_hist['Pct_FTT'] = 100 - monthly_hist['Pct_Retrabalho']

        fig_evol = go.Figure()
        fig_evol.add_trace(go.Bar(
            x=monthly_hist['Ano_Mes'], 
            y=monthly_hist['Total_NFs'], 
            name="Volume NFs", 
            marker_color="#cbd5e1"
        ))
        fig_evol.add_trace(go.Scatter(
            x=monthly_hist['Ano_Mes'], 
            y=monthly_hist['Pct_Retrabalho'], 
            name="% Retrabalho", 
            yaxis="y2", 
            mode="lines+markers",
            line=dict(color="#dc2626", width=3)
        ))
        fig_evol.add_trace(go.Scatter(
            x=monthly_hist['Ano_Mes'], 
            y=monthly_hist['Pct_FTT'], 
            name="% FTT", 
            yaxis="y2", 
            mode="lines+markers",
            line=dict(color="#008753", width=3, dash="dash")
        ))

        fig_evol.update_layout(
            title="Volume de Entradas vs Taxa de Conformidade MoM",
            yaxis=dict(title="Volume de NFs"),
            yaxis2=dict(title="Percentual (%)", overlaying="y", side="right", range=[0, 100]),
            legend=dict(x=0.01, y=1.15, orientation="h"),
            margin=dict(t=40, b=20, l=20, r=20), height=400
        )
        st.plotly_chart(fig_evol, use_container_width=True)

# ---------------------------------------------------------------------
# ABA 5: PLANO DE AÇÃO
# ---------------------------------------------------------------------
with t_acao:
    st.subheader("🎯 Matriz Priorizada de Melhorias Contínuas")
    
    st.markdown("""
    | Prioridade | Oportunidade / Causa Raiz | Impacto Estimado | Ação Recomendada | Responsável |
    | :---: | :--- | :---: | :--- | :--- |
    | 🔴 **Alta** | **Exigência da Tag `<xPed>` no Portal** | **56,5%** | Ativar trava de pré-validação do pedido no portal de recepção fiscal. | TI / Fiscal |
    | 🔴 **Alta** | **Ajuste da Conta Integrador Compras** | **45,9%** | Recalibrar robô de integração ERP Oracle para evitar pedidos sem código. | Suporte ERP |
    | 🟡 **Média** | **Saneamento Cadastral de Fornecedores** | **9,5%** | Validação automatizada de status do CNPJ e Inscrição Estadual. | Suprimentos |
    """)

# ---------------------------------------------------------------------
# ABA 6: BASE DE DADOS & INTEGRAÇÃO
# ---------------------------------------------------------------------
with t_data:
    st.subheader("⚙️ Dados Consolidados & Auditoria")
    
    c_d1, c_d2 = st.columns([3, 1])
    with c_d1:
        st.markdown(f"**Registros Exibidos:** {len(df_filtrado):,} de {len(df_master):,}")
    with c_d2:
        csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Dados (CSV)",
            data=csv_data,
            file_name=f"export_estapar_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    st.dataframe(df_filtrado, use_container_width=True, height=450)
