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
    pour obtenir 100% du stock disponible, en reproduisant exactement
    la logique de l'auto-bid pour le calcul du prix.
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    # Paramètres d'incrémentation identiques à run_auto_bid_aggressive
    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle sans le nouvel acheteur
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            # Stock déjà totalement alloué
            recommendations[prod_id] = {
                "recommended_price": 0,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max parmi les concurrents (pour démarrer au-dessus)
        max_competitor_price = 0
        for b in buyers_copy:
            max_price_b = b["products"][prod_id]["current_price"]
            if max_price_b > max_competitor_price:
                max_competitor_price = max_price_b

        # Création de l'acheteur simulé
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": max_competitor_price,  # démarrage au prix max concurrent
                    "max_price": max_competitor_price + 1000,  # très haut pour ne pas bloquer
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": False
        }

        # Incrément progressif pour atteindre 100% allocation
        test_price = temp_buyer["products"][prod_id]["current_price"]

        while True:
            # Résolution du solveur avec l'acheteur temporaire
            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            allocated = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if allocated >= remaining_stock:
                # Stock sécurisé
                recommended_price = test_price
                break

            # Step identique à auto-bid
            step = max(min_step, test_price * pct_step)
            test_price += step
            temp_buyer["products"][prod_id]["current_price"] = test_price

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
