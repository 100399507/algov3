import streamlit as st
import pandas as pd
import copy
from allocation_algo import solve_model, run_auto_bid_aggressive
from allocation_recommendation import calculate_optimal_bid

# -----------------------------
# Produits exemples
# -----------------------------
products = [
    {"id": "P1", "name": "Produit 1", "stock": 500, "volume_multiple": 10, "starting_price": 5.0, "seller_moq": 50},
    {"id": "P2", "name": "Produit 2", "stock": 300, "volume_multiple": 20, "starting_price": 10.0, "seller_moq": 80},
]

# -----------------------------
# Session state
# -----------------------------
if "buyers" not in st.session_state:
    st.session_state.buyers = []

if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------------
# Helpers
# -----------------------------
def buyers_to_df(buyers):
    rows = []
    for b in buyers:
        for pid, p in b["products"].items():
            rows.append({
                "Acheteur": b["name"],
                "Produit": pid,
                "Qté désirée": p["qty_desired"],
                "MOQ produit": p["moq"],
                "Prix courant": p["current_price"],
                "Prix max": p["max_price"],  # Toujours valeur saisie
                "Auto-bid": b.get("auto_bid", False)
            })
    return pd.DataFrame(rows)

# -----------------------------
# Ajouter un acheteur / simuler
# -----------------------------
st.sidebar.title("➕ Ajouter / Simuler un acheteur")

with st.sidebar.form("add_buyer_form"):
    buyer_name = st.text_input("Nom acheteur")

    auto_bid = st.checkbox("Auto-bid activé", value=True)

    draft_products = {}

    for p in products:
        st.markdown(f"**{p['name']} ({p['id']})**")

        qty = st.number_input(
            f"Qté désirée – {p['id']}",
            min_value=p["seller_moq"],
            value=p["seller_moq"],
            step=5,
            key=f"qty_{p['id']}"
        )

        price = st.number_input(
            f"Prix courant – {p['id']}",
            min_value=0.0,
            value=p["starting_price"],
            key=f"price_{p['id']}"
        )

        max_price = st.number_input(
            f"Prix max – {p['id']}",
            min_value=price,
            value=price,
            key=f"max_{p['id']}"
        )

        draft_products[p["id"]] = {
            "qty_desired": qty,
            "current_price": price,
            "max_price": max_price,
            "moq": p["seller_moq"]
        }

    add_submit = st.form_submit_button("➕ Ajouter acheteur")
    simulate_submit = st.form_submit_button("🧪 Simuler allocation")


# -----------------------------
# Actions formulaire
# -----------------------------
if add_submit and buyer_name:
    st.session_state.buyers.append({
        "name": buyer_name,
        "products": copy.deepcopy(draft_products),
        "auto_bid": auto_bid
    })
    st.success(f"Acheteur {buyer_name} ajouté")

if simulate_submit:
    buyers_sim = copy.deepcopy(st.session_state.buyers)

    simulated_buyer = {
        "name": "__SIMULATION__",
        "products": draft_products,
        "auto_bid": False
    }

    buyers_sim.append(simulated_buyer)

    allocations, _ = solve_model(buyers_sim, products)

    st.session_state.simulation_result = allocations.get("__SIMULATION__", {})



# -----------------------------
# Affichage acheteurs
# -----------------------------
st.subheader("👥 Acheteurs")
if st.session_state.buyers:
    st.dataframe(buyers_to_df(st.session_state.buyers))
else:
    st.info("Aucun acheteur pour le moment.")


# -----------------------------
# Modifier le prix max des acheteurs (version compacte)
# -----------------------------
st.subheader("✏️ Modifier les prix max des acheteurs")

if st.session_state.buyers:
    for idx, buyer in enumerate(st.session_state.buyers):
        st.markdown(f"**{buyer['name']}**")
        cols = st.columns(len(products))  # Une colonne par produit
        for col, (pid, prod) in zip(cols, buyer["products"].items()):
            new_max = col.number_input(
                f"{pid}",
                min_value=prod["current_price"],
                value=prod["max_price"],
                key=f"max_{buyer['name']}_{pid}"
            )
            # Mise à jour dans session_state
            st.session_state.buyers[idx]["products"][pid]["max_price"] = new_max
            if st.session_state.buyers[idx]["products"][pid]["current_price"] > new_max:
                st.session_state.buyers[idx]["products"][pid]["current_price"] = new_max


# -----------------------------
# Lancer simulation
# -----------------------------
st.subheader("⚙️ Simulation auto-bid")
if st.button("▶️ Lancer simulation avec auto-bid"):
    buyers_copy = copy.deepcopy(st.session_state.buyers)
    history = []

    max_rounds = 30
    for iteration in range(max_rounds):
        allocations, total_ca = solve_model(buyers_copy, products)
        history.append({
            "itération": iteration+1,
            "allocations": copy.deepcopy(allocations),
            "total_ca": total_ca,
            "current_prices": {b["name"]: {pid: b["products"][pid]["current_price"] for pid in b["products"]} for b in buyers_copy},
            "max_prices": {b["name"]: {pid: b["products"][pid]["max_price"] for pid in b["products"]} for b in buyers_copy}
        })
        buyers_copy_new = run_auto_bid_aggressive(buyers_copy, products, max_rounds=1)
        if buyers_copy_new == buyers_copy:
            break
        buyers_copy = buyers_copy_new

    st.session_state.history = history

# -----------------------------
# Affichage itérations
# -----------------------------
if st.session_state.history:
    st.subheader("🕒 Itérations simulation")
    for h in st.session_state.history:
        st.markdown(f"### Itération {h['itération']}")
        alloc_rows = []
        for buyer_name, prods in h["allocations"].items():
            for pid, qty in prods.items():
                current_price = h["current_prices"][buyer_name][pid]
                max_price = h["max_prices"][buyer_name][pid]
                alloc_rows.append({
                    "Acheteur": buyer_name,
                    "Produit": pid,
                    "Prix courant": current_price,
                    "Prix max saisi": max_price,
                    "Quantité allouée": qty,
                    "CA ligne": qty * current_price
                })
        st.dataframe(pd.DataFrame(alloc_rows))
        st.metric("💰 CA total", f"{h['total_ca']:.2f} €")

# -----------------------------
# Recommandations pour nouvel acheteur
# -----------------------------
st.subheader("💡 Recommandation de prix/quantité pour un nouvel acheteur")

if st.button("📊 Calculer recommandations"):
    if not st.session_state.buyers:
        st.info("Ajoute d'abord des acheteurs existants pour calculer les recommandations.")
    else:
        # Calculer recommandations
        recs = calculate_optimal_bid(st.session_state.buyers, products, new_buyer_name="Nouvel Acheteur")
        
        rec_rows = []
        for pid, rec in recs.items():
            can_allocate_all = rec["recommended_qty"] > 0
            status_msg = "✅ Peut sécuriser le stock" if can_allocate_all else "⚠️ Pas assez de stock disponible"
            
            rec_rows.append({
                "Produit": pid,
                "Prix recommandé (€)": rec["recommended_price"],
                "Quantité recommandée": rec["recommended_qty"],
                "Stock restant": rec["remaining_stock"],
                "Status": status_msg
            })
        
        st.dataframe(pd.DataFrame(rec_rows))

# -----------------------------
# Résultat simulation
# -----------------------------
if "simulation_result" in st.session_state:
    st.subheader("🧪 Résultat de la simulation")

    rows = []
    for pid, qty in st.session_state.simulation_result.items():
        rows.append({
            "Produit": pid,
            "Quantité demandée": st.session_state[f"qty_{pid}"],
            "Quantité allouée": qty,
            "Statut": "✅ Alloué" if qty > 0 else "❌ Non alloué"
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)
