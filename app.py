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


# --- FUNÇÃO DE BUSCA SEGURA ---
def buscar_dados(tabela):
    try:
        response = httpx.get(f"{URL}/{tabela}", headers=HEADERS)
        dados = response.json()
        # Filtra apenas o que for dicionário válido e tiver a chave 'codigo'
        if isinstance(dados, list):
            return [p for p in dados if isinstance(p, dict) and 'codigo' in p]
        return []
    except:
        return []


# --- MENU LATERAL ---
st.sidebar.title("🚀 SS TECH SISTEMAS")
menu = st.sidebar.radio("Navegação:",
                        ["CAIXA", "VENDAS", "ESTOQUE", "FIADO", "FLUXO CAIXA", "PRÓXIMAS COMPRAS", "GRÁFICO"])

# --- 1. CAIXA ---
if menu == "CAIXA":
    st.header("🛒 Frente de Caixa")
    estoque = buscar_dados("estoque")

    if estoque:
        # CORREÇÃO DEFINITIVA: Formata como string e evita erro de tipo
        prod_nomes = [f"{str(p.get('codigo', ''))} - {str(p.get('nome', 'Sem Nome'))}" for p in estoque]

        col1, col2 = st.columns([2, 1])
        with col1:
            selecionado = st.selectbox("Selecione o Produto", prod_nomes)
            item_cod = selecionado.split(" - ")[0]
            item = next((p for p in estoque if str(p.get('codigo')) == item_cod), None)

            if item:
                qtd = st.number_input("Quantidade", min_value=1, step=1)
                cliente = st.text_input("Nome do Cliente", "CONSUMIDOR")
                metodo = st.selectbox("Método de Pagamento",
                                      ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito", "FIADO"])

        with col2:
            if item:
                preco_v = float(item.get('preco_venda', 0))
                subtotal = preco_v * qtd
                desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0)
                total_final = subtotal - desconto
                st.metric("Total a Pagar", f"R$ {total_final:.2f}")

                if st.button("FINALIZAR VENDA", use_container_width=True):
                    # Registrar Venda
                    venda_payload = {
                        "cod_item": item['codigo'], "produto": item['nome'], "quantidade": qtd,
                        "subtotal": subtotal, "desconto": desconto, "total_liq": total_final,
                        "cliente": cliente, "metodo": metodo, "vendedor": "WEB"
                    }
                    httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda_payload)

                    # Atualizar Estoque
                    nova_venda_qtd = int(item.get('vendas', 0) or 0) + qtd
                    httpx.patch(f"{URL}/estoque?codigo=eq.{item['codigo']}", headers=HEADERS,
                                json={"vendas": nova_venda_qtd})

                    if metodo == "FIADO":
                        httpx.post(f"{URL}/fiado", headers=HEADERS,
                                   json={"cliente": cliente, "valor": total_final, "status": "PENDENTE"})

                    st.success("✅ Venda realizada!")
                    st.rerun()

# --- 2. VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    vendas = buscar_dados("vendas")
    if vendas:
        df_v = pd.DataFrame(vendas)
        st.dataframe(df_v, use_container_width=True)

# --- 3. ESTOQUE ---
elif menu == "ESTOQUE":
    st.header("📦 Gestão de Estoque")
    dados = buscar_dados("estoque")
    if dados:
        df = pd.DataFrame(dados)
        # Lógica idêntica ao EXE (tratando valores vazios com fillna)
        df['Disponível'] = df['qtd_ini'].fillna(0) + df['compras'].fillna(0) - df['vendas'].fillna(0)
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("🛠️ Editar Produto")
        with st.form("edit_estoque"):
            c1, c2, c3 = st.columns(3)
            cod_at = c1.text_input("Código")
            preco_at = c2.number_input("Novo Preço", min_value=0.0)
            compra_at = c3.number_input("Adicionar Compra (Qtd)", min_value=0)
            if st.form_submit_button("Salvar"):
                item_at = next((p for p in dados if str(p['codigo']) == cod_at), None)
                if item_at:
                    n_compra = int(item_at.get('compras', 0) or 0) + compra_at
                    httpx.patch(f"{URL}/estoque?codigo=eq.{cod_at}", headers=HEADERS,
                                json={"preco_venda": preco_at, "compras": n_compra})
                    st.success("Estoque Atualizado!")
                    st.rerun()

# --- 4. FIADO ---
elif menu == "FIADO":
    st.header("📝 Controle de Fiados")
    fiados = buscar_dados("fiado")
    if fiados:
        df_f = pd.DataFrame(fiados)
        st.table(df_f)
        devedor = st.selectbox("Marcar como pago:", df_f['cliente'].unique())
        if st.button("Remover Dívida"):
            httpx.delete(f"{URL}/fiado?cliente=eq.{devedor}", headers=HEADERS)
            st.rerun()

# --- 5. FLUXO CAIXA ---
elif menu == "FLUXO CAIXA":
    st.header("💰 Fluxo de Caixa")
    vendas = buscar_dados("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.metric("Faturamento Total", f"R$ {df['total_liq'].sum():.2f}")
        st.bar_chart(df.groupby('metodo')['total_liq'].sum())

# --- 6. PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Reposição de Estoque")
    estoque = buscar_dados("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Qtd'] = df['qtd_ini'].fillna(0) + df['compras'].fillna(0) - df['vendas'].fillna(0)
        baixo = df[df['Qtd'] <= 3]
        if not baixo.empty:
            st.warning("Itens com estoque baixo:")
            st.table(baixo[['codigo', 'nome', 'Qtd']])
        else:
            st.success("Estoque estável!")

# --- 7. GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Desempenho")
    vendas = buscar_dados("vendas")
    if vendas:
        df = pd.DataFrame(vendas)
        st.subheader("Vendas por Produto")
        st.bar_chart(df.groupby('produto')['total_liq'].sum())