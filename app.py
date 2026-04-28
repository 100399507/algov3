import streamlit as st
import pandas as pd

# Chargement des données
@st.cache_data
def load_data():
    df_stock = pd.read_csv('inventaire_10_ref.csv')
    df_offres = pd.read_csv('offres_en_attente.csv')
    return df_stock, df_offres

df_stock, df_offres = load_data()

st.title("Traidestock - Allocation Automatique")

# Fonction pour calculer l'allocation selon une stratégie donnée
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

# Préparation des stocks
stocks_dict = df_stock.set_index('ref')['stock'].to_dict()

# Définition des 3 scénarios
scenarios = {
    "Profit Maximum": (['prix'], [False]),        # Tri par prix décroissant
    "Volume Maximum": (['qte'], [False]),        # Tri par quantité décroissante
    "Priorité Acheteur": (['acheteur'], [True])  # Tri alphabétique acheteur
}

# Calculs
comparaison = {}
for nom, (critere, ordre) in scenarios.items():
    df_res = calculer_allocation(df_offres, stocks_dict, critere, ordre)
    revenu = (df_res['Prix'] * df_res['Alloué']).sum()
    comparaison[nom] = {'Revenu': revenu, 'Data': df_res}

# Interface de choix
st.subheader("Comparaison des Stratégies")
choix = st.radio("Sélectionnez la stratégie à appliquer :", list(scenarios.keys()))

# Affichage des résultats
df_final = comparaison[choix]['Data']
st.metric("Revenu total estimé", f"{comparaison[choix]['Revenu']:,.2f} €")

st.write(f"### Détail de l'allocation ({choix})")
st.table(df_final)

# Validation
if st.button("Valider et Exécuter l'allocation"):
    st.success(f"Allocation validée selon la stratégie : {choix}")
    # Ici, ajouter la logique pour sauvegarder/exporter le fichier final
