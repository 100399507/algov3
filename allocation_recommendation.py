import copy
import math
from allocation_algo import solve_model

def calculate_optimal_bid(buyers, products, new_buyer_name="Nouvel Acheteur"):
    """
    Calcule pour un nouvel acheteur le prix minimal pour obtenir 100% du stock disponible,
    en appliquant la logique exacte de l'auto-bid.
    """

    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle pour les acheteurs existants
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

        # Prix max parmi les concurrents
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy), default=0
        )

        # Quantité que le nouvel acheteur souhaite
        qty_desired = remaining_stock  # On simule qu’il souhaite tout ce qui reste

        # Premier incrément auto-bid obligatoire
        step = max(min_step, max_competitor_price * pct_step)
        test_price = max_competitor_price + step
        # Arrondi au multiple de step (comme auto-bid)
        test_price = math.ceil(test_price / step) * step

        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": qty_desired,
                    "current_price": test_price,
                    "max_price": test_price,
                    "moq": product.get("seller_moq", 1)
                }
            },
            "auto_bid": False
        }

        # Test allocation pour ce premier incrément
        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

        if alloc >= qty_desired:
            # Stock sécurisé dès le premier incrément
            recommended_price = test_price
        else:
            # Sinon, incrémenter comme auto-bid jusqu'à sécuriser le stock
            while test_price < max_competitor_price + 1000:  # limite arbitraire
                test_price = max(test_price + step, math.ceil(test_price / step) * step)
                temp_buyer["products"][prod_id]["current_price"] = test_price
                temp_buyer["products"][prod_id]["max_price"] = test_price

                allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
                alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

                if alloc >= qty_desired:
                    recommended_price = test_price
                    break
            else:
                recommended_price = max_competitor_price + 1000  # fallback

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": qty_desired,
            "remaining_stock": remaining_stock
        }

    return recommendations
