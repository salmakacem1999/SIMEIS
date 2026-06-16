"""
Tests fonctionnels pour Simeis
Lancer le serveur d'abord : cargo run --features testing
Puis : python3 tests/functional_tests.py
"""

import requests
import sys
import time
import random
import string

BASE_URL = "http://localhost:9345"


def unique_name(base):
    """Génère un nom unique pour éviter les conflits entre runs"""
    suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    return f"{base}-{suffix}"


INIT_MONEY = 72000.0

# ── Helpers ──────────────────────────────────────────────────────────────────


def headers(key):
    return {"Simeis-Key": key}


def create_player(name):
    r = requests.post(f"{BASE_URL}/player/new/{name}")
    data = r.json()
    assert data["error"] == "ok", f"Création joueur échouée: {data}"
    return data["playerId"], data["key"]


def get_player(player_id, key):
    r = requests.get(f"{BASE_URL}/player/{player_id}", headers=headers(key))
    data = r.json()
    assert data["error"] == "ok", f"get_player échoué: {data}"
    return data


def list_ships(station_id, key):
    r = requests.get(
        f"{BASE_URL}/station/{station_id}/shipyard/list", headers=headers(key)
    )
    data = r.json()
    assert data["error"] == "ok", f"list_ships échoué: {data}"
    return data["ships"]


def buy_ship(station_id, ship_id, key):
    r = requests.post(
        f"{BASE_URL}/station/{station_id}/shipyard/buy/{ship_id}", headers=headers(key)
    )
    data = r.json()
    assert data["error"] == "ok", f"buy_ship échoué: {data}"
    return data["id"]


def wait_for_server():
    for i in range(20):
        try:
            requests.get(f"{BASE_URL}/market/prices", timeout=1)
            print("Serveur prêt !")
            return
        except:
            print(f"Attente serveur... ({i+1}/20)")
            time.sleep(0.5)
    print("Serveur non disponible")
    sys.exit(1)


# ── Scénario 1 : Création de joueur ─────────────────────────────────────────


def scenario_1_creation_joueur():
    """
    On crée un joueur et on vérifie son état initial :
    - Son argent de départ est 72000
    - Il n'a pas de vaisseau
    - Un joueur test-rich a beaucoup plus d'argent
    """
    print("\n=== Scénario 1 : Création de joueur ===")

    player_id, key = create_player(unique_name("test-joueur-s1"))
    info = get_player(player_id, key)

    # Vérifier l'argent de départ
    assert (
        abs(info["money"] - INIT_MONEY) < 1.0
    ), f"Argent initial wrong: attendu {INIT_MONEY}, eu {info['money']}"
    print(f"  Argent de départ OK : {info['money']}")

    # Vérifier pas de vaisseaux
    assert len(info["ships"]) == 0, "Ne devrait pas avoir de vaisseau au départ"
    print("  Pas de vaisseau au départ OK")

    # Un joueur test-rich a plus d'argent (feature testing du jeu)
    rich_id, rich_key = create_player(unique_name("test-rich-s1"))
    rich_info = get_player(rich_id, rich_key)
    assert rich_info["money"] > INIT_MONEY * 100
    print(f"  Joueur test-rich a bien plus d'argent : {rich_info['money']}")

    print("Scénario 1 OK ✓")


# ── Scénario 2 : Achat d'un vaisseau ────────────────────────────────────────


def scenario_2_achat_vaisseau():
    """
    On achète un vaisseau et on vérifie que l'argent diminue du bon montant :
    - Créer un joueur riche
    - Lister les vaisseaux du shipyard
    - Acheter le moins cher
    - Vérifier que l'argent a diminué du prix du vaisseau
    - Vérifier que le vaisseau est bien dans notre inventaire
    """
    print("\n=== Scénario 2 : Achat d'un vaisseau ===")

    player_id, key = create_player(unique_name("test-rich-s2"))
    info = get_player(player_id, key)
    station_id = info["stations"][0]
    money_avant = info["money"]
    print(f"  Argent avant : {money_avant}")

    # Lister et acheter le vaisseau le moins cher
    ships = list_ships(station_id, key)
    ship = min(ships, key=lambda s: s["price"])
    print(f"  Vaisseau le moins cher : prix={ship['price']}")

    bought_id = buy_ship(station_id, ship["id"], key)
    print(f"  Vaisseau acheté, id={bought_id}")

    # Vérifier que l'argent a bien diminué du prix exact
    info_apres = get_player(player_id, key)
    money_apres = info_apres["money"]
    assert money_apres < money_avant, "L'argent devrait avoir diminué"
    assert (
        abs((money_avant - money_apres) - ship["price"]) < 1.0
    ), f"Mauvaise déduction: attendu {ship['price']}, eu {money_avant - money_apres}"
    print(f"  Argent après : {money_apres} (diminué de {money_avant - money_apres}) OK")

    # Vérifier que le joueur a maintenant au moins un vaisseau
    assert len(info_apres["ships"]) > 0, "Le joueur devrait avoir au moins un vaisseau"
    print("  Vaisseau dans l'inventaire OK")

    print("Scénario 2 OK ✓")


# ── Scénario 3 : Achat refusé si pas assez d'argent ─────────────────────────


def scenario_3_achat_impossible():
    """
    Un joueur normal (72000 crédits) ne peut pas acheter un vaisseau
    qui coûte plus cher que ce qu'il a :
    - Créer un joueur normal
    - Trouver le vaisseau le plus cher (le heavy)
    - Tenter de l'acheter → doit échouer
    - Vérifier que l'argent n'a PAS changé
    """
    print("\n=== Scénario 3 : Achat refusé (pas assez d'argent) ===")

    player_id, key = create_player(unique_name("test-pauvre-s3"))
    info = get_player(player_id, key)
    station_id = info["stations"][0]
    money_avant = info["money"]
    print(f"  Argent disponible : {money_avant}")

    # Le heavy ship coûte ~364000, bien plus que 72000
    ships = list_ships(station_id, key)
    ship_cher = max(ships, key=lambda s: s["price"])
    print(f"  Vaisseau le plus cher : prix={ship_cher['price']}")
    assert (
        ship_cher["price"] > money_avant
    ), "Ce test nécessite un vaisseau plus cher que l'argent du joueur"

    # Tenter l'achat → doit échouer
    r = requests.post(
        f"{BASE_URL}/station/{station_id}/shipyard/buy/{ship_cher['id']}",
        headers=headers(key),
    )
    data = r.json()
    assert data["error"] != "ok", f"L'achat devrait avoir échoué: {data}"
    print(f"  Achat refusé OK : {data['type']}")

    # L'argent ne doit pas avoir bougé
    info_apres = get_player(player_id, key)
    assert (
        abs(info_apres["money"] - money_avant) < 1.0
    ), "L'argent ne devrait pas avoir changé"
    print(f"  Argent inchangé OK : {info_apres['money']}")

    print("Scénario 3 OK ✓")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    wait_for_server()

    scenarios = [
        scenario_1_creation_joueur,
        scenario_2_achat_vaisseau,
        scenario_3_achat_impossible,
    ]

    echecs = []
    for s in scenarios:
        try:
            s()
        except Exception as e:
            print(f"ECHEC : {e}")
            echecs.append(s.__name__)

    print("\n" + "=" * 40)
    if echecs:
        print(f"ECHECS : {echecs}")
        sys.exit(1)
    else:
        print(f"Tous les scénarios OK ({len(scenarios)}/{len(scenarios)})")
