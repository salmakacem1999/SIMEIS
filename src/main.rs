use std::{
    collections::BTreeMap,
    sync::{Arc, RwLock},
};

use ntex::web::{self, HttpRequest, HttpResponse};

mod errors;
mod game;
mod nav;
#[cfg(test)]
mod tests;

#[derive(Clone)]
pub struct ServerStateInner {
    players: Arc<RwLock<BTreeMap<u64, RwLock<game::Player>>>>,
}

pub type ServerState = ntex::web::types::State<ServerStateInner>;

impl ServerStateInner {
    pub fn init() -> ServerStateInner {
        ServerStateInner {
            players: Arc::new(RwLock::new(BTreeMap::new())),
        }
    }
}

pub fn build_response(data: serde_json::Value) -> HttpResponse {
    HttpResponse::Ok()
        .content_type("application/json")
        .json(&data)
}

pub fn get_json_key(data: &serde_json::Value, key: &'static str) -> Option<serde_json::Value> {
    let keys = key.split(".").collect::<Vec<&'static str>>();
    let serde_json::Value::Object(map) = data else {
        return None;
    };

    let key_tot = keys.len();
    let mut data = map;
    for (nk, key) in keys.into_iter().enumerate() {
        if nk == (key_tot - 1) {
            return data.get(key).cloned();
        } else {
            let inner = data.get(key)?.as_object()?;
            data = inner;
        }
    }
    unreachable!()
}

pub fn get_player_key(req: &HttpRequest) -> Option<&str> {
    for q in req.query_string().split("&") {
        if q.starts_with("key=") {
            return q.split("=").nth(1);
        }
    }
    None
}

#[web::get("/ping")]
async fn ping() -> impl web::Responder {
    build_response(serde_json::json!({ "error": "ok", "ping": "pong"}))
}

#[ntex::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();
    println!("Running on http://127.0.0.1:8080");
    let state = ServerStateInner::init();

    #[allow(clippy::redundant_closure)] // DEV
    web::HttpServer::new(move || {
        web::App::new()
            .state(state.clone())
            .service(ping)
            .configure(|srv| game::configure(srv))
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
