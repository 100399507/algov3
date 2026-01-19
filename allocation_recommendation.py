import copy
from allocation_algo import solve_model

def calculate_optimal_bid(buyers, products, user_qtys, new_buyer_name="Nouvel Acheteur"):
    """
    Calcule pour un nouvel acheteur le prix minimal à proposer pour obtenir
    la quantité souhaitée par l'utilisateur si elle dépasse le stock restant,
    sinon aucune incrémentation automatique n'est faite.
    
    user_qtys : dict {prod_id: qty_saisie_par_utilisateur}
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        qty_desired = user_qtys.get(prod_id, 0)

        # Allocation actuelle
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        # Si la quantité saisie est ≤ stock restant, on ne fait pas d'incrémentation
        if qty_desired <= remaining_stock:
            recommendations[prod_id] = {
                "recommended_price": None,  # pas besoin d'augmenter le prix
                "recommended_qty": qty_desired,
                "remaining_stock": remaining_stock
            }
            continue

        # Sinon, la quantité souhaitée dépasse le stock restant → on calcule le prix à mettre
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy), default=0
        )

        test_price = max_competitor_price

        while test_price < max_competitor_price + 1000:  # limite arbitraire
            step = max(min_step, test_price * pct_step)
            next_price = test_price + step

            temp_buyer = {
                "name": new_buyer_name,
                "products": {
                    prod_id: {
                        "qty_desired": qty_desired,
                        "current_price": next_price,
                        "max_price": next_price,
                        "moq": product["seller_moq"]
                    }
                },
                "auto_bid": False
            }

            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= qty_desired:
                recommended_price = next_price
                break

            test_price = next_price
        else:
            recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": qty_desired,
            "remaining_stock": remaining_stock
        }

    return recommendations
