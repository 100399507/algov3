import streamlit as st
import pandas as pd
import copy
from allocation_algo import solve_model, run_auto_bid_aggressive
from allocation_recommendation import simulate_optimal_bid

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
                "Prix max": p["max_price"],
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
    for idx_p, p in enumerate(products):
        st.markdown(f"**{p['name']} ({p['id']})**")

        multiple = p["volume_multiple"]
        min_qty = max(p["seller_moq"], multiple)

        # Quantité désirée
        qty = st.number_input(
            f"Qté désirée – {p['id']}",
            min_value=min_qty,
            max_value=p["stock"],
            value=min_qty,
            step=multiple,
            key=f"qty_{p['id']}_{idx_p}"
        )

        # Prix courant minimal
        current_price_min = p["starting_price"]
        if st.session_state.buyers:
            allocated_prices = [
                b["products"][p["id"]]["current_price"]
                for b in st.session_state.buyers
                if p["id"] in b["products"] and b.get("allocated", {}).get(p["id"], 0) > 0
            ]
            if allocated_prices:
                current_price_min = min(allocated_prices)
    
        # Calcul du prix courant minimum parmi les acheteurs ayant du stock alloué
        allocated_prices = [
            b["products"][p["id"]]["current_price"]
            for b in st.session_state.buyers
            if p["id"] in b["products"] and b.get("allocated", {}).get(p["id"], 0) > 0
        ]
        if allocated_prices:
            current_price_min = max(allocated_prices)  # prix courant minimum pour démarrer
        else:
            current_price_min = p["starting_price"]
    
        # Affichage prix courant pour info mais non modifiable
        price = st.number_input(
            f"Prix minimum d'enchère – {p['id']}",
            min_value=current_price_min,
            value=current_price_min,
            step=0.5,
            key=f"price_{p['id']}_{idx_p}",
            disabled=True  # 🔹 affiché mais pas modifiable
        )

        # Prix max
        max_price = st.number_input(
            f"Prix max – {p['id']}",
            min_value=price,
            value=price,
            step=0.5,
            key=f"max_{p['id']}_{idx_p}"
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

if simulate_submit and buyer_name:
    # Copie isolée pour simulation
    buyers_sim = copy.deepcopy(st.session_state.buyers)

    # Ajouter l'acheteur simulé
    simulated_buyer = {
        "name": "__SIMULATION__",
        "products": copy.deepcopy(draft_products),
        "auto_bid": True
    }
    buyers_sim.append(simulated_buyer)

    # Lancer auto-bid uniquement sur la copie
    buyers_sim = run_auto_bid_aggressive(buyers_sim, products, max_rounds=5)

    # Allocation finale du simulateur
    allocations, _ = solve_model(buyers_sim, products)
    sim_alloc = allocations.get("__SIMULATION__", {})

    # Calcul du % alloué et affichage
    sim_rows = []
    for pid, prod in draft_products.items():
        qty_desired = prod["qty_desired"]
        qty_allocated = sim_alloc.get(pid, 0)
        pct_alloc = (qty_allocated / qty_desired) * 100 if qty_desired > 0 else 0

        sim_rows.append({
            "Produit": pid,
            "Prix courant simulé (€)": buyers_sim[-1]["products"][pid]["current_price"],
            "Prix max simulé (€)": buyers_sim[-1]["products"][pid]["max_price"],
            "Quantité simulée": qty_allocated,
            "% alloué": f"{pct_alloc:.1f} %"
        })

    st.subheader(f"🧪 Simulation pour {buyer_name}")
    st.dataframe(pd.DataFrame(sim_rows), use_container_width=True)

    # -----------------------------
    # Recommandation automatique pour sécuriser 100%
    # -----------------------------
    user_qtys = {pid: prod["qty_desired"] for pid, prod in draft_products.items()}
    user_prices = {pid: prod["current_price"] for pid, prod in draft_products.items()}
    
    recs = simulate_optimal_bid(
        st.session_state.buyers,
        products,
        user_qtys=user_qtys,
        user_prices=user_prices,
        new_buyer_name=buyer_name,  # optionnel, tu peux laisser le défaut "__SIMULATION__"
    )


    rec_rows = []
    for pid, rec in recs.items():
        rec_rows.append({
            "Produit": pid,
            "Prix recommandé pour 100% allocation (€)": rec["recommended_price"]
        })
    st.subheader(f"💡 Recommandation pour {buyer_name} (obtenir 100% du stock)")
    st.dataframe(pd.DataFrame(rec_rows), use_container_width=True)


# -----------------------------
# Produits en vente
# -----------------------------
st.subheader("📦 Produits en vente")
product_rows = []
for p in products:
    product_rows.append({
        "Produit": f"{p['name']} ({p['id']})",
        "Stock total": p["stock"],
        "Multiple de volume": p["volume_multiple"],
        "Prix de départ (€)": p["starting_price"],
        "MOQ vendeur": p["seller_moq"]
    })
st.dataframe(pd.DataFrame(product_rows), use_container_width=True)

# -----------------------------
# Affichage acheteurs
# -----------------------------
st.subheader("👥 Acheteurs")
if st.session_state.buyers:
    st.dataframe(buyers_to_df(st.session_state.buyers))
else:
    st.info("Aucun acheteur pour le moment.")

# -----------------------------
# Modifier le prix max des acheteurs (clé unique)
# -----------------------------
st.subheader("✏️ Modifier les prix max des acheteurs")
if st.session_state.buyers:
    for idx_b, buyer in enumerate(st.session_state.buyers):
        st.markdown(f"**{buyer['name']}**")
        cols = st.columns(len(products))
        for idx_p, (col, (pid, prod)) in enumerate(zip(cols, buyer["products"].items())):
            widget_key = f"max_{buyer['name']}_{pid}_{idx_b}_{idx_p}"
            new_max = col.number_input(
                f"{pid}",
                min_value=prod["current_price"],
                value=prod["max_price"],
                step=0.5,
                key=widget_key
            )
            st.session_state.buyers[idx_b]["products"][pid]["max_price"] = new_max
            if st.session_state.buyers[idx_b]["products"][pid]["current_price"] > new_max:
                st.session_state.buyers[idx_b]["products"][pid]["current_price"] = new_max

# -----------------------------
# Lancer simulation auto-bid
# -----------------------------
st.subheader("⚙️ Simulation auto-bid")
if st.button("▶️ Lancer simulation avec auto-bid"):
    buyers_copy = copy.deepcopy(st.session_state.buyers)
    history = []
    max_rounds = 30

    for iteration in range(max_rounds):
        allocations, total_ca = solve_model(buyers_copy, products)
        history.append({
            "itération": iteration + 1,
            "allocations": copy.deepcopy(allocations),
            "total_ca": total_ca,
            "current_prices": {
                b["name"]: {pid: b["products"][pid]["current_price"] for pid in b["products"]}
                for b in buyers_copy
            },
            "max_prices": {
                b["name"]: {pid: b["products"][pid]["max_price"] for pid in b["products"]}
                for b in buyers_copy
            }
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
# Recommandations pour nouvel acheteur simplifiées
# -----------------------------
st.subheader("💡 Recommandation de prix pour un nouvel acheteur")
if st.button("📊 Calculer recommandations"):
    if not st.session_state.buyers:
        st.info("Ajoute d'abord des acheteurs existants pour calculer les recommandations.")
    else:
        recs = calculate_optimal_bid(st.session_state.buyers, products, new_buyer_name="Nouvel Acheteur")
        rec_rows = []
        for pid, rec in recs.items():
            rec_rows.append({
                "Produit": pid,
                "Prix recommandé (€)": rec["recommended_price"]
            })
        st.dataframe(pd.DataFrame(rec_rows), use_container_width=True)
