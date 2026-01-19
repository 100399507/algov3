import pulp
import copy
from typing import Dict, List, Tuple

# -----------------------------
# Fonctions principales
# -----------------------------

def round_to_multiple(value: float, multiple: int) -> int:
    if multiple <= 0:
        return int(value)
    return int(round(value / multiple) * multiple)

def solve_model(
    buyers: List[Dict],
    products: List[Dict],
    seller_global_moq: int = 80
) -> Tuple[Dict, float]:
    """Résout le modèle multi-produits avec MOQ Global"""
    if not buyers:
        return {}, 0.0

    model = pulp.LpProblem("Sequential_Auction", pulp.LpMaximize)

    x = {}
    y = {}
    z = {}
    n_mult = {}

    # Variables
    for buyer in buyers:
        buyer_name = buyer["name"]
        z[buyer_name] = pulp.LpVariable(f"z_{buyer_name}", lowBound=0, upBound=1, cat="Binary")

        for product in products:
            prod_id = product["id"]
            x[(buyer_name, prod_id)] = pulp.LpVariable(f"x_{buyer_name}_{prod_id}", lowBound=0)
            y[(buyer_name, prod_id)] = pulp.LpVariable(f"y_{buyer_name}_{prod_id}", lowBound=0, upBound=1, cat="Binary")
            n_mult[(buyer_name, prod_id)] = pulp.LpVariable(f"n_{buyer_name}_{prod_id}", lowBound=0, cat="Integer")

    # Fonction objectif
    revenue_terms = []
    for buyer in buyers:
        for prod_id in buyer["products"]:
            buyer_name = buyer["name"]
            price = buyer["products"][prod_id]["current_price"]
            revenue_terms.append(price * x[(buyer_name, prod_id)])
    model += pulp.lpSum(revenue_terms)

    # Contraintes par produit
    for product in products:
        prod_id = product["id"]
        volume_multiple = product["volume_multiple"]
        stock_terms = [x[(b["name"], prod_id)] for b in buyers]
        if stock_terms:
            model += pulp.lpSum(stock_terms) <= product["stock"]
        for buyer in buyers:
            model += x[(buyer["name"], prod_id)] == volume_multiple * n_mult[(buyer["name"], prod_id)]

    # Contraintes par acheteur
    for buyer in buyers:
        buyer_name = buyer["name"]
        total_alloc_terms = [x[(buyer_name, prod_id)] for prod_id in buyer["products"]]
        model += pulp.lpSum(total_alloc_terms) >= seller_global_moq * z[buyer_name]

        for prod_id, prod_conf in buyer["products"].items():
            big_m = 10000
            model += x[(buyer_name, prod_id)] <= big_m * z[buyer_name]
            model += x[(buyer_name, prod_id)] >= prod_conf["moq"] * y[(buyer_name, prod_id)]
            model += x[(buyer_name, prod_id)] <= prod_conf["qty_desired"] * y[(buyer_name, prod_id)]
            model += y[(buyer_name, prod_id)] <= z[buyer_name]

    # Résolution
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    allocations = {}
    total_ca = 0.0

    for buyer in buyers:
        allocations[buyer["name"]] = {}
        buyer_total = 0

        for prod_id in buyer["products"]:
            alloc_value = x[(buyer["name"], prod_id)].value() or 0
            volume_multiple = next(p["volume_multiple"] for p in products if p["id"] == prod_id)
            alloc_value = round_to_multiple(alloc_value, volume_multiple)
            buyer_total += alloc_value

        if buyer_total < seller_global_moq:
            for prod_id in buyer["products"]:
                allocations[buyer["name"]][prod_id] = 0
        else:
            for prod_id in buyer["products"]:
                alloc_value = x[(buyer["name"], prod_id)].value() or 0
                volume_multiple = next(p["volume_multiple"] for p in products if p["id"] == prod_id)
                alloc_value = round_to_multiple(alloc_value, volume_multiple)
                allocations[buyer["name"]][prod_id] = alloc_value
                total_ca += alloc_value * buyer["products"][prod_id]["current_price"]

    return allocations, total_ca

# -----------------------------
# Auto-bid agressif
# -----------------------------
def run_auto_bid_aggressive(
    buyers: List[Dict],
    products: List[Dict],
    max_rounds: int = 30
) -> List[Dict]:
    """
    Augmente les prix pour atteindre allocations optimales.
    Ne dépasse jamais max_price.
    """
    current_buyers = copy.deepcopy(buyers)

    for _ in range(max_rounds):
        allocations, _ = solve_model(current_buyers, products)
        changes_made = False

        for buyer in current_buyers:
            if not buyer.get("auto_bid", False):
                continue
            buyer_name = buyer["name"]

            for prod_id, prod_conf in buyer["products"].items():
                qty_desired = prod_conf["qty_desired"]
                current_price = prod_conf["current_price"]
                max_price = prod_conf["max_price"]
                current_alloc = allocations[buyer_name][prod_id]

                if current_alloc >= qty_desired or current_price >= max_price:
                    continue

            best_price = current_price
            # -----------------------------
            # Parcours des acheteurs par prix max décroissant
            # -----------------------------
            # Trier les acheteurs selon le prix max le plus élevé parmi leurs produits
            buyers_sorted = sorted(
                current_buyers,
                key=lambda b: max(p["max_price"] for p in b["products"].values()),
                reverse=True
            )
            
            for buyer in buyers_sorted:
                if not buyer.get("auto_bid", False):
                    continue
                buyer_name = buyer["name"]
            
                for prod_id, prod_conf in buyer["products"].items():
                    qty_desired = prod_conf["qty_desired"]
                    current_price = prod_conf["current_price"]
                    max_price = prod_conf["max_price"]
            
                    # allocation actuelle
                    allocations, _ = solve_model(current_buyers, products)
                    current_alloc = allocations[buyer_name][prod_id]
            
                    # 1️⃣ Test max_price pour voir si l'acheteur peut obtenir plus
                    prod_conf["current_price"] = max_price
                    max_allocations, _ = solve_model(current_buyers, products)
                    max_alloc = max_allocations[buyer_name][prod_id]
            
                    if max_alloc <= current_alloc:
                        # pas besoin de bid, max_price n'améliore pas
                        prod_conf["current_price"] = current_price
                        continue
            
                    # 2️⃣ Incrément progressif jusqu'au prix minimal nécessaire
                    target_alloc = max_alloc
                    test_price = current_price
                    min_step = 0.1
                    pct_step = 0.05
            
                    while test_price < max_price:
                        step = max(min_step, test_price * pct_step)
                        next_price = min(test_price + step, max_price)
            
                        prod_conf["current_price"] = next_price
                        new_allocs, _ = solve_model(current_buyers, products)
                        new_alloc = new_allocs[buyer_name][prod_id]
            
                        if new_alloc >= target_alloc:
                            test_price = next_price
                            break
                        else:
                            test_price = next_price
            
                    # 3️⃣ Mettre à jour le prix final
                    prod_conf["current_price"] = test_price
            
            
                            prod_conf["current_price"] = min(best_price, max_price)

        if not changes_made:
            break

    return current_buyers
