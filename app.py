import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Configurações do Painel ---
st.set_page_config(
    page_title="Dashboard de Dívidas de Precatórios do TJPE",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("Dashboard de Dívidas de Precatórios do TJPE")

# --- Leitura e Limpeza dos Dados ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, header=1)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{file_path}' não encontrado. Verifique se o nome e o caminho estão corretos.")
        return None

    df['SALDO ATUALIZADO'] = pd.to_numeric(df['SALDO ATUALIZADO'], errors='coerce')
    
    return df

# NOME EXATO DO SEU ARQUIVO .xlsx
file_name = 'Estudo da dívia em Agosto-25.xlsx'
df = load_data(file_name)

if df is not None:
    # --- Filtros no Painel Principal ---
    st.subheader("Filtros")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        ente_selecionado = st.selectbox("Selecione o Ente Devedor", ['Todos'] + sorted(df['ENTE'].unique()))
    with col2:
        orcamento_selecionado = st.selectbox("Selecione o Orçamento", ['Todos'] + sorted(df['ORÇAMENTO'].unique()))
    with col3:
        situacao_selecionada = st.selectbox("Selecione a Situação", ['Todos'] + sorted(df['SITUAÇÃO'].unique()))
    with col4:
        processo_selecionado = st.text_input("Buscar por Processo (Digite o nº):")
    with col5:
        cpf_cnpj_selecionado = st.text_input("Buscar por CPF/CNPJ:")
    
    df_filtrado = df.copy()
    
    if ente_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ENTE'] == ente_selecionado]
    if orcamento_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ORÇAMENTO'] == orcamento_selecionado]
    if situacao_selecionada != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['SITUAÇÃO'] == situacao_selecionada]
    if processo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['PROCESSO'].astype(str).str.contains(processo_selecionado, case=False, na=False)]
    if cpf_cnpj_selecionado:
        df_filtrado = df_filtrado[df_filtrado['CPF/CNPJ'].astype(str).str.contains(cpf_cnpj_selecionado, case=False, na=False)]

    # --- Área de Destaque para Processo (Busca) ---
    st.subheader("Informações Detalhadas do Processo")
    if processo_selecionado:
        processo_info = df[df['PROCESSO'].astype(str).str.contains(processo_selecionado, case=False, na=False)]
        if not processo_info.empty:
            info_display = processo_info.iloc[0][['ENTE', 'PROCESSO', 'ORÇAMENTO', 'SALDO ATUALIZADO']]
            info_display['SALDO ATUALIZADO'] = f"R$ {info_display['SALDO ATUALIZADO']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.write(info_display)
        else:
            st.write("Nenhum processo encontrado com esse número.")

    # --- Widgets e Gráficos Principais ---
    st.subheader("Análises da Dívida")

    # Gráfico de Participação na Dívida Total (com agrupamento)
    total_por_ente = df.groupby('ENTE')['SALDO ATUALIZADO'].sum().reset_index()
    total_geral = total_por_ente['SALDO ATUALIZADO'].sum()
    total_por_ente['% Participação'] = (total_por_ente['SALDO ATUALIZADO'] / total_geral) * 100
    
    total_por_ente['ENTE'] = total_por_ente.apply(
        lambda row: row['ENTE'] if row['% Participação'] >= 2 else 'Outros', axis=1
    )
    total_por_ente = total_por_ente.groupby('ENTE')['SALDO ATUALIZADO'].sum().reset_index()
    
    fig_participacao = px.pie(total_por_ente, values='SALDO ATUALIZADO', names='ENTE',
                             title='Participação dos Entes na Dívida Total',
                             labels={'SALDO ATUALIZADO':'Saldo Total'})
    st.plotly_chart(fig_participacao, use_container_width=True)

    # Gráfico de Proporção da Dívida por Situação
    proporcao_situacao = df_filtrado.groupby('SITUAÇÃO')['SALDO ATUALIZADO'].sum().reset_index()
    fig_situacao = px.pie(proporcao_situacao, values='SALDO ATUALIZADO', names='SITUAÇÃO',
                      title='Proporção da Dívida por Situação (%)')
    st.plotly_chart(fig_situacao, use_container_width=True)

    # Gráfico de Evolução da Dívida do Ente Selecionado
    if ente_selecionado != 'Todos':
        evolucao_divida = df[df['ENTE'] == ente_selecionado].groupby('ORÇAMENTO')['SALDO ATUALIZADO'].sum().reset_index()
        fig_evolucao = px.line(evolucao_divida, x='ORÇAMENTO', y='SALDO ATUALIZADO',
                              title=f'Evolução da Dívida de {ente_selecionado} por Ano')
        st.plotly_chart(fig_evolucao, use_container_width=True)

    # Ranking TOP 10 Maiores Devedores
    st.subheader("TOP 10 Maiores Devedores")
    top_10 = df.groupby('ENTE')['SALDO ATUALIZADO'].sum().sort_values(ascending=False).head(10).reset_index()
    top_10.index = top_10.index + 1  # Começa a numeração em 1
    top_10['SALDO ATUALIZADO'] = top_10['SALDO ATUALIZADO'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(top_10, use_container_width=True)
