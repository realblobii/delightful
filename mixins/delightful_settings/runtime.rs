// Delightful's settings: which add-ons are on. No game types, so this is plain Rust (`rustc --test runtime.rs`).
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};

/// This native mod's id: its settings page and its saved settings are under it.
pub const ID: &str = "delightful_settings";

/// The add-ons that can be switched: resource namespace and display name. The base mod (`farmersdelight`) cannot be.
pub const ADDONS: [(&str, &str); 4] = [
    ("brewinandchewin", "Brewin' And Chewin'"),
    ("rusticdelight", "Rustic Delight"),
    ("expandeddelight", "Expanded Delight"),
    ("corn_delight", "Corn Delight"),
];

static MASK: AtomicU32 = AtomicU32::new(0);
static LOADED: AtomicBool = AtomicBool::new(false);

/// The saved setting's key for add-on `i`.
pub fn key(i: usize) -> String {
    format!("enable_{}", ADDONS[i].0)
}

/// An add-on is on unless its setting says `false`: all are on by default.
pub fn on(saved: Option<&str>) -> bool {
    saved != Some("false")
}

pub fn label(i: usize, on: bool) -> String {
    format!("{}: {}", ADDONS[i].1, if on { "ON" } else { "OFF" })
}

/// Bit `i` set means add-on `i` is off.
pub fn loaded() -> bool {
    LOADED.load(Ordering::Relaxed)
}
pub fn mask() -> u32 {
    MASK.load(Ordering::Relaxed)
}
pub fn set_mask(mask: u32) {
    MASK.store(mask, Ordering::Relaxed);
    LOADED.store(true, Ordering::Relaxed);
}

/// Whether the item id belongs to an add-on that is off.
pub fn is_disabled(item: &str, mask: u32) -> bool {
    let Some((ns, _)) = item.split_once(':') else { return false };
    ADDONS.iter().enumerate().any(|(i, (id, _))| mask & (1 << i) != 0 && *id == ns)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_is_on_and_only_false_turns_off() {
        assert!(on(None));
        assert!(on(Some("true")));
        assert!(!on(Some("false")));
    }

    #[test]
    fn only_items_of_an_off_addon_are_disabled() {
        let rustic = ADDONS.iter().position(|a| a.0 == "rusticdelight").unwrap();
        let mask = 1 << rustic;
        assert!(is_disabled("rusticdelight:coffee", mask));
        assert!(!is_disabled("corn_delight:corn", mask));
        assert!(!is_disabled("farmersdelight:cabbage", mask));
        assert!(!is_disabled("minecraft:stick", mask));
        assert!(!is_disabled("rusticdelight:coffee", 0));
    }
}
