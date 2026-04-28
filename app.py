import streamlit as st
import pandas as pd

# Chargement des données
@st.cache_data
def load_data():
    df_stock = pd.read_csv('inventaire_10_ref.csv')
    df_offres = pd.read_csv('offres_en_attente.csv')
    # Conversion date pour le critère "Premier arrivé, premier servi"
    df_offres['heure_offre'] = pd.to_datetime(df_offres['heure_offre'])
    return df_stock, df_offres

df_stock, df_offres = load_data()

st.title("Traidestock - Dashboard Allocation")

# --- 1. État des lieux ---
st.header("État des lieux")

# Synthèse par référence
synthese_ref = df_offres.groupby('ref').agg({
    'acheteur': 'count', 'qte': 'sum', 'prix': 'mean'
}).rename(columns={'acheteur': 'Nb Offres', 'qte': 'Qté Demandée', 'prix': 'Prix Moyen'})

stock_view = df_stock.merge(synthese_ref, on='ref', how='left').fillna(0)
stock_view['Taux écoulement'] = (stock_view['Qté Demandée'] / stock_view['stock']).apply(lambda x: f"{x:.1%}")

with st.expander("📊 Synthèse des offres par référence", expanded=True):
    st.table(stock_view)

with st.expander("📋 Liste détaillée des offres reçues"):
    st.dataframe(df_offres, use_container_width=True)

with st.expander("📦 Inventaire & Prix d'Achat Immédiat"):
    st.dataframe(df_stock, use_container_width=True)

# --- 2. Logique d'allocation ---
def calculer_allocation(df_offres, df_stock, critere_tri, ordre_tri):
    # Création d'un dictionnaire pour le prix d'achat immédiat (issu du stock)
    prix_immediat_dict = df_stock.set_index('ref')['prix_immediat'].to_dict()
    stocks_temp = df_stock.set_index('ref')['stock'].to_dict()
    
    resultats = []
    
    # On groupe par référence pour traiter les priorités
    for ref, group in df_offres.groupby('ref'):
        prix_seuil = prix_immediat_dict.get(ref, float('inf'))
        stock_dispo = stocks_temp.get(ref, 0)
        
        # Séparation : Prix >= Prix immédiat (tri heure) vs Autres (tri selon stratégie)
        immediats = group[group['prix'] >= prix_seuil].sort_values('heure_offre')
        autres = group[group['prix'] < prix_seuil].sort_values(by=critere_tri, ascending=ordre_tri)
        
        for _, row in pd.concat([immediats, autres]).iterrows():
            a_allouer = min(row['qte'], stock_dispo)
            if a_allouer > 0:
                resultats.append({
                    'Référence': ref,
                    'Acheteur': row['acheteur'],
                    'Prix': row['prix'],
                    'Alloué': a_allouer,
                    'Type': 'Immédiat' if row['prix'] >= prix_seuil else 'Standard'
                })
                stock_dispo -= a_allouer
    return pd.DataFrame(resultats)

# --- 3. Simulation ---
st.header("Simulation d'Allocation")
scenarios = {
    "Profit Maximum": (['prix'], [False]),
    "Volume Maximum": (['qte'], [False]),
    "Priorité Acheteur": (['acheteur'], [True])
}

choix = st.selectbox("Sélectionnez une stratégie pour les offres standards :", list(scenarios.keys()))
df_final = calculer_allocation(df_offres, df_stock, scenarios[choix][0], scenarios[choix][1])

st.metric("Revenu total estimé", f"{ (df_final['Prix'] * df_final['Alloué']).sum():,.2f} €")

with st.expander("🔍 Voir le détail de l'allocation", expanded=True):
    st.table(df_final)

if st.button("Valider et Exécuter"):
    st.success(f"Allocation validée avec succès !")
