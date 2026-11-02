// A click flips that add-on's setting and the cached mask the inventory check reads.
fn delightful_click(game: &crate::game::Game<'_>, mod_id: &str, button: usize) {
    if mod_id != delightful::ID || button >= delightful::ADDONS.len() {
        return;
    }
    let key = delightful::key(button);
    let now = delightful::on(game.native_setting(delightful::ID, &key).as_deref());
    game.native_set_setting(delightful::ID, &key, if now { "false" } else { "true" });
    let mask = delightful::mask() ^ (1 << button);
    delightful::set_mask(mask);
}
