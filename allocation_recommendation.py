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
    pour obtenir 100% du stock disponible, en utilisant le même pas
    que l'auto-bid agressif pour que le résultat retombe sur le même chiffre.
    """
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle sans le nouvel acheteur
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock == 0:
            recommendations[prod_id] = {
                "recommended_price": 0.0,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max actuel parmi les autres acheteurs
        max_competitor_price = 0
        for b in buyers_copy:
            if prod_id in b["products"]:
                max_price = b["products"][prod_id]["max_price"]
                if max_price > max_competitor_price:
                    max_competitor_price = max_price

        # Départ du prix au-dessus du max concurrent
        test_price = max_competitor_price
        recommended_price = test_price

        # 0️⃣ Tester d'abord le prix de départ
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": test_price,
                    "max_price": test_price,
                    "moq": product["seller_moq"]
                }
            },
            "auto_bid": False
        }
        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)
        if alloc >= remaining_stock:
            # Le prix initial suffit
            recommended_price = test_price
        else:
            # 🔹 Sinon, incrément progressif
            while test_price < test_price + 100:  # limite haute arbitraire
                step = max(min_step, test_price * pct_step)
                next_price = round(test_price + step, 2)

                temp_buyer["products"][prod_id]["current_price"] = next_price
                allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
                alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

                if alloc >= remaining_stock:
                    recommended_price = next_price
                    break

                test_price = next_price

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
