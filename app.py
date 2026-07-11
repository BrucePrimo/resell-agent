import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- CONFIGURATION ET DESIGN ---
NOM_APPLI = "Primo Bruce 1 system"    
ICONE_APPLI = "⚡"                      
SOUS_TITRE = "Expertise Argus & Estimations de Marché Professionnelles"
COULEUR_PRINCIPALE = "#1E293B"          

st.set_page_config(page_title=NOM_APPLI, page_icon=ICONE_APPLI, layout="wide")

st.markdown(f"""
    <style>
    .metric-box {{ background-color: #ffffff; padding: 22px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid {COULEUR_PRINCIPALE}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .big-price {{ font-size: 34px; font-weight: 700; color: {COULEUR_PRINCIPALE}; margin-top: 5px; margin-bottom: 5px; }}
    div.stButton > button:first-child {{ background-color: {COULEUR_PRINCIPALE}; color: white; border: none; border-radius: 6px; font-weight: 600; padding: 10px 20px; }}
    </style>
""", unsafe_allow_html=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# --- FONCTIONS DE RECHERCHE ---
def fetch_ebay_sold(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://www.ebay.fr/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        items = soup.select(".s-item__wrapper") or soup.select(".s-item")
        for item in items[:10]:
            title_elem = item.select_one(".s-item__title")
            price_elem = item.select_one(".s-item__price")
            if title_elem and price_elem:
                title = title_elem.text.replace("Nouvelle annonce", "").strip()
                if "Boutique sur" in title or "Shop on eBay" in title: continue
                p_txt = price_elem.text.replace("EUR", "").replace("€", "").replace(",", ".").replace(" ", "").strip()
                if "à" in p_txt: p_txt = p_txt.split("à")[0]
                try:
                    prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                    if prix > 0: ventes.append({"Titre": title, "Prix (€)": prix})
                except: pass
        return ventes
    except: return []

# --- INTERFACE ---
with st.sidebar:
    st.title("⚙️ Secteurs de Veille")
    univers = st.radio("Sélectionnez l'univers de l'objet :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection & Mag", "⌚ Montres de Collection"))

st.title(f"{ICONE_APPLI} {NOM_APPLI}")
st.markdown(f"<p style='color:#64748b; font-size:16px; margin-top:-15px; margin-bottom:25px;'>{SOUS_TITRE}</p>", unsafe_allow_html=True)

query = st.text_input("Saisissez l'objet à rechercher (Artiste, album, modèle, réf...) :", value="")

if query:
    encoded_query = urllib.parse.quote(query)
    st.write("🔍 **Accès directs aux catalogues :**")
    cols_btn = st.columns(4)
    with cols_btn[0]: st.markdown(f'<a href="https://www.ebay.fr/sch/i.html?_nkw={encoded_query}&LH_Complete=1&LH_Sold=1" target="_blank"><button style="width:100%; height:38px; background-color:#ff9800; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟠 eBay (Vendus)</button></a>', unsafe_allow_html=True)
    with cols_btn[1]: st.markdown(f'<a href="https://www.leboncoin.fr/recherche?text={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#ff5722; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🔴 LeBonCoin</button></a>', unsafe_allow_html=True)
    with cols_btn[2]: st.markdown(f'<a href="https://www.vinted.fr/catalog?search_text={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#009688; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🔵 Vinted</button></a>', unsafe_allow_html=True)
    
    if univers == "⌚ Montres de Collection":
        with cols_btn[3]: st.markdown(f'<a href="https://www.chrono24.fr/search/index.htm?query={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#374151; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">⌚ Chrono24</button></a>', unsafe_allow_html=True)
    else:
        with cols_btn[3]: st.markdown(f'<a href="https://www.catawiki.com/fr/s?q={encoded_query}" target="_blank"><button style="width:100%; height:38px; background-color:#a855f7; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟣 Catawiki</button></a>', unsafe_allow_html=True)

st.write(" ")
bouton_analyser = st.button("🚀 Extraire la valeur de l'objet et calculer l'argus", type="primary", use_container_width=True)

if bouton_analyser and query:
    with st.spinner("Analyse des prix en cours..."):
        ebay_prices = fetch_ebay_sold(query)
        if ebay_prices:
            df = pd.DataFrame(ebay_prices)
            st.dataframe(df, use_container_width=True)
            prices = df["Prix (€)"].tolist()
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-box"><p>ESTIMATION MÉDIANE</p><p class="big-price">{round(np.median(prices), 2)} €</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-box"><p>VALEUR HAUTE</p><p class="big-price" style="color:#10b981;">{round(max(prices), 2)} €</p></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-box"><p>SEUIL PLANCHER</p><p class="big-price" style="color:#ef4444;">{round(min(prices), 2)} €</p></div>', unsafe_allow_html=True)
        else:
            st.warning("Aucune vente extraite automatiquement. Utilise les boutons ci-dessus.")
