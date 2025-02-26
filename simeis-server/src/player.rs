use std::{
    ops::Deref,
    sync::{Arc, RwLock},
};

use base64::{prelude::BASE64_STANDARD, Engine};
use serde_json::json;
use simeis_data::{
    errors::Errcode,
    player::{Player, PlayerId, PlayerKey},
    ship::Ship,
};

use crate::{api::ApiResult, GameState};

pub fn new_player(srv: GameState, name: String) -> ApiResult {
    for (_, player) in srv.players.read().unwrap().iter() {
        if name == player.read().unwrap().deref().name {
            return Err(Errcode::PlayerAlreadyExists(name));
        }
    }

    let station = srv.galaxy.init_new_station();
    let player = Player::new(station, name);
    let resp = json!({
        "playerId": player.id,
        "key": &BASE64_STANDARD.encode(player.key),
    });
    srv.player_index
        .write()
        .unwrap()
        .insert(player.key, player.id);
    srv.players
        .write()
        .unwrap()
        .insert(player.id, Arc::new(RwLock::new(player)));
    Ok(resp)
}

pub fn get_player(srv: GameState, id: PlayerId, key: PlayerKey) -> ApiResult {
    let players = srv.players.read().unwrap();
    let Some(playerlck) = players.get(&id) else {
        return Err(Errcode::PlayerNotFound(id));
    };

    let player = playerlck.read().unwrap();

    #[allow(clippy::if_same_then_else)] // DEV
    if player.key == key {
        Ok(json!({
            "id": id,
            "name": player.name,
            "stations": player.stations,
            "money": player.money,
            "ships": serde_json::to_value(
                player.ships.values().collect::<Vec<&Ship>>()
            ).unwrap(),
            "costs": player.costs,
        }))
    } else {
        Ok(json!({
            "id": id,
            "name": player.name,
            "stations": player.stations,
        }))
    }
}
