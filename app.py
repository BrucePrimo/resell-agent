import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from streamlit_mic_recorder import speech_to_text
import time

st.set_page_config(page_title="Primo Bruce 1 System", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .metric-box { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; }
    .header-style { font-size: 20px; font-weight: bold; color: #1e293b; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

# Headers plus robustes pour éviter les blocages anti-bot
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
}

def get_ebay_sold(keywords):
    url = f"https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(keywords)}&LH_Complete=1&LH_Sold=1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        # Utilisation de sélecteurs plus larges et stables
        items = soup.select(".s-item__wrapper") or soup.select(".s-item")
        for item in items[:6]:
            title_elem = item.select_one(".s-item__title")
            price_elem = item.select_one(".s-item__price")
            if title_elem and price_elem:
                title = title_elem.text.replace("Nouvelle annonce", "").strip()
                if "Boutique sur" in title or "Shop on eBay" in title: continue
                price_txt = price_elem.text.replace("EUR", "").replace("€", "").replace(",", ".").split("à")[0].strip()
                try:
                    prix = float(''.join(c for c in price_txt if c.isdigit() or c == '.'))
                    if prix > 0:
                        data.append({"Titre": title, "Prix (€)": prix})
                except: pass
        return data
    except: return []

def get_rakuten_data(keywords):
    url = f"https://fr.shopping.rakuten.com/s/{urllib.parse.quote(keywords)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        items = soup.select("[data-qa='product_card']") or soup.select(".m_product_card")
        for prod in items[:4]:
            title_elem = prod.select_one("[data-qa='product_title']") or prod.select_one(".title")
            price_elem = prod.select_one("[data-qa='product_price']") or prod.select_one(".price")
            if title_elem and price_elem:
                title = title_elem.text.strip()
                price_txt = price_elem.text.replace("€", "").replace(",", ".").strip()
                try:
                    prix = float(''.join(c for c in price_txt if c.isdigit() or c == '.'))
                    data.append({"Plateforme": "Rakuten", "Titre": title, "Prix (€)": prix})
                except: pass
    except: pass
    return data

def get_discogs_data(keywords):
    if not DISCOGS_TOKEN: return []
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(keywords)}&type=release&per_page=5"
    try:
        res = requests.get(url, headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}", "User-Agent": "ResellAgentIA/1.0"}, timeout=5)
        results = []
        if res.status_code == 200:
            for item in res.json().get("results", []):
                # Extraction alternative du prix ou de l'année si dispo directement
                title = item.get("title")
                year = item.get("year", "N/C")
                # Faute de prix temps réel via l'API restreinte, on utilise une estimation ou le label pour l'identification
                label = item.get("label", ["N/C"])[0]
                results.append({"Titre": title, "Édition / Label": f"{label} ({year})"})
        return results
    except: return []

# --- INTERFACE UTILISATEUR ---
st.title("⚡ Primo Bruce 1 System")

with st.sidebar:
    st.header("⚙️ Paramètres")
    univers = st.radio("Univers de recherche :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection", "⌚ Montres"))

text_in = speech_to_text(language='fr', start_prompt="▶️ Lancer l'écoute", stop_prompt="⏹️ Arrêter", key='stt')
query = st.text_input("Recherche manuelle ou vocale :", value=text_in if text_in else "")

if st.button("🚀 Lancer l'analyse complète", type="primary"):
    if query:
        # 1. eBay Section
        st.markdown('<p class="header-style">🟠 eBay (Ventes conclues)</p>', unsafe_allow_html=True)
        ebay_data = get_ebay_sold(query)
        if ebay_data: st.dataframe(pd.DataFrame(ebay_data), use_container_width=True)
        else: st.info("Aucune vente eBay trouvée (Vérifier la saisie ou protection temporaire).")

        # 2. Rakuten Section
        st.markdown('<p class="header-style">🟢 Rakuten & Autres</p>', unsafe_allow_html=True)
        other_data = get_rakuten_data(query)
        if other_data: st.dataframe(pd.DataFrame(other_data), use_container_width=True)
        else: st.info("Aucun résultat Rakuten.")

        # 3. Discogs Section
        if univers == "🎵 Disques & Vinyles":
            st.markdown('<p class="header-style">🎵 Discogs (Identification des pressages)</p>', unsafe_allow_html=True)
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
        else:
            st.warning("Calcul de la synthèse impossible sans données de prix valides.")
