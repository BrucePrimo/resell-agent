import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib.parse
from io import BytesIO

# --- 1. CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="ResellAgent IA", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .big-price { font-size: 32px; font-weight: bold; color: #1f77b4; }
    .vinyl-spec { font-size: 13px; color: #555; background: #eef2f7; padding: 4px 8px; border-radius: 4px; margin-right: 5px; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LES MOTEURS DE RECHERCHE EN LIGNE ---

DISCOGS_TOKEN = st.secrets.get("DISCOGS_TOKEN", "")

def fetch_discogs_api(keywords):
    if not DISCOGS_TOKEN: return []
    query = urllib.parse.quote(keywords)
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=8"
    headers = {"User-Agent": "ResellAgentIA/1.0", "Authorization": f"Discogs token={DISCOGS_TOKEN}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return [{
                "Plateforme": "Discogs API",
                "Titre": item.get("title", "Sans titre"),
                "Édition / Label": f"{item.get('label', ['N/C'])[0]} - {item.get('catno', 'N/C')} ({item.get('country', 'N/C')})",
                "Année": item.get("year", "N/C"),
                "Info Complémentaire": f"Ref: {item.get('catno', 'N/C')}"
            } for item in res.json().get("results", [])]
        return []
    except: return []

def fetch_ebay_sold(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://www.ebay.fr/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for item in soup.select(".s-item")[:10]:
            title_elem = item.select_one(".s-item__title")
            price_elem = item.select_one(".s-item__price")
            if title_elem and price_elem:
                title = title_elem.text.replace("Nouvelle annonce", "").strip()
                if "Shop on eBay" in title or "Boutique sur" in title: continue
                p_txt = price_elem.text.replace("EUR", "").replace("€", "").replace(",", ".").replace(" ", "").strip()
                if "à" in p_txt: p_txt = p_txt.split("à")[0]
                try:
                    prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                    ventes.append({"Plateforme": "eBay (Vendu)", "Titre": title, "Prix (€)": prix, "Détails": "Vente validée"})
                except: pass
        return ventes
    except: return []

def fetch_delcampe(keywords):
    query = urllib.parse.quote_plus(keywords)
    url = f"https://www.delcampe.net/fr/collections/search?term={query}&status=closed&net_prices=all&order=sale_date_desc"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for art in soup.select("div.item-listing-card") or soup.select(".item-main-infos")[:8]:
            titre = art.select_one(".item-title").text.strip() if art.select_one(".item-title") else "Objet"
            p_elem = art.select_one(".price") or art.select_one(".item-price")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                prix = float(''.join(c for c in p_txt if c.isdigit() or c == '.'))
                ventes.append({"Plateforme": "Delcampe (Vendu)", "Titre": titre, "Prix (€)": prix, "Détails": "Historique de vente"})
        return ventes
    except: return []

def fetch_rakuten(keywords):
    query = urllib.parse.quote(keywords)
    url = f"https://fr.shopping.rakuten.com/s/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        ventes = []
        for prod in soup.select("[data-qa='product_card']")[:8]:
            titre = prod.select_one("[data-qa='product_title']").text.strip() if prod.select_one("[data-qa='product_title']") else "Objet"
            p_elem = prod.select_one("[data-qa='product_price']")
            if p_elem:
                p_txt = p_elem.text.replace("€", "").replace(",", ".").replace(" ", "").strip()
                ventes.append({"Plateforme": "Rakuten", "Titre": titre, "Prix (€)": float(''.join(c for c in p_txt if c.isdigit() or c == '.')), "Détails": "Prix constaté"})
        return ventes
    except: return []

# --- 3. INTERFACE UTILISATEUR ---

with st.sidebar:
    st.title("⚙️ Spectre Secteurs")
    univers = st.radio(
        "Choisissez l'univers de vente :", 
        ("📚 Bandes Dessinées", "🎵 Disques & Vinyles", "🏺 Objets de Collection & Mag", "⌚ Montres de Collection")
    )
    st.divider()
    st.success("🤖 Analyseurs multi-sources actifs")
    st.info("📊 Traque automatique : eBay (Vendus), Rakuten, Delcampe")

st.title("⚡ ResellAgent IA")
st.subheader("Analyseur de marché global et multicritères")

# Choix de l'exemple par défaut
if univers == "📚 Bandes Dessinées": default_search = "Tramber La Grande Souris Noire"
elif univers == "🎵 Disques & Vinyles": default_search = "Prince Purple Rain Original"
elif univers == "⌚ Montres de Collection": default_search = "Seiko SKX007"
else: default_search = "Magazine Starwax"

query = st.text_input("Saisissez votre recherche (Modèle, Marque, Titre, Code-barres...) :", value=default_search)

# --- CONFIGURATION DES ACCÈS DIRECTS (TERRAIN) ---
encoded_query = urllib.parse.quote(query)
url_lbc = f"https://www.leboncoin.fr/recherche?text={encoded_query}"
url_vinted = f"https://www.vinted.fr/catalog?search_text={encoded_query}"
url_catawiki = f"https://www.catawiki.com/fr/s?q={encoded_query}"
url_chrono24 = f"https://www.chrono24.fr/search/index.htm?query={encoded_query}"

st.write("🔗 **Raccourcis de vérification directe sur le terrain :**")
cols_btn = st.columns(4)

with cols_btn[0]:
    st.markdown(f'<a href="{url_lbc}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background-color:#ff6e14; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">Core 🟠 LeBonCoin</button></a>', unsafe_allow_html=True)

with cols_btn[1]:
    st.markdown(f'<a href="{url_vinted}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background-color:#09b1ba; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🟢 Vinted</button></a>', unsafe_allow_html=True)

with cols_btn[2]:
    st.markdown(f'<a href="{url_catawiki}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background-color:#1434cb; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🔵 Catawiki</button></a>', unsafe_allow_html=True)

if univers == "⌚ Montres de Collection":
    with cols_btn[3]:
        st.markdown(f'<a href="{url_chrono24}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:38px; background-color:#333333; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">⌚ Chrono24</button></a>', unsafe_allow_html=True)

st.write(" ")
bouton_analyser = st.button("🚀 Lancer l'estimation automatique globale", type="primary", use_container_width=True)

if bouton_analyser and query:
    with st.spinner("🔄 Scan simultané des historiques de transactions..."):
        
        # Collecte globale MAXIMALISTE (Toutes les sources grattent pour toutes les catégories)
        resultats_prix = []
        resultats_prix.extend(fetch_ebay_sold(query))
        resultats_prix.extend(fetch_rakuten(query))
        resultats_prix.extend(fetch_delcampe(query)) # Maintenant actif pour TOUT (BD, Vinyles, Objets, Montres)
            
        # Calcul des statistiques financières
        if resultats_prix:
            df = pd.DataFrame(resultats_prix)
            prix_bruts = df["Prix (€)"].tolist()
            q1, q3 = np.percentile(prix_bruts, [25, 75])
            iqr = q3 - q1
            prix_nettoyes = [p for p in prix_bruts if (q1 - 1.5*iqr) <= p <= (q3 + 1.5*iqr)]
            if not prix_nettoyes: prix_nettoyes = prix_bruts
            
            mediane = round(np.median(prix_nettoyes), 2)
            plafond = round(max(prix_nettoyes), 2)
            plancher = round(min(prix_nettoyes), 2)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-box"><p style="margin:0;font-weight:bold;">ESTIMATION MÉDIANE REVENTE</p><p class="big-price">{mediane} €</p><p style="margin:0;font-size:12px;color:green;">🎯 Prix cible conseillé (Toutes plateformes)</p></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-box" style="border-left-color:#2ca02c;"><p style="margin:0;font-weight:bold;">PRIX CONSTATÉ HAUT</p><p class="big-price" style="color:#2ca02c;">{plafond} €</p><p style="margin:0;font-size:12px;">État exceptionnel / Édition rare</p></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-box" style="border-left-color:#d62728;"><p style="margin:0;font-weight:bold;">PRIX DE LIQUIDATION MIN</p><p class="big-price" style="color:#d62728;">{plancher} €</p><p style="margin:0;font-size:12px;">Seuil de sécurité d\'achat en brocante</p></div>', unsafe_allow_html=True)
            
            st.subheader("📊 Base de données des ventes réelles croisées (eBay, Rakuten, Delcampe)")
            st.dataframe(df, use_container_width=True)
        else:
            if univers != "🎵 Disques & Vinyles":
                st.warning("⚠️ Aucun prix d'adjudication récent trouvé automatiquement. Utilise les boutons de raccourcis ci-dessus pour sonder manuellement le marché.")

        # Affichage Discogs additionnel pour l'univers Vinyle
        if univers == "🎵 Disques & Vinyles":
            st.write(" ")
            st.subheader("🔍 Identification du pressage officiel (Base Mondiale Discogs)")
            resultats_vinyles = fetch_discogs_api(query)
            if resultats_vinyles:
                st.success(f"🎯 {len(resultats_vinyles)} fiches de pressages d'origine trouvées :")
                for v in resultats_vinyles:
                    with st.expander(f"🎵 {v['Titre']} ({v['Année']})"):
                        st.markdown(f"**Label / Pressage d'origine :** {v['Édition / Label']}")
                        st.markdown(f"**Infos complémentaires :** {v['Info Complémentaire']}")
                        st.markdown('<span class="vinyl-spec">Format: LP / Vinyle</span><span class="vinyl-spec">Référence certifiée</span>', unsafe_allow_html=True)
