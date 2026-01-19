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

        # Calcul du stock restant après allocations actuelles
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            # Stock déjà épuisé
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max parmi tous les autres acheteurs pour ce produit
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy), default=0
        )

        # Si le stock total disponible est inférieur à la quantité souhaitée,
        # on peut directement sécuriser le stock au prix minimal juste au-dessus du max concurrent
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": max_competitor_price + min_step,
                    "max_price": max_competitor_price + min_step,
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": False
        }

        # Tester allocation
        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

        if alloc >= remaining_stock:
            recommended_price = max_competitor_price + min_step
        else:
            # Sinon, on fait l'incrément progressif comme avant
            test_price = max_competitor_price
            while test_price < max_competitor_price + 1000:
                step = max(min_step, test_price * pct_step)
                next_price = test_price + step

                temp_buyer["products"][prod_id]["current_price"] = next_price
                temp_buyer["products"][prod_id]["max_price"] = next_price

                allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
                alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

                if alloc >= remaining_stock:
                    recommended_price = next_price
                    break

                test_price = next_price
            else:
                recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
