import time
import sys

# Copie le fichier sdk.py du prof dans le même dossier
# puis lance : python main.py

from python import SimeisSDK, get_dist

USERNAME = "sk3"   # ton nom de joueur
IP = "212.147.229.70"
PORT = 8080

def setup(sdk, sta):
    """Achète un vaisseau, un module, embauche l'équipage si besoin"""
    station = sdk.get_station_status(sta)
    ships_on_station = sdk.shop_list_ship(sta)

    # Si pas encore de vaisseau, on achète le moins cher
    player = sdk.get("/player/" + str(sdk.player["playerId"]))
    
    # On check via gamestats si on a déjà des vaisseaux
    gamestats = sdk.get("/gamestats")
    player_stats = gamestats.get(str(sdk.player["playerId"]), {})
    # Les vaisseaux sont dans les crews des stations pour l'instant
    # On va juste essayer de se setup

    print("=== SETUP ===")
    print(f"Argent disponible: {player['money']:.0f} cr")

    # Acheter le vaisseau le moins cher si on a assez d'argent
    cheapest_ship = ships_on_station[0]
    print(f"Vaisseau le moins cher: {cheapest_ship['price']:.0f} cr (cargo: {cheapest_ship['cargo_capacity']})")

    if player["money"] > cheapest_ship["price"]:
        print("Achat du vaisseau...")
        result = sdk.buy_ship(sta, cheapest_ship["id"])
        ship_id = result["id"]
        print(f"Vaisseau acheté ! ID: {ship_id}")

        # Acheter un module d'extraction (GasSucker pour les gaz)
        modules = sdk.get(f"/station/{sta}/shop/modules")
        print(f"Modules disponibles: {list(modules.keys())}")
        
        # GasSucker = extrait les gaz (Hydrogen, Helium etc.)
        sdk.buy_module_on_ship(sta, ship_id, "GasSucker")
        print("Module GasSucker installé !")

        # Embaucher pilote + opérateur
        pilot = sdk.hire_crew(sta, "Pilot")
        print(f"Pilote embauché: {pilot['id']}")
        
        operator = sdk.hire_crew(sta, "Operator")
        print(f"Opérateur embauché: {operator['id']}")

        # Assigner pilote au vaisseau
        ship_info = sdk.get_ship_status(ship_id)
        sdk.assign_crew_to_ship(sta, ship_id, pilot["id"], "pilot")
        print("Pilote assigné au vaisseau")

        # Assigner opérateur au module 1
        sdk.post(f"/station/{sta}/crew/assign/{operator['id']}/ship/{ship_id}/1")
        print("Opérateur assigné au module")

        # Embaucher un trader pour la station
        if not sdk.station_has_trader(sta):
            trader = sdk.hire_crew(sta, "Trader")
            sdk.assign_trader_to_station(sta, trader["id"])
            print(f"Trader assigné à la station: {trader['id']}")

        return ship_id
    else:
        print("Pas assez d'argent pour acheter un vaisseau !")
        print("Vérifie que tu as bien 72000 cr de départ")
        sys.exit(1)

def run_mining_loop(sdk, sta, ship_id):
    """Boucle principale : mine → décharge → vend → recommence"""
    
    loop = 0
    while True:
        loop += 1
        print(f"\n{'='*40}")
        print(f"BOUCLE #{loop}")
        print(f"{'='*40}")

        # --- 1. Scanner les planètes ---
        print("\n[1] Scan des planètes...")
        planets = sdk.scan_planets(sta)
        if not planets:
            print("Aucune planète trouvée !")
            time.sleep(5)
            continue

        # Choisir la planète gazeuse la plus proche
        gas_planets = [p for p in planets if not p["solid"]]
        target = gas_planets[0] if gas_planets else planets[0]
        print(f"Cible: pos={target['position']} temp={target['temperature']}K solid={target['solid']}")

        # --- 2. Acheter du carburant si besoin ---
        print("\n[2] Ravitaillement...")
        sdk.buy_fuel_for_refuel(sta, ship_id)
        sdk.refuel_ship(sta, ship_id)
        
        # Réparer si besoin
        sdk.buy_hull_for_repair(sta, ship_id)
        sdk.repair_ship(sta, ship_id)

        ship = sdk.get_ship_status(ship_id)
        print(f"Fuel: {ship['fuel_tank']:.0f}/{ship['fuel_tank_capacity']} | Hull decay: {ship['hull_decay']:.1f}")

        # --- 3. Aller à la planète ---
        print(f"\n[3] Navigation vers la planète...")
        cost = sdk.compute_travel_cost(ship_id, target["position"])
        print(f"Durée: {cost['duration']:.1f}s | Fuel: {cost['fuel_consumption']:.2f} | Hull usage: {cost['hull_usage']:.2f}")
        
        sdk.travel(ship_id, target["position"], wait_end=True)
        print("Arrivé à destination !")

        # --- 4. Extraction ---
        print("\n[4] Extraction en cours...")
        result = sdk.start_extraction(ship_id)
        fill_time = result.get("time_fill_cargo", 30)
        rates = result.get("mining_rate", {})
        print(f"Ressources extraites: {rates}")
        print(f"Temps pour remplir: {fill_time:.1f}s")
        
        # Attendre que le cargo soit plein
        print(f"Attente de {fill_time:.0f}s...")
        time.sleep(fill_time + 2)

        # --- 5. Retour et déchargement ---
        print("\n[5] Retour à la station...")
        sdk.return_station_and_unload_all(sta, ship_id)
        print("Cargo déchargé !")

        # --- 6. Vendre les ressources ---
        print("\n[6] Vente des ressources...")
        resources = sdk.get_station_resources(sta)
        prices = sdk.get_market_prices()
        
        total_earned = 0
        for res, qty in resources.items():
            if res in ("Fuel", "Hull"):  # garder pour maintenance
                continue
            if qty > 0:
                try:
                    result = sdk.sell_resource(sta, res, qty)
                    earned = result.get("added_money", 0)
                    total_earned += earned
                    print(f"  Vendu {qty:.1f} {res} → +{earned:.1f} cr")
                except Exception as e:
                    print(f"  Erreur vente {res}: {e}")

        print(f"Total gagné ce tour: {total_earned:.1f} cr")

        # Afficher le bilan
        player = sdk.get("/player/" + str(sdk.player["playerId"]))
        print(f"\nArgent total: {player['money']:.0f} cr")

        # Petite pause avant de recommencer
        time.sleep(2)


def main():
    print("Connexion au serveur Simeis...")
    sdk = SimeisSDK(USERNAME, IP, PORT)
    print("Connecté !")

    # Récupérer la station de départ
    gamestats = sdk.get("/gamestats")
    player_id = str(sdk.player["playerId"])
    player_data = gamestats[player_id]
    
    stations = player_data["stations"]
    sta = list(stations.keys())[0]
    print(f"Station: {sta}")
    print(f"Argent: {player_data['money']:.0f} cr")

    # Check si on a déjà un vaisseau
    # (les vaisseaux sont dans la crew des stations dans gamestats)
    # On essaie de setup si besoin
    ship_id_str = input("\nTu as déjà un vaisseau ? Entre son ID (ou appuie Entrée pour en acheter un): ").strip()
    
    if ship_id_str:
        ship_id = int(ship_id_str)
        print(f"Utilisation du vaisseau {ship_id}")
        ship = sdk.get_ship_status(ship_id)
        print(f"État: {ship['state']} | Fuel: {ship['fuel_tank']:.0f} | Cargo: {ship['cargo']['usage']:.0f}/{ship['cargo']['capacity']}")
    else:
        ship_id = setup(sdk, sta)
    
    print(f"\nDémarrage de la boucle de minage avec le vaisseau {ship_id}...")
    print("Appuie sur Ctrl+C pour arrêter\n")
    
    try:
        run_mining_loop(sdk, sta, ship_id)
    except KeyboardInterrupt:
        print("\n\nArrêt demandé. À bientôt !")


def print_leaderboard(sdk):
    stats = sdk.get("/gamestats")
    players = [(k, v) for k, v in stats.items()]
    players.sort(key=lambda x: x[1]["score"], reverse=True)
    
    print("\n" + "="*50)
    print("        CLASSEMENT")
    print("="*50)
    for i, (pid, p) in enumerate(players):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        print(f"{medal} {p['name']:<15} score: {p['score']:>8.2f}   argent: {p['money']:>12.0f} cr")
    print("="*50 + "\n")
    
if __name__ == "__main__":
    main()