#![allow(unexpected_cfgs)]
use actix_web::middleware::Logger;

use simeis_data::game::Game;

mod api;

pub type GameState = actix_web::web::Data<Game>;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    #[cfg(not(feature = "testing"))]
    let port = 8080;

    #[cfg(feature = "testing")]
    let port = 9345;

    env_logger::builder()
        .parse_default_env()
        .filter_module("actix_web_server", log::LevelFilter::Warn)
        .filter_module("actix_web_io", log::LevelFilter::Warn)
        .filter_module("actix_web_rt", log::LevelFilter::Warn)
        .filter_module("actix_web::http::h1", log::LevelFilter::Warn)
        .init();

    log::info!("Running on http://0.0.0.0:{port}");
    let (gamethread, state) = Game::init();
    let game = state.clone();

    let res = actix_web::HttpServer::new(move || {
        actix_web::App::new()
            .wrap(Logger::default())
            .app_data(state.clone())
            .configure(api::configure)
    })
    // .stop_runtime()
    .bind(("0.0.0.0", port))?
    .run()
    .await;

    game.stop(gamethread).await;
    res
}

#[cfg(feature = "heavy_testing")]
#[test]
fn test_heavy_testing() {
    assert!(false);
}
