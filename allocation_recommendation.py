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
        # Step minimal et step en pourcentage comme dans l'auto-bid
        min_step = 0.05
        pct_step = 0.02
        
        # Départ du prix au-dessus du max concurrent
        
        test_price = max_competitor_price
        while test_price < product["starting_price"] + 100:  # limite arbitraire pour éviter boucle infinie
            # Incrément progressif
            step = max(min_step, test_price * pct_step)
            next_price = test_price + step
        
            # Créer un buyer temporaire avec ce prix
            temp_buyer = {
                "name": new_buyer_name,
                "products": {
                    prod_id: {
                        "qty_desired": remaining_stock,
                        "current_price": next_price,
                        "max_price": next_price,
                        "moq": product["seller_moq"]
                    }
                },
                "auto_bid": False
            }
        
            # Tester allocation avec ce prix
            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)
        
            if alloc >= remaining_stock:
                # Stock sécurisé : on peut s'arrêter
                recommended_price = next_price
                break
        
            test_price = next_price


        # Quantité à demander : tout le stock restant
        recommended_qty = remaining_stock

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": recommended_qty,
            "remaining_stock": remaining_stock
        }

    return recommendations
