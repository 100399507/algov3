import streamlit as st
import pandas as pd

# Chargement des données
@st.cache_data
def load_data():
    df_stock = pd.read_csv('inventaire_10_ref.csv')
    df_offres = pd.read_csv('offres_en_attente.csv')
    return df_stock, df_offres

df_stock, df_offres = load_data()

st.title("Traidestock - Dashboard")

# --- 1. État des lieux (Sections repliables) ---
st.header("État des lieux")

# Synthèse par référence
synthese_ref = df_offres.groupby('ref').agg({
    'acheteur': 'count',
    'qte': 'sum',
    'prix': 'mean'
}).rename(columns={'acheteur': 'Nb Offres', 'qte': 'Qté Demandée', 'prix': 'Prix Moyen'})

stock_view = df_stock.merge(synthese_ref, on='ref', how='left').fillna(0)
stock_view['Taux écoulement'] = (stock_view['Qté Demandée'] / stock_view['stock']).apply(lambda x: f"{x:.1%}")

with st.expander("📊 Synthèse des offres par référence", expanded=True):
    st.table(stock_view)

with st.expander("📋 Liste détaillée des offres reçues"):
    st.dataframe(df_offres, use_container_width=True)

with st.expander("📦 Inventaire de départ"):
    st.dataframe(df_stock, use_container_width=True)

# --- 2. Logique d'allocation ---
def calculer_allocation(df_offres, stocks_restants, critere_tri, ordre_tri):
    allocation_temp = df_offres.sort_values(by=['ref'] + critere_tri, ascending=[True] + ordre_tri)
    resultats = []
    stocks_temp = stocks_restants.copy()
    
    for ref, group in allocation_temp.groupby('ref'):
        stock_dispo = stocks_temp.get(ref, 0)
        for _, row in group.iterrows():
            a_allouer = min(row['qte'], stock_dispo)
            if a_allouer > 0:
                resultats.append({
                    'Référence': ref,
                    'Acheteur': row['acheteur'],
                    'Prix': row['prix'],
                    'Alloué': a_allouer
                })
                stock_dispo -= a_allouer
    return pd.DataFrame(resultats)

stocks_dict = df_stock.set_index('ref')['stock'].to_dict()
scenarios = {
    "Profit Maximum": (['prix'], [False]),
    "Volume Maximum": (['qte'], [False]),
    "Priorité Acheteur": (['acheteur'], [True])
}

comparaison = {}
for nom, (critere, ordre) in scenarios.items():
    df_res = calculer_allocation(df_offres, stocks_dict, critere, ordre)
    revenu = (df_res['Prix'] * df_res['Alloué']).sum()
    comparaison[nom] = {'Revenu': revenu, 'Data': df_res}

# --- 3. Simulation ---
st.header("Simulation d'Allocation")
choix = st.selectbox("Sélectionnez une stratégie :", list(scenarios.keys()))
st.metric("Revenu total estimé", f"{comparaison[choix]['Revenu']:,.2f} €")

with st.expander("🔍 Voir le détail de l'allocation sélectionnée", expanded=True):
    st.table(comparaison[choix]['Data'])

if st.button("Valider et Exécuter"):
    st.success(f"Allocation validée avec la stratégie : {choix}")
