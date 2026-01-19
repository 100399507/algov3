import copy
from allocation_algo import solve_model

def calculate_optimal_bid(buyers, products, new_buyer_name="Nouvel Acheteur"):
    """
    Calcule pour un nouvel acheteur le prix minimal à proposer pour obtenir
    100% du stock disponible, en tenant compte des prix max des autres acheteurs
    et en appliquant la même logique d'incrémentation que l'auto-bid.
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    # Paramètres d'incrémentation identiques à l'auto-bid
    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Quantité totale que le nouvel acheteur souhaite (tout le stock restant)
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)
        if remaining_stock <= 0:
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max parmi tous les autres acheteurs pour ce produit
        max_competitor_price = 0
        for b in buyers_copy:
            max_price = b["products"][prod_id]["max_price"]
            if max_price > max_competitor_price:
                max_competitor_price = max_price

        # On commence juste au-dessus du max competitor
        test_price = max_competitor_price

        while test_price < max_competitor_price + 1000:  # limite arbitraire
            # Incrément progressif
            step = max(min_step, test_price * pct_step)
            next_price = test_price + step

            # On crée le buyer temporaire avec ce prix
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

            # Tester allocation
            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= remaining_stock:
                # Stock sécurisé : on peut s'arrêter
                recommended_price = next_price
                break

            test_price = next_price
        else:
            # Si jamais on n'atteint pas le stock (limite arbitr.), on met max
            recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
