import copy
from typing import List, Dict
from allocation_algo import solve_model

def calculate_optimal_bid(
    buyers: List[Dict],
    products: List[Dict],
    new_buyer_name: str = "Nouvel Acheteur"
) -> Dict[str, Dict]:
    """
    Calcule pour un nouvel acheteur le prix et la quantité à proposer
    pour obtenir 100% du stock disponible, en appliquant le même 
    mécanisme d'incrémentation que l'auto-bid (step minimal + pourcentage).
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1     # step minimum
    pct_step = 0.05    # step en pourcentage du prix courant

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle sans le nouvel acheteur
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(
            allocations[b["name"]][prod_id] for b in buyers_copy
        )
        remaining_stock = max(stock_available - total_allocated, 0)
        if remaining_stock <= 0:
            # Pas de stock dispo
            recommendations[prod_id] = {
                "recommended_price": 0,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Départ du prix : max entre prix de départ et prix max des concurrents
        max_competitor_price = max(
            [b["products"][prod_id]["current_price"] for b in buyers_copy if prod_id in b["products"]] + [product["starting_price"]]
        )
        test_price = max_competitor_price

        # Création du nouvel acheteur simulé
        simulated_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": test_price,
                    "max_price": 1e6,  # pas de limite pour simulation
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": True
        }

        # Boucle d'incrémentation progressive
        while True:
            simulated_buyer["products"][prod_id]["current_price"] = round(test_price, 2)
            allocs, _ = solve_model(buyers_copy + [simulated_buyer], products)
            alloc_qty = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc_qty >= remaining_stock:
                # Stock sécurisé, on peut arrêter
                recommended_price = round(test_price, 2)
                break

            # Incrément progressif comme auto-bid
            step = max(min_step, test_price * pct_step)
            test_price += step

            # Sécurité pour éviter boucle infinie
            if test_price > simulated_buyer["products"][prod_id]["current_price"] + 100:
                recommended_price = round(test_price, 2)
                break

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
