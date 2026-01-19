def run_auto_bid_aggressive(
    buyers: List[Dict],
    products: List[Dict],
    max_rounds: int = 30
) -> List[Dict]:
    """
    Applique l'auto-bid avant de résoudre le solveur.
    Les prix sont augmentés progressivement jusqu'au prix minimal nécessaire
    pour obtenir l'allocation maximale possible ou la quantité désirée.
    """
    current_buyers = copy.deepcopy(buyers)
    min_step = 0.1  # pas minimal en euros
    pct_step = 0.05  # incrément en % du prix actuel

    for _ in range(max_rounds):
        changes_made = False

        # Trier les acheteurs par prix max décroissant pour prioriser les plus payants
        buyers_sorted = sorted(
            current_buyers,
            key=lambda b: max(p["max_price"] for p in b["products"].values()),
            reverse=True
        )

        # Parcours de tous les acheteurs pour incrément global par round
        for buyer in buyers_sorted:
            if not buyer.get("auto_bid", False):
                continue
            buyer_name = buyer["name"]

            for prod_id, prod_conf in buyer["products"].items():
                current_price = prod_conf["current_price"]
                max_price = prod_conf["max_price"]
                qty_desired = prod_conf["qty_desired"]

                # 1️⃣ Test max_price pour voir si l'acheteur peut obtenir plus
                prod_conf["current_price"] = max_price
                max_allocs, _ = solve_model(current_buyers, products)
                max_alloc = max_allocs[buyer_name][prod_id]

                # Si pas possible d'obtenir plus de stock, revenir au prix courant
                if max_alloc <= 0 or max_alloc <= current_price:
                    prod_conf["current_price"] = current_price
                    continue

                # 2️⃣ Déterminer la cible à atteindre
                target_alloc = min(max_alloc, qty_desired)
                test_price = current_price

                # 3️⃣ Incrément progressif jusqu'au prix minimal nécessaire
                while test_price < max_price:
                    step = max(min_step, test_price * pct_step)
                    next_price = min(test_price + step, max_price)

                    prod_conf["current_price"] = next_price
                    new_allocs, _ = solve_model(current_buyers, products)
                    new_alloc = new_allocs[buyer_name][prod_id]

                    if new_alloc >= target_alloc:
                        test_price = next_price
                        changes_made = True
                        break
                    else:
                        test_price = next_price
                        changes_made = True

                # 4️⃣ Mettre à jour le prix final
                prod_conf["current_price"] = test_price

        # Stop si aucun changement sur tous les acheteurs
        if not changes_made:
            break

    # Résolution finale pour allocations finales après auto-bid
    solve_model(current_buyers, products)
    return current_buyers
