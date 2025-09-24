import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Configurações do Painel ---
st.set_page_config(
    page_title="Dashboard de Dívidas de Precatórios do TJPE",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Dashboard de Dívidas de Precatórios do TJPE")

# --- Leitura e Limpeza dos Dados ---
# @st.cache_data armazena os dados em cache para o painel carregar mais rápido
@st.cache_data
def load_data(file_path):
    try:
        # Carrega a planilha Excel
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{file_path}' não encontrado. Verifique se o nome e o caminho estão corretos.")
        return None

    # Procura a coluna de saldo de forma flexível
    saldo_col = None
    for col in df.columns:
        if re.search(r'saldo', col, re.IGNORECASE):
            saldo_col = col
            break
            
    if saldo_col is None:
        st.error(f"Erro: Não foi encontrada uma coluna de saldo na planilha. As colunas disponíveis são: {list(df.columns)}")
        return None

    # Renomeia a coluna encontrada para padronizar
    df = df.rename(columns={saldo_col: 'SALDO ATUALIZADO'})
    
    # Garante que 'SALDO ATUALIZADO' é um número
    df['SALDO ATUALIZADO'] = pd.to_numeric(df['SALDO ATUALIZADO'], errors='coerce')
    return df

# NOME EXATO DO SEU ARQUIVO .xlsx
file_name = 'Estudo da dívia em Agosto-25.xlsx'
df = load_data(file_name)

if df is not None:
    # --- Filtros na Barra Lateral ---
    st.sidebar.header("Filtros Principais")
    ente_selecionado = st.sidebar.selectbox("Selecione o Ente Devedor", ['Todos'] + sorted(df['ENTE'].unique()))
    orcamento_selecionado = st.sidebar.selectbox("Selecione o Orçamento", ['Todos'] + sorted(df['ORÇAMENTO'].unique()))
    situacao_selecionada = st.sidebar.selectbox("Selecione a Situação", ['Todos'] + df['SITUAÇÃO'].unique())

    df_filtrado = df.copy()
    if ente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ENTE'] == ente_selecionado]
    if orcamento_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ORÇAMENTO'] == orcamento_selecionado]
    if situacao_selecionada != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['SITUAÇÃO'] == situacao_selecionada]

    # --- Área de Destaque para Processo (Busca) ---
    st.subheader("Informações Detalhadas do Processo")
    processo_selecionado = st.sidebar.text_input("Buscar por Processo (Digite o nº):")
    if processo_selecionado:
        processo_info = df[df['PROCESSO'].astype(str).str.contains(processo_selecionado, case=False, na=False)]
        if not processo_info.empty:
            st.write(processo_info[['ENTE', 'PROCESSO', 'ORÇAMENTO', 'SALDO ATUALIZADO']].iloc[0])
        else:
            st.write("Nenhum processo encontrado com esse número.")

    # --- Widgets e Gráficos Principais ---
    st.subheader("Análises da Dívida")

    # Gráfico de Participação na Dívida Total
    total_por_ente = df.groupby('ENTE')['SALDO ATUALIZADO'].sum().reset_index()
    total_geral = df['SALDO ATUALIZADO'].sum()
    total_por_ente['% Participação'] = (total_por_ente['SALDO ATUALIZADO'] / total_geral) * 100
    fig_participacao = px.pie(total_por_ente, values='SALDO ATUALIZADO', names='ENTE',
                             title='Participação dos Entes na Dívida Total',
                             hover_data=['% Participação'], labels={'SALDO ATUALIZADO':'Saldo Total'})
    st.plotly_chart(fig_participacao)

    # Gráfico de Evolução da Dívida do Ente Selecionado
    if ente_selecionado != 'Todos':
        evolucao_divida = df[df['ENTE'] == ente_selecionado].groupby('ORÇAMENTO')['SALDO ATUALIZADO'].sum().reset_index()
        fig_evolucao = px.line(evolucao_divida, x='ORÇAMENTO', y='SALDO ATUALIZADO',
                              title=f'Evolução da Dívida de {ente_selecionado} por Ano')
        st.plotly_chart(fig_evolucao)

    # Gráfico de Proporção da Dívida por Situação
    proporcao_situacao = df_filtrado.groupby('SITUAÇÃO')['SALDO ATUALIZADO'].sum().reset_index()
    fig_situacao = px.bar(proporcao_situacao, x='SITUAÇÃO', y='SALDO ATUALIZADO',
                          title='Proporção da Dívida por Situação')
    st.plotly_chart(fig_situacao)

    # Ranking TOP 10 Devedores
    st.subheader("TOP 10 Maiores Devedores")
    top_10 = df.groupby('ENTE')['SALDO ATUALIZADO'].sum().sort_values(ascending=False).head(10).reset_index()
    st.dataframe(top_10, use_container_width=True)
