import streamlit as st
import pandas as pd

# Chargement des données
df_stock = pd.read_csv('inventaire_10_ref.csv')
df_offres = pd.read_csv('offres_en_attente.csv')

st.title("Traidestock - Smart Matching MVP")

# Saisie de la nouvelle offre
st.sidebar.header("Nouvelle Offre Acheteur")
acheteur = st.sidebar.selectbox("Acheteur", ["Acheteur_A", "Acheteur_B", "Acheteur_C"])
ref = st.sidebar.selectbox("Référence", df_stock['ref'].unique())
prix = st.sidebar.number_input("Prix unitaire proposé")
qte = st.sidebar.number_input("Quantité demandée")

if st.sidebar.button("Analyser et Allouer"):
    # Calcul du prix moyen du marché (offres des autres acheteurs)
    marche = df_offres[df_offres['ref'] == ref]
    prix_moyen = marche['prix'].mean() if not marche.empty else df_stock.loc[df_stock['ref']==ref, 'prix_plancher'].values[0]
    
    st.write(f"### Analyse pour {ref}")
    st.metric("Prix moyen du marché", f"{prix_moyen:.2f} €")
    st.metric("Votre offre", f"{prix:.2f} €")

    # Logique de recommandation NO-TOUCH
    if prix >= prix_moyen:
        st.success("✅ RECOMMANDATION : Validation automatique (No-Touch).")
    elif prix >= prix_moyen * 0.95:
        st.info("ℹ️ RECOMMANDATION : Négoce léger possible (Alignement 98%).")
    else:
        st.warning("⚠️ RECOMMANDATION : Contre-proposition nécessaire (Prix trop bas).")

# Dashboard de répartition
st.write("### État du carnet d'ordres par référence")
st.table(df_offres.groupby('ref').agg({'prix': 'mean', 'qte': 'sum'}))
