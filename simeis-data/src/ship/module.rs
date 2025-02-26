use serde::{Deserialize, Serialize};
use strum::{EnumIter, EnumString, IntoEnumIterator, IntoStaticStr};

use super::resources::Resource;
use crate::crew::{Crew, CrewId, CrewMemberType};
use crate::galaxy::planet::Planet;

pub type ShipModuleId = u16;

#[derive(
    EnumIter,
    EnumString,
    IntoStaticStr,
    Debug,
    Serialize,
    Deserialize,
    PartialEq,
    Eq,
    PartialOrd,
    Ord,
)]
#[strum(ascii_case_insensitive)]
pub enum ShipModuleType {
    Miner,
    GasSucker,
}

impl ShipModuleType {
    pub fn new_module(self) -> ShipModule {
        ShipModule {
            operator: None,
            modtype: self,
        }
    }

    pub fn get_price_buy(&self) -> f64 {
        match self {
            ShipModuleType::Miner => 1000.0,
            ShipModuleType::GasSucker => 2000.0,
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ShipModule {
    pub operator: Option<CrewId>,
    pub modtype: ShipModuleType,
}

impl ShipModule {
    pub fn compute_price(&self) -> f64 {
        0.0
    }

    // Returns
    pub fn need(&self, ctype: &CrewMemberType) -> bool {
        match self.modtype {
            ShipModuleType::Miner | ShipModuleType::GasSucker => {
                ctype == &CrewMemberType::Operator && self.operator.is_none()
            }
        }
    }

    pub fn can_extract(&self, crew: &Crew, planet: &Planet) -> Vec<(Resource, f64)> {
        let Some(ref opid) = self.operator else {
            log::debug!("No operator");
            return vec![];
        };

        let cm = crew.0.get(opid).unwrap();
        let all_resources = Resource::iter()
            .map(|r| (r, planet.resource_density(&r)))
            .filter(|(_, d)| *d > 0.0);

        match self.modtype {
            ShipModuleType::Miner => all_resources
                .filter(|(r, _)| r.mineable(cm.rank))
                .map(|(r, density)| (r, self.extraction_rate(&r, cm.rank, density)))
                .collect(),
            ShipModuleType::GasSucker => all_resources
                .filter(|(r, _)| r.suckable(cm.rank))
                .map(|(r, density)| (r, self.extraction_rate(&r, cm.rank, density)))
                .collect(),
        }
    }

    pub fn extraction_rate(&self, resource: &Resource, oprank: u8, density: f64) -> f64 {
        let d = resource.extraction_difficulty();
        density / (d / (oprank as f64))
    }
}
