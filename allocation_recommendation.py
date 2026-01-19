import copy
import math
from allocation_algo import solve_model


def calculate_optimal_bid(
    buyers,
    products,
    new_buyer_name="Nouvel Acheteur",
    simulated_qty_by_product=None,
):
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    # Sécurité si non fourni
    simulated_qty_by_product = simulated_qty_by_product or {}

    # Lookup du nouvel acheteur s'il existe déjà
    buyer_lookup = {
        b["name"]: b for b in buyers_copy
    }

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]
        moq = product.get("seller_moq", 1)

        # -----------------------------
        # 1. Quantité désirée réelle
        # -----------------------------
        if prod_id in simulated_qty_by_product:
            qty_desired = simulated_qty_by_product[prod_id]
        else:
            qty_desired = (
                buyer_lookup
                .get(new_buyer_name, {})
                .get("products", {})
                .get(prod_id, {})
                .get("qty_desired", 0)
            )

        if qty_desired <= 0:
            continue

        # -----------------------------
        # 2. Stock restant
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

        target_qty = min(qty_desired, remaining_stock)

        # -----------------------------
        # 3. Prix max concurrent
        # -----------------------------
        max_competitor_price = 0
        for b in buyers_copy:
            if prod_id in b["products"]:
                max_competitor_price = max(
                    max_competitor_price,
                    b["products"][prod_id]["max_price"]
                )

        # -----------------------------
        # 4. Simulation helper
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

        # -----------------------------
        # 5. Test SANS incrément
        # -----------------------------
        if simulate(max_competitor_price) >= target_qty:
            recommendations[prod_id] = {
                "recommended_price": round(max_competitor_price, 2),
                "recommended_qty": target_qty,
                "remaining_stock": remaining_stock
            }
            continue

        # -----------------------------
        # 6. Incrémentation auto-bid
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
