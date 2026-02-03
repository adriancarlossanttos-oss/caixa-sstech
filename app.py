import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="SS TECH PRO", layout="wide", initial_sidebar_state="expanded")

# Credenciais Supabase
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÕES DE APOIO ---
def buscar(tabela):
    try:
        return httpx.get(f"{URL}/{tabela}", headers=HEADERS).json()
    except:
        return []


# --- MENU ---
st.sidebar.title("🚀 SS TECH WEB v2.0")
menu = st.sidebar.radio("Navegação:", ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "GRÁFICO"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar("estoque")
    if estoque:
        col1, col2 = st.columns([2, 1])
        with col1:
            prod_nomes = [f"{p['codigo']} - {p['nome']}" for p in estoque]
            selecionado = st.selectbox("Produto", prod_nomes)
            item = next(p for p in estoque if f"{p['codigo']} - {p['nome']}" == selecionado)

            qtd = st.number_input("Quantidade", min_value=1, step=1)
            cliente = st.text_input("Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão", "FIADO"])

        with col2:
            total = item['preco_venda'] * qtd
            st.metric("Total a Pagar", f"R$ {total:.2f}")
            if st.button("CONFIRMAR VENDA", use_container_width=True):
                # Registrar Venda
                venda_data = {"cod_item": item['codigo'], "produto": item['nome'], "quantidade": qtd,
                              "total_liq": total, "cliente": cliente, "metodo": metodo, "vendedor": "WEB"}
                httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda_data)

                # Atualizar Estoque (Vendas)
                httpx.patch(f"{URL}/estoque?codigo=eq.{item['codigo']}", headers=HEADERS,
                            json={"vendas": item['vendas'] + qtd})

                # Se for fiado, registra na tabela de fiado
                if metodo == "FIADO":
                    httpx.post(f"{URL}/fiado", headers=HEADERS,
                               json={"cliente": cliente, "valor": total, "status": "PENDENTE"})

                st.success("Venda processada!")
                st.rerun()

# --- 2. ESTOQUE (COM EDIÇÃO) ---
elif menu == "ESTOQUE":
    st.header("📦 Gestão de Inventário")
    dados = buscar("estoque")
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("🛠️ Editar ou Adicionar Produto")
        with st.expander("Clique para abrir o editor"):
            cod_edit = st.text_input("Código do Produto (para editar ou criar)")
            novo_nome = st.text_input("Nome")
            novo_preco = st.number_input("Preço de Venda", min_value=0.0)

            if st.button("SALVAR ALTERAÇÕES"):
                payload = {"nome": novo_nome, "preco_venda": novo_preco}
                # Verifica se existe para dar PATCH ou POST
                res = httpx.patch(f"{URL}/estoque?codigo=eq.{cod_edit}", headers=HEADERS, json=payload)
                st.success("Dados atualizados!")
                st.rerun()

# --- 3. FLUXO CAIXA (LUCRO) ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Resumo Financeiro")
    vendas = buscar("vendas")
    if vendas:
        df_v = pd.DataFrame(vendas)
        total_vendas = df_v['total_liq'].sum()

        c1, c2 = st.columns(2)
        c1.metric("Faturamento Total", f"R$ {total_vendas:.2f}")
        c2.metric("Vendas Realizadas", len(df_v))

        st.write("### Detalhes de Entradas")
        st.table(df_v[['produto', 'total_liq', 'metodo']])

# --- 4. FIADO ---
elif menu == "FIADO":
    st.header("📝 Contas a Receber")
    fiados = buscar("fiado")
    if fiados:
        st.table(pd.DataFrame(fiados))
    else:
        st.write("Nenhum fiado pendente.")

# --- 5. VENDAS E GRÁFICOS ---
elif menu == "VENDAS":
    st.header("📋 Histórico Geral")
    st.dataframe(pd.DataFrame(buscar("vendas")), use_container_width=True)

elif menu == "GRÁFICO":
    st.header("📊 Performance")
    vendas = buscar("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.bar_chart(df.set_index('produto')['total_liq'])