import streamlit as st
import pandas as pd
import pulp

# Charger les données
df_stock = pd.read_csv('data_complet.csv')

# Simulation d'acheteurs (pour le test)
acheteurs = {
    "Acheteur Pro (Score: 90)": 90,
    "Acheteur Standard (Score: 60)": 60,
    "Nouveau Client (Score: 30)": 30
}

st.title("Traidestock - Moteur d'Allocation Multi-Acheteurs")

# Interface
acheteur_choisi = st.selectbox("Qui demande le stock ?", list(acheteurs.keys()))
score_acheteur = acheteurs[acheteur_choisi]

st.subheader("Besoins du client")
demandes = {}
for i, row in df_stock.iterrows():
    demandes[row['ref']] = st.number_input(f"Qté pour {row['ref']} (Stock: {row['stock']})", min_value=0, max_value=int(row['stock']))

if st.button("Simuler l'Allocation"):
    # Logique : On priorise selon le score
    # Si le score > 80, on valide 100% de la demande
    # Si le score < 50, on applique une réduction de 20% par sécurité
    
    st.write(f"### Résultat pour {acheteur_choisi}")
    
    taux_allocation = 1.0 if score_acheteur >= 80 else 0.8
    
    results = []
    for ref, qte in demandes.items():
        alloue = int(qte * taux_allocation)
        results.append({'Ref': ref, 'Demandé': qte, 'Alloué': alloue})
    
    df_res = pd.DataFrame(results)
    st.table(df_res)
    
    if score_acheteur < 80:
        st.warning("Client à score moyen : Allocation limitée à 80% pour préserver les stocks prioritaires.")
    else:
        st.success("Client Premium : Allocation prioritaire validée !")
