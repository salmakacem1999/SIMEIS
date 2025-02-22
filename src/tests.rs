use crate::get_json_key;

#[test]
fn test_get_json_by_key() {
    let data = serde_json::json!({
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": 3,
                    }
                }
            },
            "f": {
                "g": 5,
            }
        }
    });

    assert_eq!(
        get_json_key(&data, "a.b.c.d.e")
            .map(|v| v.as_number().map(|v| v.as_u64()).flatten())
            .flatten(),
        Some(3)
    );

    assert_eq!(
        get_json_key(&data, "a.f.g")
            .map(|v| v.as_number().map(|v| v.as_u64()).flatten())
            .flatten(),
        Some(5)
    );

    assert!(get_json_key(&data, "a.b.c.d.e.f").is_none());
    assert!(get_json_key(&data, "a.b").is_some());
    assert!(get_json_key(&data, "a.b.x").is_none());
}
