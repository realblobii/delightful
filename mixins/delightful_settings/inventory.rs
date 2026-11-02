// Items of an add-on that is off are taken out of the player's inventory as they are carried.
fn delightful_inventory(game: &mut crate::game::Game<'_>, slot: i32) {
    if !delightful::loaded() {
        let mut mask = 0u32;
        for i in 0..delightful::ADDONS.len() {
            if !delightful::on(game.native_setting(delightful::ID, &delightful::key(i)).as_deref()) {
                mask |= 1 << i;
            }
        }
        delightful::set_mask(mask);
    }
    let mask = delightful::mask();
    if mask == 0 {
        return;
    }
    if let Some(stack) = game.native_carried_stack(slot) {
        if delightful::is_disabled(&stack.item, mask) {
            stack.count = 0;
        }
    }
}
