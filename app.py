import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="SS TECH PRO WEB", layout="wide", initial_sidebar_state="expanded")

# Credenciais Supabase
URL = "https://ikkcupfmcbuxnraboexx.supabase.co/rest/v1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlra2N1cGZtY2J1eG5yYWJvZXh4Iiwicm9sZSI6ImFub24iLeveliaXQiOjE3Njk5ODU5NDYsImV4cCI6MjA4NTU2MTk0Nn0.rK5TSg2p2LJxrmqiTtlLZKylHnbE4cpFaWYxBDsASn0",
    "Content-Type": "application/json"
}


# --- FUNÇÕES DE COMUNICAÇÃO ---
def buscar_dados(tabela):
    try:
        response = httpx.get(f"{URL}/{tabela}", headers=HEADERS)
        dados = response.json()
        # Filtra apenas itens que possuem 'codigo' e 'nome' válidos para evitar o TypeError
        return [p for p in dados if isinstance(p, dict) and 'codigo' in p and 'nome' in p]
    except:
        return []


# --- INTERFACE LATERAL ---
st.sidebar.title("🚀 SS TECH SISTEMAS")
menu = st.sidebar.radio("Navegação:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar_dados("estoque")

    if estoque:
        # Formatação segura para evitar o erro de 'redacted'
        prod_nomes = [f"{str(p['codigo'])} - {str(p['nome'])}" for p in estoque]

        col1, col2 = st.columns([2, 1])
        with col1:
            selecionado = st.selectbox("Selecione o Produto", prod_nomes)
            item_cod_bruto = selecionado.split(" - ")[0]
            item = next(p for p in estoque if str(p['codigo']) == item_cod_bruto)

            qtd = st.number_input("Quantidade", min_value=1, step=1)
            cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")
            metodo = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito", "FIADO"])

        with col2:
            preco_venda = float(item.get('preco_venda', 0))
            subtotal = preco_venda * qtd
            desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0)
            total_final = subtotal - desconto
            st.metric("Total a Pagar", f"R$ {total_final:.2f}")

            if st.button("FINALIZAR VENDA", use_container_width=True):
                venda_payload = {
                    "cod_item": item['codigo'], "produto": item['nome'], "quantidade": qtd,
                    "subtotal": subtotal, "desconto": desconto, "total_liq": total_final,
                    "cliente": cliente, "metodo": metodo, "vendedor": "WEB-MOBILE"
                }
                httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda_payload)

                vendas_atuais = int(item.get('vendas', 0))
                httpx.patch(f"{URL}/estoque?codigo=eq.{item['codigo']}", headers=HEADERS,
                            json={"vendas": vendas_atuais + qtd})

                if metodo == "FIADO":
                    httpx.post(f"{URL}/fiado", headers=HEADERS,
                               json={"cliente": cliente, "valor": total_final, "status": "PENDENTE"})

                st.success("✅ Venda Finalizada!")
                st.rerun()

# --- 2. VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Histórico de Vendas")
    vendas = buscar_dados("vendas")
    if vendas:
        st.dataframe(pd.DataFrame(vendas), use_container_width=True)

# --- 3. ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Estoque")
    estoque = buscar_dados("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        # Lógica de cálculo idêntica ao EXE
        df['Qtd Atual'] = df['qtd_ini'].fillna(0) + df['compras'].fillna(0) - df['vendas'].fillna(0)
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("🛠️ Editar Preço/Estoque")
        with st.form("edit"):
            c1, c2, c3 = st.columns(3)
            e_cod = c1.text_input("Código do Produto")
            e_preco = c2.number_input("Novo Preço", min_value=0.0)
            e_compra = c3.number_input("Adicionar Compra", min_value=0)
            if st.form_submit_button("Atualizar"):
                item_e = next((p for p in estoque if str(p['codigo']) == e_cod), None)
                if item_e:
                    nova_compra = int(item_e.get('compras', 0)) + e_compra
                    httpx.patch(f"{URL}/estoque?codigo=eq.{e_cod}", headers=HEADERS,
                                json={"preco_venda": e_preco, "compras": nova_compra})
                    st.success("Atualizado!")
                    st.rerun()

# --- 4. FIADO ---
elif menu == "FIADO":
    st.header("📝 Fiados")
    fiados = buscar_dados("fiado")
    if fiados:
        df_f = pd.DataFrame(fiados)
        st.table(df_f)
        devedor = st.selectbox("Baixa em:", df_f['cliente'].unique())
        if st.button("Confirmar Pagamento"):
            httpx.delete(f"{URL}/fiado?cliente=eq.{devedor}", headers=HEADERS)
            st.rerun()

# --- 5. FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo de Caixa")
    vendas = buscar_dados("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        total = df['total_liq'].sum()
        st.metric("Faturamento Total", f"R$ {total:.2f}")
        st.subheader("Entradas por Método")
        st.bar_chart(df.groupby('metodo')['total_liq'].sum())

# --- 6. PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Reposição Necessária")
    estoque = buscar_dados("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Qtd Atual'] = df['qtd_ini'].fillna(0) + df['compras'].fillna(0) - df['vendas'].fillna(0)
        baixo = df[df['Qtd Atual'] <= 3]
        st.table(baixo[['codigo', 'nome', 'Qtd Atual']])

# --- 7. GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Performance de Produtos")
    vendas = buscar_dados("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.bar_chart(df.groupby('produto')['total_liq'].sum())