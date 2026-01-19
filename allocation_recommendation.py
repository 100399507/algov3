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
    pour obtenir 100% du stock disponible, en appliquant la même
    logique que l'auto-bid (incrément progressif).
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
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        # Commencer au prix de départ (starting_price ou min_price que tu veux tester)
        test_price = product.get("starting_price", 0)

        # Créer un buyer temporaire avec ce prix
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": test_price,
                    "max_price": test_price + 100,  # limite arbitraire haute
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": False
        }

        # Incrément progressif jusqu'à obtenir 100% du stock restant
        while test_price <= temp_buyer["products"][prod_id]["max_price"]:
            temp_buyer["products"][prod_id]["current_price"] = test_price
            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= remaining_stock:
                # Stock sécurisé, on peut s'arrêter
                break

            # incrément suivant
            step = max(min_step, test_price * pct_step)
            test_price += step

        # Arrondir au centième
        recommended_price = round(test_price, 2)

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
