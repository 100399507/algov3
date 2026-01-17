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
    pour obtenir 100% du stock disponible, en tenant compte des prix max
    des autres acheteurs afin que l'auto-bid ne le dépasse pas.
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

        # Prix max actuel parmi les autres acheteurs
        max_competitor_price = 0
        for b in buyers_copy:
            current_price = b["products"][prod_id]["current_price"]
            max_price = b["products"][prod_id]["max_price"]
            # L'auto-bid peut pousser jusqu'à max_price
            if max_price > max_competitor_price:
                max_competitor_price = max_price

        # Prix recommandé légèrement au-dessus du max concurrent
        recommended_price = max_competitor_price + 0.1

        # Quantité à demander : tout le stock restant
        recommended_qty = remaining_stock

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": recommended_qty,
            "remaining_stock": remaining_stock
        }

    return recommendations
