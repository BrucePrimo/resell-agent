import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- 1. CONFIGURATION ET DESIGN ---
NOM_APPLI = "Primo Bruce 1 system"
ICONE_APPLI = "⚡"
SOUS_TITRE = "Expertise Argus & Estimations de Marché Professionnelles"
COULEUR_PRINCIPALE = "#1E293B"

st.set_page_config(page_title=NOM_APPLI, page_icon=ICONE_APPLI, layout="wide")

st.markdown(f"""
    <style>
    html, body, [class*="css"], p, div, button, input, label {{ font-family: 'Roboto', sans-serif !important; }}
    .metric-box {{ background-color: #ffffff; padding: 22px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid {COULEUR_PRINCIPALE}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .big-price {{ font-size: 34px; font-weight: 700; color: {COULEUR_PRINCIPALE}; margin-top: 5px; margin-bottom: 5px; }}
    div.stButton > button:first-child {{ background-color: {COULEUR_PRINCIPALE}; color: white; border: none; border-radius: 6px; font-weight: 600; padding: 10px 20px; }}
    .header-style {{ font-size: 20px; font-weight: bold; color: {COULEUR_PRINCIPALE}; margin-top: 20px; margin-bottom: 10px; }}
    </style>
""", unsafe_allow_html=True)

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# --- 2. MOTEURS D'EXTRACTION EN TEMPS RÉEL ---

def fetch_ebay_prices(keywords):
    url = f"https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(keywords)}&LH_Complete=1&LH_Sold=1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        for item in soup.select(".s-item")[:8]:
            title = item.select_one(".s-item__title")
            price = item.select_one(".s-item__price")
            if title and price:
                titre_txt = title.text.replace("Nouvelle annonce", "").strip()
                if "Boutique" in titre_txt or "Shop" in titre_txt: continue
                prix_txt = price.text.replace("EUR", "").replace("€", "").replace(",", ".").split("à")[0].strip()
                try:
                    prix_val = float(''.join(c for c in prix_txt if c.isdigit() or c == '.'))
                    if prix_val > 0: data.append({"Titre": titre_txt, "Prix (€)": prix_val})
                except: continue
        return data
    except: return []

def fetch_rakuten_prices(keywords):
    url = f"https://fr.shopping.rakuten.com/s/{urllib.parse.quote(keywords)}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        for prod in soup.select("[data-qa='product_card']")[:5]:
            title = prod.select_one("[data-qa='product_title']")
            price = prod.select_one("[data-qa='product_price']")
            if title and price:
                prix_txt = price.text.replace("€", "").replace(",", ".").strip()
                try:
                    prix_val = float(''.join(c for c in prix_txt if c.isdigit() or c == '.'))
                    data.append({"Titre": title.text.strip(), "Prix (€)": prix_val})
                except: continue
        return data
    except: return []

def fetch_delcampe_prices(keywords):
    url = f"https://www.delcampe.net/fr/collections/search?term={urllib.parse.quote(keywords)}&status=closed&net_prices=all"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        data = []
        for art in soup.select(".item-main-infos")[:5]:
            title = art.select_one(".item-title")
            price = art.select_one(".item-price")
            if title and price:
                prix_txt = price.text.replace("€", "").replace(",", ".").strip()
                try:
                    prix_val = float(''.join(c for c in prix_txt if c.isdigit() or c == '.'))
                    data.append({"Titre": title.text.strip(), "Prix (€)": prix_val})
                except: continue
        return data
    except: return []

def fetch_discogs_prices(keywords):
    if not DISCOGS_TOKEN: return []
    url = f"https://api.discogs.com/database/search?q={urllib.parse.quote(keywords)}&type=release&per_page=4"
    try:
        res = requests.get(url, headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}", "User-Agent": "ResellAgentIA/1.0"}, timeout=5)
        results = []
        if res.status_code == 200:
            for item in res.json().get("results", []):
                rel_id = item.get("id")
                # Récupération du prix min sur la marketplace pour cette édition
                stat_res = requests.get(f"https://api.discogs.com/marketplace/price_statistics/{rel_id}", headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}"}, timeout=3)
                price_val = 0.0
                if stat_res.status_code == 200:
                    price_val = stat_res.json().get('lowest_price', {}).get('value', 0.0)
                
                results.append({
                    "Titre": item.get("title"),
                    "Édition": f"{item.get('label', ['N/C'])[0]} ({item.get('year', 'N/C')})",
                    "Prix Min (€)": float(price_val) if price_val else 0.0
                })
        return results
    except: return []

# --- 3. INTERFACE UTILISATEUR ---
with st.sidebar:
    st.title("⚙️ Secteurs de Veille")
    univers = st.radio("Univers :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection", "⌚ Montres"))

st.title(f"{ICONE_APPLI} {NOM_APPLI}")
st.markdown(f"<p style='color:#64748b; font-size:16px; margin-top:-15px; margin-bottom:25px;'>{SOUS_TITRE}</p>", unsafe_allow_html=True)

query = st.text_input("Objet à rechercher (Saisir la référence exacte) :")

if query:
    q = urllib.parse.quote(query)
    st.write("### 🔍 Accès rapides (Vérification manuelle)")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<a href="https://www.ebay.fr/sch/i.html?_nkw={q}&LH_Complete=1&LH_Sold=1" target="_blank"><button style="width:100%; height:38px; background-color:#ff9800; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟠 eBay (Vendus)</button></a>', unsafe_allow_html=True)
    c2.markdown(f'<a href="https://www.leboncoin.fr/recherche?text={q}" target="_blank"><button style="width:100%; height:38px; background-color:#ff5722; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🔴 LeBonCoin</button></a>', unsafe_allow_html=True)
    c3.markdown(f'<a href="https://www.vinted.fr/catalog?search_text={q}" target="_blank"><button style="width:100%; height:38px; background-color:#009688; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🔵 Vinted</button></a>', unsafe_allow_html=True)
    
    if univers == "⌚ Montres":
        c4.markdown(f'<a href="https://www.chrono24.fr/search/index.htm?query={q}" target="_blank"><button style="width:100%; height:38px; background-color:#374151; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">⌚ Chrono24</button></a>', unsafe_allow_html=True)
    else:
        c4.markdown(f'<a href="https://www.catawiki.com/fr/s?q={q}" target="_blank"><button style="width:100%; height:38px; background-color:#a855f7; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟣 Catawiki</button></a>', unsafe_allow_html=True)

    st.write("---")
    
    if st.button("🚀 Lancer l'analyse comparative en temps réel", type="primary", use_container_width=True):
        with st.spinner("Extraction simultanée des données de marché..."):
            
            # Stockage global pour la synthèse finale
            all_discovered_prices = []
            
            # 1. TABLEAU EBAY
            st.markdown('<p class="header-style">🟠 eBay (Ventes Conclues)</p>', unsafe_allow_html=True)
            ebay_data = fetch_ebay_prices(query)
            if ebay_data:
                df_ebay = pd.DataFrame(ebay_data)
                st.dataframe(df_ebay, use_container_width=True)
                all_discovered_prices.extend(df_ebay["Prix (€)"].tolist())
            else:
                st.info("Aucune transaction récente extraite d'eBay.")

            # 2. TABLEAU RAKUTEN
            st.markdown('<p class="header-style">🟢 Rakuten (Offres en cours)</p>', unsafe_allow_html=True)
            rakuten_data = fetch_rakuten_prices(query)
            if rakuten_data:
                df_rakuten = pd.DataFrame(rakuten_data)
                st.dataframe(df_rakuten, use_container_width=True)
                all_discovered_prices.extend(df_rakuten["Prix (€)"].tolist())
            else:
                st.info("Aucun résultat sur Rakuten.")

            # 3. TABLEAU DELCAMPE
            st.markdown('<p class="header-style">🟤 Delcampe (Historique de ventes)</p>', unsafe_allow_html=True)
            delcampe_data = fetch_delcampe_prices(query)
            if delcampe_data:
                df_delcampe = pd.DataFrame(delcampe_data)
                st.dataframe(df_delcampe, use_container_width=True)
                all_discovered_prices.extend(df_delcampe["Prix (€)"].tolist())
            else:
                st.info("Aucun résultat sur Delcampe.")

            # 4. TABLEAU DISCOGS (Uniquement si vinyle)
            if univers == "🎵 Disques & Vinyles":
                st.markdown('<p class="header-style">🎵 Discogs Marketplace (Prix minimum par pressage)</p>', unsafe_allow_html=True)
                discogs_data = fetch_discogs_prices(query)
                if discogs_data:
                    df_discogs = pd.DataFrame(discogs_data)
                    st.dataframe(df_discogs, use_container_width=True)
                    # On n'ajoute à l'argus global que les prix valides (> 0)
                    valid_discogs = [x["Prix Min (€)"] for x in discogs_data if x["Prix Min (€)"] > 0]
                    all_discovered_prices.extend(valid_discogs)
                else:
                    st.info("Aucune référence de prix trouvée sur Discogs.")

            # 5. SYNTHÈSE ARGUS
            st.write("---")
            st.markdown('### 🎯 Indicateurs de Marché Globaux')
            if all_discovered_prices:
                col1, col2, col3 = st.columns(3)
                col1.markdown(f'<div class="metric-box"><p style="margin:0;font-size:12px;color:#64748b;font-weight:bold;">PRIX MÉDIAN GLOBAL</p><p class="big-price">{round(np.median(all_discovered_prices), 2)} €</p></div>', unsafe_allow_html=True)
                col2.markdown(f'<div class="metric-box"><p style="margin:0;font-size:12px;color:#10b981;font-weight:bold;">VALEUR PLAFOND</p><p class="big-price" style="color:#10b981;">{round(max(all_discovered_prices), 2)} €</p></div>', unsafe_allow_html=True)
                col3.markdown(f'<div class="metric-box"><p style="margin:0;font-size:12px;color:#ef4444;font-weight:bold;">SEUIL PLANCHER</p><p class="big-price" style="color:#ef4444;">{round(min(all_discovered_prices), 2)} €</p></div>', unsafe_allow_html=True)
            else:
                st.warning("Indicateurs indisponibles : pas assez de données chiffrées extraites en direct.")
