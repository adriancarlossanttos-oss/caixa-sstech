import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
import time

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
            prod_sel = st.selectbox("Selecione o Produto", lista_prods, key="prod_box")
            qtd = st.number_input("Quantidade", min_value=1, value=1, key="qtd_box")
            cliente = st.text_input("Cliente", "CONSUMIDOR", key="cli_box")
            metodo = st.selectbox("Método", ["Dinheiro", "Pix", "Cartão"], key="met_box")

        with col2:
            cod_item = prod_sel.split(" - ")[0]
            item = next(p for p in estoque_dados if str(p['codigo']) == cod_item)

            # Ajuste de Colunas baseado no seu banco
            preco_v = float(item.get('preco_venda', 0))

            # Tenta pegar 'P.COMPRA (MÉD)', se não existir tenta 'preco_custo', se não 0
            preco_c = float(item.get('P.COMPRA (MÉD)') or item.get('preco_custo') or 0)

            subtotal = preco_v * qtd
            desconto = st.number_input("Desconto (R$ total)", min_value=0.0, value=0.0, key="desc_box")
            total_liq = subtotal - desconto

            st.write(f"### Total: R$ {total_liq:.2f}")
            st.info(f"Unitário: R$ {preco_v:.2f} | Custo Médio: R$ {preco_c:.2f}")

        if st.button("FINALIZAR VENDA", use_container_width=True):
            custo_total = preco_c * qtd

            # Trava de segurança
            if total_liq < custo_total:
                st.error(
                    f"❌ Desconto excessivo! O valor final (R$ {total_liq:.2f}) é menor que o custo (R$ {custo_total:.2f}).")
            else:
                with st.spinner("Gravando dados..."):
                    agora = datetime.now().isoformat()

                    # 1. Vendas
                    venda_payload = {
                        "data_hora": agora,
                        "cod_item": str(cod_item),
                        "produto": str(item['nome']),
                        "cliente": str(cliente),
                        "metodo": str(metodo),
                        "forma": str(metodo),
                        "subtotal": float(subtotal),
                        "desconto": float(desconto),
                        "total_liq": float(total_liq),
                        "vendedor": "WEB"
                    }
                    httpx.post(f"{URL}/vendas", headers=HEADERS, json=venda_payload)

                    # 2. Fluxo (como ENTRADA)
                    fluxo_payload = {
                        "tipo": "ENTRADA",
                        "valor": float(total_liq),
                        "descricao": f"Venda: {item['nome']}",
                        "observacao": f"Cliente: {cliente}",
                        "created_at": agora
                    }
                    httpx.post(f"{URL}/fluxo", headers=HEADERS, json=fluxo_payload)

                    # 3. Baixar Estoque
                    vendas_atuais = int(item.get('vendas', 0) or 0)
                    httpx.patch(f"{URL}/estoque?codigo=eq.{cod_item}", headers=HEADERS,
                                json={"vendas": vendas_atuais + qtd})

                    st.balloons()
                    st.success("✅ Venda Finalizada!")
                    time.sleep(1.5)
                    st.rerun()

# --- 2. VENDAS ---
elif menu == "VENDAS":
    st.header("📋 Relatório de Vendas")
    dados = get_data("vendas")
    if dados:
        df = pd.DataFrame(dados)
        colunas = ['id', 'data_hora', 'cod_item', 'produto', 'cliente', 'metodo', 'subtotal', 'desconto', 'total_liq']
        st.dataframe(df[[c for c in colunas if c in df.columns]], use_container_width=True)

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
    st.header("💰 Fluxo de Caixa")
    dados = get_data("fluxo")
    if dados:
        df = pd.DataFrame(dados)
        if 'valor' in df.columns and 'tipo' in df.columns:
            df['valor_calc'] = df.apply(lambda x: x['valor'] if str(x['tipo']).upper() == "ENTRADA" else -x['valor'],
                                        axis=1)
            st.metric("Saldo Real", f"R$ {df['valor_calc'].sum():.2f}")
        st.dataframe(df, use_container_width=True)

# --- 6. PRÓXIMAS COMPRAS ---
elif menu == "PRÓXIMAS COMPRAS":
    st.header("🛒 Compras Necessárias")
    estoque = get_data("estoque")
    if estoque:
        df = pd.DataFrame(estoque)
        df['Qtd'] = df.get('qtd_ini', 0).fillna(0) + df.get('compras', 0).fillna(0) - df.get('vendas', 0).fillna(0)
        baixo = df[df['Qtd'] <= 3]
        st.table(baixo[['codigo', 'nome', 'Qtd']])

# --- 7. GRÁFICO ---
elif menu == "GRÁFICO":
    st.header("📊 Performance Visual")
    vendas = get_data("fluxo")
    if vendas:
        df = pd.DataFrame(vendas)
        if 'valor' in df.columns:
            st.bar_chart(df.groupby('descricao')['valor'].sum())