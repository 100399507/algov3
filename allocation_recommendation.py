import copy
import math
from allocation_algo import solve_model


def calculate_optimal_bid(buyers, products, new_buyer_name="Nouvel Acheteur"):
    """
    Calcule pour un nouvel acheteur le prix minimal à proposer pour sécuriser
    le stock restant, avec EXACTEMENT la logique d'incrémentation de l'auto-bid.

    Règles :
    - Si le stock restant suffit → PAS d'incrément
    - Si le stock restant est insuffisant → premier incrément auto-bid obligatoire
    """

    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    # Paramètres auto-bid
    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]
        moq = product.get("seller_moq", 1)

        # -----------------------------
        # 1. Stock restant réel
        # -----------------------------
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(
            allocations.get(b["name"], {}).get(prod_id, 0)
            for b in buyers_copy
        )

        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Quantité que le nouvel acheteur peut réellement demander
        qty_desired = remaining_stock

        # -----------------------------
        # 2. Prix max concurrent
        # -----------------------------
        max_competitor_price = 0
        for b in buyers_copy:
            if prod_id in b["products"]:
                max_competitor_price = max(
                    max_competitor_price,
                    b["products"][prod_id]["max_price"]
                )

        # -----------------------------
        # 3. Test SANS incrément
        # -----------------------------
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": qty_desired,
                    "current_price": max_competitor_price,
                    "max_price": max_competitor_price,
                    "moq": moq
                }
            },
            "auto_bid": False
        }

        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

        # ✔️ Stock suffisant → on s'arrête
        if alloc >= qty_desired:
            recommendations[prod_id] = {
                "recommended_price": round(max_competitor_price, 2),
                "recommended_qty": qty_desired,
                "remaining_stock": remaining_stock
            }
            continue

        # -----------------------------
        # 4. Incrémentation auto-bid
        # -----------------------------
        step = max(min_step, max_competitor_price * pct_step)

        test_price = max_competitor_price + step
        test_price = math.ceil(test_price / step) * step

        recommended_price = None

        while test_price < max_competitor_price + 1000:
            temp_buyer["products"][prod_id]["current_price"] = test_price
            temp_buyer["products"][prod_id]["max_price"] = test_price

            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= qty_desired:
                recommended_price = test_price
                break

            test_price += step
            test_price = math.ceil(test_price / step) * step

        if recommended_price is None:
            recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": qty_desired,
            "remaining_stock": remaining_stock
        }

    return recommendations
