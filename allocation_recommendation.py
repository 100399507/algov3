import copy
import math
from allocation_algo import solve_model

def auto_bid_increment(price, min_step=0.1, pct_step=0.05):
    """
    Calcule le prix suivant selon la logique auto-bid.
    L'incrément est max(min_step, price*pct_step),
    et on arrondit toujours au multiple supérieur de cet incrément.
    """
    step = max(min_step, price * pct_step)
    return math.ceil(price / step) * step

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

        # Quantité totale déjà allouée aux autres acheteurs
        allocations, _ = solve_model(buyers_copy, products)
        total_allocated = sum(allocations[b["name"]][prod_id] for b in buyers_copy)
        remaining_stock = max(stock_available - total_allocated, 0)

        if remaining_stock <= 0:
            # Plus de stock disponible
            recommendations[prod_id] = {
                "recommended_price": None,
                "recommended_qty": 0,
                "remaining_stock": 0
            }
            continue

        # Prix max parmi les autres acheteurs
        max_competitor_price = max(
            (b["products"][prod_id]["max_price"] for b in buyers_copy), default=0
        )

        # Premier prix à tester : juste au-dessus du max concurrent
        test_price = auto_bid_increment(max_competitor_price, min_step, pct_step)

        # Vérifier si on peut sécuriser tout le stock dès ce prix
        temp_buyer = {
            "name": new_buyer_name,
            "products": {
                prod_id: {
                    "qty_desired": remaining_stock,
                    "current_price": test_price,
                    "max_price": test_price,
                    "moq": product.get("seller_moq", 1)
                }
            },
            "auto_bid": False
        }

        allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
        alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

        if alloc >= remaining_stock:
            recommended_price = test_price
        else:
            # Sinon, on incrémente exactement comme auto-bid
            while test_price < max_competitor_price + 1000:  # limite arbitraire
                test_price = auto_bid_increment(test_price, min_step, pct_step)
                temp_buyer["products"][prod_id]["current_price"] = test_price
                temp_buyer["products"][prod_id]["max_price"] = test_price

                allocs, _ = solve_model(buyers_copy + [temp_buyer], products)
                alloc = allocs.get(new_buyer_name, {}).get(prod_id, 0)

                if alloc >= remaining_stock:
                    recommended_price = test_price
                    break
            else:
                recommended_price = max_competitor_price + 1000  # fallback

        recommendations[prod_id] = {
            "recommended_price": recommended_price,
            "recommended_qty": remaining_stock,
            "remaining_stock": remaining_stock
        }

    return recommendations
