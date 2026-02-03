import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="SS TECH WEB", layout="wide")

# Credenciais Supabase (Mantenha as suas)
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÕES DE BANCO ---
def buscar_dados(tabela):
    try:
        r = httpx.get(f"{URL}/{tabela}", headers=HEADERS)
        return r.json()
    except:
        return []


# --- MENU LATERAL ---
st.sidebar.title("MENU SS TECH")
menu = st.sidebar.radio("Ir para:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- ABA CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar_dados("estoque")

    if estoque:
        # Criar colunas para organizar o formulário
        col1, col2 = st.columns(2)

        with col1:
            produtos_nomes = [f"{p['codigo']} - {p['nome']}" for p in estoque]
            selecionado = st.selectbox("Selecione o Produto", produtos_nomes)
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")

        with col2:
            metodo = st.selectbox("Forma de Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"])
            desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0)

            # Pegar dados do item selecionado
            item_cod = selecionado.split(" - ")[0]
            item_data = next(p for p in estoque if str(p['codigo']) == item_cod)
            preco = item_data['preco_venda']
            subtotal = preco * qtd
            total_liq = subtotal - desconto

            st.write(f"### Total: R$ {total_liq:.2f}")

        if st.button("FINALIZAR VENDA", use_container_width=True):
            # Lógica para registrar venda e atualizar estoque (POST e PATCH)
            nova_venda = {
                "pedido": 0, "cod_item": item_cod, "produto": item_data['nome'],
                "quantidade": qtd, "cliente": cliente, "metodo": metodo,
                "forma": "À VISTA", "subtotal": subtotal, "desconto": desconto,
                "total_liq": total_liq, "vendedor": "WEB"
            }
            httpx.post(f"{URL}/vendas", headers=HEADERS, json=nova_venda)

            # Atualizar coluna 'vendas' no estoque
            nova_qtd_venda = item_data['vendas'] + qtd
            httpx.patch(f"{URL}/estoque?codigo=eq.{item_cod}", headers=HEADERS, json={"vendas": nova_qtd_venda})

            st.success("Venda realizada e sincronizada!")

# --- ABA VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    vendas = buscar_dados("vendas")
    if vendas:
        df_vendas = pd.DataFrame(vendas)
        st.dataframe(df_vendas, use_container_width=True)

# --- ABA ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Controle de Estoque")
    estoque = buscar_dados("estoque")
    if estoque:
        df_estoque = pd.DataFrame(estoque)
        # Calcula quantidade atual conforme sua regra
        df_estoque['QTD ATUAL'] = df_estoque['qtd_ini'] + df_estoque['compras'] - df_estoque['vendas'] - df_estoque[
            'fiado'] - df_estoque['garantia']
        st.dataframe(df_estoque, use_container_width=True)

# --- OUTRAS ABAS (ESTRUTURA) ---
elif menu == "FIADO":
    st.header("📝 Controle de Fiado")
    st.info("Espaço para gerenciar contas pendentes.")

elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo de Caixa")
    st.write("Resumo financeiro das entradas e saídas.")

elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Sugestão de Compras")
    st.write("Produtos com estoque baixo aparecerão aqui.")

elif menu == "GRÁFICO":
    st.header("📊 Desempenho de Vendas")
    st.bar_chart(pd.DataFrame({"Vendas": [10, 20, 15, 30]}))