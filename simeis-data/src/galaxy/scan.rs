use std::ops::Deref;

use serde::{Deserialize, Serialize};

use super::planet::Planet;
use super::station::StationInfo;
use super::{get_distance, SpaceCoord, SpaceObject};

#[derive(Serialize, Deserialize, Debug)]
pub struct ScanResult {
    planets: Vec<Planet>,
    stations: Vec<StationInfo>,
}

impl ScanResult {
    pub fn empty() -> ScanResult {
        ScanResult {
            planets: vec![],
            stations: vec![],
        }
    }

    pub fn add(&mut self, obj: &SpaceObject) {
        match obj {
            SpaceObject::BaseStation(station) => {
                let station = station.read().unwrap();
                self.stations.push(StationInfo::from(station.deref()));
            }
            SpaceObject::Planet(planet) => self.planets.push(planet.as_ref().clone()),
        }
    }

    pub fn get_closest_planet(&self, pos: &SpaceCoord) -> Option<Planet> {
        let mut planets = self.planets.clone();
        planets.sort_by(|a, b| {
            let dist_a = get_distance(pos, &a.position);
            let dist_b = get_distance(pos, &b.position);
            dist_a.total_cmp(&dist_b)
        });
        planets.into_iter().next()
    }
}
