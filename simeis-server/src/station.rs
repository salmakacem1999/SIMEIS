use std::sync::{Arc, RwLock};

use serde_json::json;
use simeis_data::{errors::Errcode, galaxy::station::Station, player::Player, ship::ShipId};

use crate::api::ApiResult;

pub fn get_idle_crew(station: Arc<RwLock<Station>>) -> ApiResult {
    Ok(json!({"idle": station.read().unwrap().idle_crew}))
}

pub fn list_shipyard_ships(station: Arc<RwLock<Station>>) -> ApiResult {
    let ships = station
        .read()
        .unwrap()
        .shipyard
        .iter()
        .map(|ship| ship.market_data())
        .collect::<Vec<serde_json::Value>>();
    Ok(json!({
        "ships": ships,
    }))
}

// TODO (#22)    Allow to sell ships
pub fn buy_ship(
    player: Arc<RwLock<Player>>,
    station: Arc<RwLock<Station>>,
    id: ShipId,
) -> ApiResult {
    let ship_opt = {
        let mut data = None;
        for (n, ship) in station.read().unwrap().shipyard.iter().enumerate() {
            if ship.id == id {
                data = Some((n, ship.compute_price()));
            }
        }
        data
    };

    let Some((index, price)) = ship_opt else {
        return Err(Errcode::ShipNotFound(id));
    };

    let money_got = player.read().unwrap().money;
    if price > money_got {
        return Err(Errcode::NotEnoughMoney(money_got, price));
    }

    let mut player = player.write().unwrap();
    let mut ship = station.write().unwrap().shipyard.remove(index);
    ship.update_perf_stats();
    ship.fuel_tank = ship.fuel_tank_capacity;
    player.money -= price;
    player.ships.insert(id, ship);

    Ok(json!({}))
}
