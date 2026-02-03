import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# Configuração visual
st.set_page_config(page_title="SS TECH WEB", layout="wide")

# Credenciais
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


def get_data(table):
    try:
        r = httpx.get(f"{URL}/{table}", headers=HEADERS)
        return r.json()
    except:
        return []


# Menu Lateral
st.sidebar.title("MENU SS TECH")
menu = st.sidebar.radio("Ir para:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque_dados = get_data("estoque")
    if estoque_dados:
        lista_prods = [f"{p['codigo']} - {p['nome']}" for p in estoque_dados if 'codigo' in p]
        col1, col2 = st.columns(2)
        with col1:
            prod_sel = st.selectbox("Selecione o Produto", lista_prods)
            qtd = st.number_input("Quantidade", min_value=1, value=1)
            cliente = st.text_input("Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Método", ["Dinheiro", "Pix", "Cartão"])

        with col2:
            cod_item = prod_sel.split(" - ")[0]
            item = next(p for p in estoque_dados if str(p['codigo']) == cod_item)
            total = float(item.get('preco_venda', 0)) * qtd
            st.write(f"### Total: R$ {total:.2f}")

        if st.button("FINALIZAR VENDA", use_container_width=True):
            # 1. Salvar na tabela 'vendas' (usando colunas do seu print)
            venda = {
                "cod_item": cod_item,
                "produto": item['nome'],
                "cliente": cliente,
                "metodo": metodo,
                "forma": metodo,
                "data_hora": datetime.now().isoformat()
            }
            httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda)

            # 2. Salvar na tabela 'fluxo' (conforme image_e14ec3.png)
            fluxo = {
                "tipo": "VENDA",
                "valor": total,
                "descricao": f"Venda: {item['nome']}",
                "observacao": f"Cliente: {cliente}"
            }
            httpx.post(f"{URL}/fluxo", headers=HEADERS, json=fluxo)

            # 3. Baixar Estoque
            nova_venda_qtd = int(item.get('vendas', 0) or 0) + qtd
            httpx.patch(f"{URL}/estoque?codigo=eq.{cod_item}", headers=HEADERS, json={"vendas": nova_venda_qtd})

            st.success("✅ Venda salva em Vendas e Fluxo!")
            st.rerun()

# --- 2. VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    dados = get_data("vendas")
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)
    else:
        st.info("Tabela de vendas vazia.")

# --- 3. ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Estoque")
    dados = get_data("estoque")
    if dados:
        df = pd.DataFrame(dados)
        df['Disponível'] = df.get('qtd_ini', 0).fillna(0) + df.get('compras', 0).fillna(0) - df.get('vendas', 0).fillna(
            0)
        st.dataframe(df, use_container_width=True)

# --- 4. FIADO ---
elif menu == "FIADO":
    st.header("📝 Fiados")
    dados = get_data("fiado")
    if dados:
        st.dataframe(pd.DataFrame(dados), use_container_width=True)

# --- 5. FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo de Caixa (Tabela Fluxo)")
    dados = get_data("fluxo")  # Nome correto da sua tabela
    if dados:
        df = pd.DataFrame(dados)
        if 'valor' in df.columns:
            st.metric("Saldo Total", f"R$ {df['valor'].sum():.2f}")
        st.dataframe(df, use_container_width=True)

# --- 6. PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Compras Necessárias")
    estoque = get_data("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Qtd'] = df.get('qtd_ini', 0).fillna(0) + df.get('compras', 0).fillna(0) - df.get('vendas', 0).fillna(0)
        st.table(df[df['Qtd'] <= 3][['codigo', 'nome', 'Qtd']])

# --- 7. GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Resumo Visual")
    vendas = get_data("fluxo")
    if vendas:
        df = pd.DataFrame(vendas)
        if 'valor' in df.columns:
            st.bar_chart(df.groupby('descricao')['valor'].sum())