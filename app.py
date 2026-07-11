import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuration de la page (Mode Large pour optimiser l'espace visuel)
st.set_page_config(
    page_title="ResellAgent IA — Estimation Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé pour dynamiser l'affichage
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .big-price {
        font-size: 32px;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Barre Latérale (Sidebar) - Sélections globales et Paramètres
with st.sidebar:
    st.title("⚙️ Configuration")
    st.subheader("Catégorie de Recherche")
    categorie = st.radio(
        "Choisissez l'univers :",
        ("📚 Bandes Dessinées", "🎵 Disques & Vinyles")
    )
    
    st.divider()
    st.subheader("🔑 Statut des Clés API")
    st.success("eBay API : En attente de validation (24h)")
    st.info("Discogs Token : Prêt")
    
    st.divider()
    st.caption("ResellAgent IA v1.0 — Développé pour la productivité.")

# 3. Corps Principal du Dashboard
st.title("⚡ ResellAgent IA")
st.subheader("Analyse de valeur en temps réel et historique transactionnel")

# Barre de recherche principale
col_search, col_btn = st.columns([4, 1])
with col_search:
    query = st.text_input(
        "Entrez le titre, l'artiste, l'éditeur ou le code-barres :",
        value="Tramber - La Grande Souris Noire (1984)"
    )
with col_btn:
    st.write(" ") # Alignement esthétique
    bouton_analyser = st.button("🚀 Lancer l'analyse", use_container_width=True)

st.divider()

# Affichage des résultats de démonstration basés sur ton album de Tramber
if query:
    st.header(f"🔍 Résultat de l'analyse : *{query}*")
    
    # --- SECTION 1 : LES METRIQUES CLÉS (KPI) ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-box">
                <p style="margin:0; font-weight:bold; color:#555;">PRIX MÉDIAN RÉEL</p>
                <p class="big-price">31.50 €</p>
                <p style="margin:0; font-size:12px; color:green;">🎯 Zone de vente conseillée</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="metric-box" style="border-left-color: #2ca02c;">
                <p style="margin:0; font-weight:bold; color:#555;">PRIX PLAFOND (COLLECTION)</p>
                <p class="big-price" style="color:#2ca02c;">45.00 €</p>
                <p style="margin:0; font-size:12px; color:#555;">État Neuf / EO validée</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div class="metric-box" style="border-left-color: #d62728;">
                <p style="margin:0; font-weight:bold; color:#555;">PRIX PLANCHER</p>
                <p class="big-price" style="color:#d62728;">14.00 €</p>
                <p style="margin:0; font-size:12px; color:#555;">Rotation rapide / État moyen</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
            <div class="metric-box" style="border-left-color: #ff7f0e;">
                <p style="margin:0; font-weight:bold; color:#555;">INDICE DE LIQUIDITÉ</p>
                <p class="big-price" style="color:#ff7f0e;">Élevé 🔥</p>
                <p style="margin:0; font-size:12px; color:#555;">Se vend en moyenne sous 7 jours</p>
            </div>
        """, unsafe_allow_html=True)

    st.write(" ")
    
    # --- SECTION 2 : ACTION PRODUCTIVITÉ ---
    col_action1, col_action2 = st.columns([2, 3])
    with col_action1:
        st.button("📥 Exporter cette fiche vers mon inventaire Excel", type="primary", use_container_width=True)

    st.write(" ")

    # --- SECTION 3 : GRAPHIQUES ET REPARTITION ---
    tab1, tab2 = st.tabs(["📊 Graphiques de Tendance", "📋 Données Brutes par Plateforme"])
    
    with tab1:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Historique des prix constatés (6 derniers mois)")
            chart_data = pd.DataFrame(
                np.random.normal(31.5, 3, size=(20, 1)),
                columns=['Prix de vente validé (€)']
            )
            st.line_chart(chart_data)
            
        with col_g2:
            st.subheader("Volume de transactions par plateforme")
            sources_data = pd.DataFrame({
                'Plateforme': ['eBay', 'Delcampe', 'Catawiki', 'Rakuten', 'Vinted/LBC', 'Interencheres'],
                'Ventes Validées': [12, 18, 4, 25, 9, 2]
            }).set_index('Plateforme')
            st.bar_chart(sources_data)

    with tab2:
        st.subheader("Détail des dernières transactions détectées")
        mock_data = pd.DataFrame([
            {"Date": "10/07/2026", "Plateforme": "Delcampe", "Titre": "Tramber - La Grande Souris Noire EO", "Prix payé (€)": 34.00, "Statut": "Vendu"},
            {"Date": "08/07/2026", "Plateforme": "eBay", "Titre": "LA GRANDE SOURIS NOIRE - TRAMBER TBE", "Prix payé (€)": 29.00, "Statut": "Vendu"},
            {"Date": "04/07/2026", "Plateforme": "Interencheres", "Titre": "Lot de BD underground dont Tramber T2", "Prix payé (€)": 15.00, "Statut": "Adjugé"},
            {"Date": "01/07/2026", "Plateforme": "Vinted", "Titre": "BD Tramber Souris Noire Albin Michel", "Prix payé (€)": 32.00, "Statut": "Snapshot (Vendu)"},
            {"Date": "28/06/2026", "Plateforme": "Catawiki", "Titre": "William Vaurien (Tramber) - La Grande Souris Noire", "Prix payé (€)": 45.00, "Statut": "Adjugé"}
        ])
        st.dataframe(mock_data, use_container_width=True)
