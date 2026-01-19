import copy
from allocation_algo import solve_model
import math

def auto_bid_increment(price, min_step=0.1, pct_step=0.05):
    """
    Calcule l'incrément selon la logique auto-bid : arrondi au multiple supérieur de step
    """
    step = max(min_step, price * pct_step)
    return math.ceil(price / step) * step

def calculate_optimal_bid(buyers, products, new_buyer_name="Nouvel Acheteur"):
    buyers_copy = copy.deepcopy(buyers)
    recommendations = {}

    min_step = 0.1
    pct_step = 0.05

    for product in products:
        prod_id = product["id"]
        stock_available = product["stock"]

        # Allocation actuelle
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)

        # Stock restant pour le nouvel acheteur
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max concurrent
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy), default=0
        )

        # Quantité que le nouvel acheteur souhaite (on peut l'adapter si besoin)
        qty_desired = remaining_stock  # Ici on simule qu’il souhaite tout ce qui reste

        # Si le stock restant est suffisant pour la quantité souhaitée, on peut sécuriser dès le premier incrément
        test_price = auto_bid_increment(max_competitor_price, min_step, pct_step)

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

        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

        if alloc >= qty_desired:
            # Stock sécurisé dès le premier incrément
            recommended_price = test_price
        else:
            # Sinon, on incrémente exactement comme auto-bid jusqu'à sécuriser
            while test_price < max_competitor_price + 1000:
                test_price = auto_bid_increment(test_price, min_step, pct_step)
                temp_buyer["products"][prod_id]["current_price"] = test_price
                temp_buyer["products"][prod_id]["max_price"] = test_price

                allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
                alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

                if alloc >= qty_desired:
                    recommended_price = test_price
                    break
            else:
                # fallback si jamais on n’atteint pas la quantité
                recommended_price = max_competitor_price + 1000

        recommendations[prod_id] = {
            "recommended_price": round(recommended_price, 2),
            "recommended_qty": qty_desired,
            "remaining_stock": remaining_stock
        }

    return recommendations
