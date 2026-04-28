import streamlit as st
import pandas as pd

# Chargement
df_stock = pd.read_csv('inventaire_10_ref.csv')
df_offres = pd.read_csv('offres_en_attente.csv')

st.title("Traidestock - Allocation Automatique")

# 1. Calcul du score de profitabilité par offre (Prix * Quantité)
df_offres['score_profit'] = df_offres['prix'] * df_offres['qte']

# 2. Logique d'allocation (Tri par prix décroissant par référence)
# On donne la priorité aux acheteurs qui paient le plus cher
allocation = df_offres.sort_values(['ref', 'prix'], ascending=[True, False])

st.write("### Recommandation d'Allocation par Acheteur")

# On alloue le stock aux meilleurs offreurs
resultats = []
stocks_restants = df_stock.set_index('ref')['stock'].to_dict()

for ref, group in allocation.groupby('ref'):
    stock_dispo = stocks_restants.get(ref, 0)
    for index, row in group.iterrows():
        a_allouer = min(row['qte'], stock_dispo)
        if a_allouer > 0:
            resultats.append({
                'Référence': ref,
                'Acheteur': row['acheteur'],
                'Prix': row['prix'],
                'Alloué': a_allouer
            })
            stock_dispo -= a_allouer

df_allocation = pd.DataFrame(resultats)
st.table(df_allocation)

# 3. Stats pour le vendeur (No-Touch Dashboard)
st.write("### Analyse du gain (Revenu Total)")
total_revenue = (df_allocation['Prix'] * df_allocation['Alloué']).sum()
st.metric("Revenu total optimisé", f"{total_revenue:,.2f} €")

if st.button("Valider et Exécuter l'allocation"):
    st.success("Allocation envoyée aux acheteurs (Mode No-Touch activé).")
