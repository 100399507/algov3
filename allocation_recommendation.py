import copy
from typing import List, Dict
from allocation_algo import solve_model

def calculate_optimal_bid(
    buyers: List[Dict],
    products: List[Dict],
    new_buyer_name: str = "Nouvel Acheteur",
    min_step: float = 0.1,
    pct_step: float = 0.05,
) -> Dict[str, Dict]:
    """
    Calcule pour un nouvel acheteur le prix et la quantité à proposer
    pour obtenir 100% du stock disponible, en simulant l'auto-bid
    sur ce nouvel acheteur uniquement.
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle sans le nouvel acheteur
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        # Si pas de stock restant, rien à recommander
        if remaining_stock <= 0:
            recommendations[prod_id] = {
                "recommended_price": 0,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix de départ : current_price minimal que peut proposer le nouvel acheteur
        competitor_prices = [
            b["products"][prod_id]["current_price"]
            for b in buyers_copy if prod_id in b["products"]
        ]
        start_price = max(competitor_prices + [product["starting_price"]])

        # Création du buyer simulé
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": start_price,
                    "max_price": start_price,  # on incrémente nous-mêmes
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": False
        }

        test_price = start_price
        final_price = test_price

        # Incrément progressif jusqu'à obtenir 100% du stock
        while test_price <= 1000:  # limite arbitraire
            temp_buyer["products"][prod_id]["current_price"] = test_price
            sim_allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            allocated_qty = sim_allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if allocated_qty >= remaining_stock:
                final_price = test_price
                break

            step = max(min_step, test_price * pct_step)
            test_price += step

        recommendations[prod_id] = {
            "recommended_price": round(final_price, 2),
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
