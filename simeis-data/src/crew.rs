use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use strum::{EnumString, IntoStaticStr};

pub type CrewId = u32;

#[derive(Debug, Deserialize, Default, Serialize)]
pub struct Crew(pub BTreeMap<CrewId, CrewMember>);
impl Crew {
    pub fn sum_wages(&self) -> f64 {
        self.0.values().map(|crew| crew.wage()).sum::<f64>()
    }
}

#[derive(Debug, Deserialize, Serialize)]
pub struct CrewMember {
    pub member_type: CrewMemberType,
    pub rank: u8,
}

impl From<CrewMemberType> for CrewMember {
    fn from(member_type: CrewMemberType) -> Self {
        CrewMember {
            member_type,
            rank: 1,
        }
    }
}

impl CrewMember {
    pub fn wage(&self) -> f64 {
        let base = match self.member_type {
            CrewMemberType::Pilot => 5.0,
            CrewMemberType::Operator => 0.5,
            CrewMemberType::Trader => 2.5,
            CrewMemberType::Soldier => 1.5,
        };
        // TODO (#17)    Make the wage increase faster than rank
        base * (self.rank as f64)
    }
}

#[allow(dead_code)]
#[derive(EnumString, IntoStaticStr, Debug, Serialize, Deserialize, Clone, PartialEq, Eq)]
#[strum(ascii_case_insensitive)]
pub enum CrewMemberType {
    Pilot,
    Operator,
    Trader,
    Soldier,
}
