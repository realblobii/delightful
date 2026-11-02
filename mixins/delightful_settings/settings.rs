// The settings page's buttons: one per add-on, labelled with its state.
fn delightful_settings(game: &crate::game::Game<'_>, mod_id: &str, buttons: &mut Vec<String>) {
    if mod_id != delightful::ID {
        return;
    }
    for i in 0..delightful::ADDONS.len() {
        let saved = game.native_setting(delightful::ID, &delightful::key(i));
        buttons.push(delightful::label(i, delightful::on(saved.as_deref())));
    }
}
