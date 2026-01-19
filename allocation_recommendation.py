import copy
from typing import List, Dict
from allocation_algo import solve_model

def calculate_optimal_bid(buyers: List[Dict], products: List[Dict], new_buyer_name: str = "Nouvel Acheteur") -> Dict[str, Dict]:
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.05
    pct_step = 0.02  # même que auto-bid

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

        # Prix max parmi concurrents
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy if prod_id in b["products"]),
            default=0
        )

        # Commencer au prix max concurrent
        test_price = max_competitor_price
        recommended_price = test_price

        while test_price < max_competitor_price + 100:
            step = max(min_step, test_price * pct_step)
            next_price = test_price + step

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

            allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
            alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

            if alloc >= remaining_stock:
                recommended_price = next_price
                break

            test_price = next_price

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
