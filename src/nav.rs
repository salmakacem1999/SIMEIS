use std::collections::BTreeMap;
use std::sync::RwLock;

use crate::game::Player;

pub type SpaceCoord = (u32, u32, u32);

pub fn init_new_station(_players: &BTreeMap<u64, RwLock<Player>>) -> SpaceCoord {
    // TODO (#4)    Find a point at the same distance as at least 2 other players
    (5, 3, 1)
}
