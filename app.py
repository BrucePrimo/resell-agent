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
    .space-block {{ margin-top: 20px; margin-bottom: 20px; }}
    </style>
""", unsafe_allow_html=True)

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# --- 2. MOTEURS D'EXTRACTION ---
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

def fetch_discogs_data(keywords):
    if not DISCOGS_TOKEN: return []
    query = urllib.parse.quote(keywords)
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=5"
    try:
        res = requests.get(url, headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}", "User-Agent": "ResellAgentIA/1.0"}, timeout=5)
        results = []
        if res.status_code == 200:
            for item in res.json().get("results", []):
                results.append({"Titre": item.get("title"), "Édition / Label": f"{item.get('label', ['N/C'])[0]} ({item.get('year', 'N/C')})"})
        return results
    except: return []

# --- 3. INTERFACE ---
with st.sidebar:
    st.title("⚙️ Secteurs de Veille")
    univers = st.radio("Sélectionnez l'univers de l'objet :", ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection & Mag", "⌚ Montres de Collection"))

st.title(f"{ICONE_APPLI} {NOM_APPLI}")
st.markdown(f"<p style='color:#64748b; font-size:16px; margin-top:-15px; margin-bottom:25px;'>{SOUS_TITRE}</p>", unsafe_allow_html=True)

# Un seul champ de texte stable
query = st.text_input("Saisissez l'objet à rechercher (Utilise le micro de ton Chromebook si besoin) :", value="")

st.markdown('<div class="space-block"></div>', unsafe_allow_html=True)

# --- 4. AFFICHAGE DES BOUTONS DE REDIRECTION ---
if query:
    encoded_query = urllib.parse.quote(query)
    st.markdown("### 🔍 Liens d'accès direct aux prix du marché")
    
    url_ebay = f"https://www.ebay.fr/sch/i.html?_nkw={encoded_query}&LH_Complete=1&LH_Sold=1"
    url_lbc = f"https://www.leboncoin.fr/recherche?text={encoded_query}"
    url_vinted = f"https://www.vinted.fr/catalog?search_text={encoded_query}"
    url_catawiki = f"https://www.catawiki.com/fr/s?q={encoded_query}"
    url_chrono24 = f"https://www.chrono24.fr/search/index.htm?query={encoded_query}"
    url_discogs = f"https://www.discogs.com/fr/sell/list?q={encoded_query}"

    cols_btn = st.columns(4)
    with cols_btn[0]: st.markdown(f'<a href="{url_ebay}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#ff9800; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🟠 eBay (Vendus)</button></a>', unsafe_allow_html=True)
    with cols_btn[1]: st.markdown(f'<a href="{url_lbc}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#ff5722; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🔴 LeBonCoin</button></a>', unsafe_allow_html=True)
    with cols_btn[2]: st.markdown(f'<a href="{url_vinted}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#009688; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🔵 Vinted</button></a>', unsafe_allow_html=True)
    
    if univers == "⌚ Montres de Collection":
        with cols_btn[3]: st.markdown(f'<a href="{url_chrono24}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#374151; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">⌚ Chrono24</button></a>', unsafe_allow_html=True)
    elif univers == "🎵 Disques & Vinyles":
        with cols_btn[3]: st.markdown(f'<a href="{url_discogs}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#854d0e; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🎵 Discogs Market</button></a>', unsafe_allow_html=True)
    else:
        with cols_btn[3]: st.markdown(f'<a href="{url_catawiki}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#a855f7; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">🟣 Catawiki</button></a>', unsafe_allow_html=True)

st.markdown('<div class="space-block"></div>', unsafe_allow_html=True)

# --- 5. EXECUTION DE L'ANALYSE ---
bouton_analyser = st.button("🚀 Extraire la valeur de l'objet et calculer l'argus", use_container_width=True)

if bouton_analyser and query:
    with st.spinner("Analyse en cours..."):
        st.markdown('### 🟠 Prix extraits (eBay Vendus)')
        ebay_prices = fetch_ebay_sold(query)
        
        if ebay_prices:
            df_ebay = pd.DataFrame(ebay_prices)
            st.dataframe(df_ebay, use_container_width=True)
            
            prices = df_ebay["Prix (€)"].tolist()
            mediane = round(np.median(prices), 2)
            plafond = round(max(prices), 2)
            plancher = round(min(prices), 2)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">ESTIMATION MÉDIANE</p><p class="big-price">{mediane} €</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">VALEUR HAUTE</p><p class="big-price" style="color:#10b981;">{plafond} €</p></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-box"><p style="margin:0;font-size:13px;font-weight:600;color:#64748b;">SEUIL PLANCHER</p><p class="big-price" style="color:#ef4444;">{plancher} €</p></div>', unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée extraite directement à cet instant à cause des protections anti-bot d'eBay. Utilisez les boutons d'accès direct ci-dessus pour consulter les prix réels instantanément.")

        if univers == "🎵 Disques & Vinyles":
            st.markdown('### 🎵 Base Discogs (Pressages)')
            discogs_results = fetch_discogs_data(query)
            if discogs_results: st.dataframe(pd.DataFrame(discogs_results), use_container_width=True)
