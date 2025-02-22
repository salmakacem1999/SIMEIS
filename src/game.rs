use base64::prelude::{Engine, BASE64_STANDARD};
use ntex::web::types::{Json, Path};
use ntex::web::{self, HttpRequest, ServiceConfig};
use rand::RngCore;
use serde::Deserialize;
use serde_json::json;
use std::hash::{DefaultHasher, Hasher};
use std::ops::Deref;
use std::sync::RwLock;

use crate::errors::Errcode;
use crate::nav::{init_new_station, SpaceCoord};
use crate::{build_response, get_player_key, ServerState};

// Game state for a single player
#[allow(dead_code)] // DEV
pub struct Player {
    id: u64,
    name: String,
    key: String,

    station: SpaceCoord,
}

impl Player {
    pub fn new(station: SpaceCoord, req: ReqNewPlayer) -> Player {
        let mut hasher = DefaultHasher::new();
        hasher.write(req.name.as_bytes());
        let mut rng = rand::rng();
        let mut randbytes = [0; 128];
        rng.fill_bytes(&mut randbytes);
        let key = BASE64_STANDARD.encode(randbytes);
        Player {
            id: hasher.finish(),
            name: req.name,
            key,
            station,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct ReqNewPlayer {
    name: String,
}

#[web::post("/newplayer")]
async fn new_player(srv: ServerState, req: Json<ReqNewPlayer>) -> impl web::Responder {
    let station = init_new_station(srv.players.read().unwrap().deref());
    let player = Player::new(station, req.0);
    let resp = build_response(json!({
        "error": "ok",
        "playerId": player.id,
        "key": &player.key,
    }));
    srv.players
        .write()
        .unwrap()
        .insert(player.id, RwLock::new(player));
    resp
}

#[web::get("/player/{id}")]
async fn get_player(srv: ServerState, id: Path<u64>, req: HttpRequest) -> impl web::Responder {
    let Some(key) = get_player_key(&req) else {
        return Errcode::NoPlayerKey.build_resp();
    };

    let players = srv.players.read().unwrap();
    let Some(playerlck) = players.get(id.as_ref()) else {
        return Errcode::PlayerNotFound(*id).build_resp();
    };

    let player = playerlck.read().unwrap();

    #[allow(clippy::if_same_then_else)] // DEV
    if player.key == key {
        build_response(json!({
            "error": "ok",
            "name": player.name,
            "station": player.station,
        }))
    } else {
        build_response(json!({
            "error": "ok",
            "name": player.name,
            "station": player.station,
        }))
    }
}

pub fn configure(srv: &mut ServiceConfig) {
    srv.service(get_player).service(new_player);
}
