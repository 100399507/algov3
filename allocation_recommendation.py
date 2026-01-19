import copy
import math
from allocation_algo import solve_model


def calculate_optimal_bid(
    buyers,
    products,
    new_buyer_name="Nouvel Acheteur",
    simulated_qty_by_product=None,  # 🔑 clé métier
):
    """
    Recommandation de prix auto-bid exacte.

    Règles :
    - qty_desired peut dépasser le stock restant
    - allocation cible = min(qty_desired, remaining_stock)
    - incrément seulement si allocation impossible au prix courant
    """

    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]
        moq = product.get("seller_moq", 1)

        qty_desired = simulated_qty_by_product.get(prod_id, 0)

        # -----------------------------
        # 1. Stock restant
        # -----------------------------
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(
            allocations.get(b["name"], {}).get(prod_id, 0)
            for b in buyers_copy
        )

        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0 or qty_desired <= 0:
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": remaining_stock
            }
            continue

        target_qty = min(qty_desired, remaining_stock)

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
        # 3. Test sans incrément
        # -----------------------------
        def simulate(price):
            temp_buyer = {
                "name": new_buyer_name,
                "products": {
                    prod_id: {
                        "qty_desired": qty_desired,
                        "current_price": price,
                        "max_price": price,
                        "moq": moq
                    }
                },
                "auto_bid": False
            }

            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            return allocs.get(new_buyer_name, {}).get(prod_id, 0)

        if simulate(max_competitor_price) >= target_qty:
            recommendations[prod_id] = {
                "recommended_price": round(max_competitor_price, 2),
                "recommended_qty": target_qty,
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
            if simulate(test_price) >= target_qty:
                recommended_price = test_price
                break

            test_price += step
            test_price = math.ceil(test_price / step) * step

        if recommended_price is None:
            recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": target_qty,
            "remaining_stock": remaining_stock
        }

    return recommendations
