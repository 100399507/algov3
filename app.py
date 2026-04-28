import streamlit as st
import pandas as pd
import pulp

# Simulation de stock
data = {'ref': ['A', 'B', 'C'], 'stock': [100, 50, 200], 'prix_vente': [10, 20, 5]}
df_stock = pd.DataFrame(data)

st.title("Traidestock - Smart Matching MVP")

# Input acheteur
st.subheader("Votre Panier d'Achat")
refs = st.multiselect("Choisir les références", df_stock['ref'].tolist())
quantites = {ref: st.number_input(f"Quantité pour {ref}", min_value=0) for ref in refs}

if st.button("Lancer l'Optimisation"):
    # Initialisation du problème de maximisation
    prob = pulp.LpProblem("Allocation", pulp.LpMaximize)
    
    # Variables de décision
    vars = {ref: pulp.LpVariable(f"x_{ref}", 0, quantites[ref]) for ref in refs}
    
    # Objectif : Maximiser la valeur (Prix * Quantité)
    prob += pulp.lpSum([vars[ref] * df_stock.loc[df_stock['ref']==ref, 'prix_vente'].values[0] for ref in refs])
    
    # Contrainte : Ne pas dépasser le stock
    for ref in refs:
        prob += vars[ref] <= df_stock.loc[df_stock['ref']==ref, 'stock'].values[0]
        
    prob.solve()
    
    st.write("### Proposition d'allocation")
    for ref in refs:
        st.write(f"Référence {ref} : {vars[ref].varValue} unités allouées")
