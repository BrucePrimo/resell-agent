import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from streamlit_mic_recorder import speech_to_text

# Configuration de la page
st.set_page_config(page_title="Primo Bruce 1 System", layout="wide", page_icon="⚡")

# Style CSS pour une interface propre
st.markdown("""
    <style>
    .metric-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; }
    .header-style { font-size: 20px; font-weight: bold; color: #1e293b; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

# --- FONCTIONS DE RÉCUPÉRATION ---

def get_ebay_sold(keywords):
    url = f"https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(keywords)}&LH_Complete=1&LH_Sold=1"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        for item in soup.select(".s-item")[:5]:
            title = item.select_one(".s-item__title").text.replace("Nouvelle annonce", "").strip()
            price = item.select_one(".s-item__price").text.replace("EUR", "").replace("€", "").replace(",", ".").split("à")[0].strip()
            data.append({"Titre": title, "Prix (€)": float(''.join(c for c in price if c.isdigit() or c == '.'))})
        return data
    except: return []

def get_rakuten_delcampe(keywords):
    data = []
    # Rakuten
    url_r = f"https://fr.shopping.rakuten.com/s/{urllib.parse.quote(keywords)}"
    try:
        res = requests.get(url_r, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        for prod in soup.select("[data-qa='product_card']")[:3]:
            title = prod.select_one("[data-qa='product_title']").text.strip()
            price = prod.select_one("[data-qa='product_price']").text.replace("€", "").replace(",", ".").strip()
            data.append({"Plateforme": "Rakuten", "Titre": title, "Prix (€)": float(''.join(c for c in price if c.isdigit() or c == '.'))})
    except: pass
    return data

def get_discogs_data(keywords):
    if not DISCOGS_TOKEN: return []
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(keywords)}&type=release&per_page=5"
    try:
        res = requests.get(url, headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}"}, timeout=5)
        results = []
        for item in res.json().get("results", []):
            rel_id = item.get("id")
            price_stat = requests.get(f"https://api.discogs.com/marketplace/price_statistics/{rel_id}", headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}"}).json()
            price = price_stat.get('lowest_price', {}).get('value', 0)
            results.append({"Titre": item.get("title"), "Prix (€)": float(price)})
        return results
    except: return []

# --- INTERFACE UTILISATEUR ---

st.title("⚡ Primo Bruce 1 System")

with st.sidebar:
    st.header("⚙️ Paramètres")
    univers = st.radio("Univers de recherche :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection", "⌚ Montres"))

# Entrée unifiée
text_in = speech_to_text(language='fr', start_prompt="▶️ Lancer l'écoute", stop_prompt="⏹️ Arrêter", key='stt')
query = st.text_input("Recherche manuelle ou vocale :", value=text_in if text_in else "")

if st.button("🚀 Lancer l'analyse complète", type="primary"):
    if query:
        # 1. eBay Section
        st.markdown('<p class="header-style">🟠 eBay (Ventes conclues)</p>', unsafe_allow_html=True)
        ebay_data = get_ebay_sold(query)
        if ebay_data: st.dataframe(pd.DataFrame(ebay_data), use_container_width=True)
        else: st.info("Aucune vente eBay trouvée.")

        # 2. Rakuten Section
        st.markdown('<p class="header-style">🟢 Rakuten & Autres</p>', unsafe_allow_html=True)
        other_data = get_rakuten_delcampe(query)
        if other_data: st.dataframe(pd.DataFrame(other_data), use_container_width=True)
        else: st.info("Aucun résultat Rakuten.")

        # 3. Discogs Section
        if univers == "🎵 Disques & Vinyles":
            st.markdown('<p class="header-style">🎵 Discogs (Marché)</p>', unsafe_allow_html=True)
            disc_data = get_discogs_data(query)
            if disc_data: st.dataframe(pd.DataFrame(disc_data), use_container_width=True)
            else: st.info("Aucune donnée Discogs.")

        # 4. Synthèse Globale
        st.divider()
        st.header("🎯 Synthèse des prix")
        all_prices = [d['Prix (€)'] for d in ebay_data] + [d['Prix (€)'] for d in other_data]
        if all_prices:
            col1, col2, col3 = st.columns(3)
            col1.metric("Médiane", f"{np.median(all_prices):.2f} €")
            col2.metric("Prix Max", f"{max(all_prices):.2f} €")
            col3.metric("Prix Min", f"{min(all_prices):.2f} €")
