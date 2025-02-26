use rand::RngCore;
use std::collections::BTreeMap;
use std::hash::{DefaultHasher, Hasher};

use crate::errors::Errcode;
use crate::galaxy::station::{Station, StationId};
use crate::galaxy::SpaceCoord;
use crate::ship::module::{ShipModuleId, ShipModuleType};
use crate::ship::{Ship, ShipId};

const INIT_MONEY: f64 = 30000.0;

pub type PlayerId = u16;
pub type PlayerKey = [u8; 128];

// Game state for a single player
#[allow(dead_code)] // DEV
pub struct Player {
    pub id: PlayerId,
    pub key: PlayerKey,
    lost: bool,

    pub name: String,
    pub money: f64,
    pub costs: f64,

    pub stations: BTreeMap<StationId, SpaceCoord>,
    pub ships: BTreeMap<ShipId, Ship>,
}

impl Player {
    pub fn new(station: (StationId, SpaceCoord), name: String) -> Player {
        let mut hasher = DefaultHasher::new();
        hasher.write(name.as_bytes());
        let mut rng = rand::rng();
        let mut randbytes = [0; 128];
        rng.fill_bytes(&mut randbytes);

        #[allow(unused_mut)]
        let mut money = INIT_MONEY;

        #[cfg(feature = "testing")]
        if name.starts_with("test-rich") {
            money *= 10000.0;
        }
        let mut stations = BTreeMap::new();
        stations.insert(station.0, station.1);
        Player {
            key: randbytes,
            id: (hasher.finish() % (PlayerId::MAX as u64)) as PlayerId,
            lost: false,

            money,
            costs: 0.0,

            name,
            stations,
            ships: BTreeMap::new(),
        }
    }

    pub fn update_wages(&mut self, station: &Station) {
        self.costs = 0.0;
        self.costs += station.idle_crew.sum_wages();
        self.costs += self
            .ships
            .values()
            .map(|ship| ship.crew.sum_wages())
            .sum::<f64>();
    }

    pub fn update_money(&mut self, tdelta: f64) {
        self.money -= self.costs * tdelta;
        if self.money < 0.0 {
            self.lost = true;
            // TODO (#19)  What to do with its resources, ships, etc...
        }
    }

    pub fn buy_ship_module(
        &mut self,
        station_id: &StationId,
        ship_id: &ShipId,
        modtype: ShipModuleType,
    ) -> Result<ShipModuleId, Errcode> {
        let Some(station) = self.stations.get(station_id) else {
            return Err(Errcode::NoSuchStation(*station_id));
        };

        let Some(ship) = self.ships.get_mut(ship_id) else {
            return Err(Errcode::ShipNotFound(*ship_id));
        };

        if station != &ship.position {
            return Err(Errcode::ShipNotInStation);
        }

        let price = modtype.get_price_buy();
        if self.money < price {
            return Err(Errcode::NotEnoughMoney(self.money, price));
        }
        self.money -= price;
        let id = (ship.modules.len() + 1) as ShipModuleId;
        log::warn!("id: {id:?}");
        ship.modules.insert(id, modtype.new_module());
        Ok(id)
    }
}
