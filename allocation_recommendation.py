import copy
from typing import List, Dict
from allocation_algo import solve_model

def calculate_optimal_bid(
    buyers: List[Dict],
    products: List[Dict],
    new_buyer_name: str = "Nouvel Acheteur",
    starting_prices: Dict[str, Dict] = None  # draft_products du front
) -> Dict[str, Dict]:
    """
    Calcule pour un nouvel acheteur le prix et la quantité à proposer
    pour obtenir 100% du stock disponible, en tenant compte des prix max
    des autres acheteurs et en utilisant la même logique d'incrément que l'auto-bid.
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05  # même step que l'auto-bid

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle sans le nouvel acheteur
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(
            allocations[b["name"]].get(prod_id, 0) for b in buyers_copy
        )
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            # Pas de stock restant
            recommendations[prod_id] = {
                "recommended_price": 0,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix de départ : prix saisi dans le front si disponible, sinon starting_price
        test_price = starting_prices[prod_id]["current_price"] if starting_prices else product["starting_price"]
        max_price = starting_prices[prod_id]["max_price"] if starting_prices else test_price + 100  # limite arbitraire

        recommended_price = test_price  # par défaut

        # Incrément progressif jusqu'à obtenir 100% du stock
        while test_price <= max_price:
            # Créer un buyer temporaire
            temp_buyer = {
                "name": new_buyer_name,
                "products": {
                    prod_id: {
                        "qty_desired": remaining_stock,
                        "current_price": round(test_price, 2),
                        "max_price": max_price,
                        "moq": product["seller_moq"]
                    }
                },
                "auto_bid": False
            }

            # Tester allocation avec ce prix
            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= remaining_stock:
                recommended_price = round(test_price, 2)
                break

            # Incrément suivant
            step = max(min_step, test_price * pct_step)
            test_price += step

        # Quantité recommandée : tout le stock restant
        recommended_qty = remaining_stock

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": recommended_qty,
            "remaining_stock": remaining_stock
        }

    return recommendations
