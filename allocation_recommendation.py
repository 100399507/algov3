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
    pour obtenir 100% du stock disponible.
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

        # Prix minimal pour surpasser la concurrence
        current_prices = [b["products"][prod_id]["current_price"] for b in buyers_copy]
        max_current_price = max(current_prices) if current_prices else product["starting_price"]
        recommended_price = max_current_price + 0.1

        recommended_qty = remaining_stock

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": recommended_qty,
            "remaining_stock": remaining_stock
        }

    return recommendations
