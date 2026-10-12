from app import constants


def registered_paths(app):
    return {rule.rule for rule in app.url_map.iter_rules()}


def test_app_registers_blacklist_routes(app):
    paths = registered_paths(app)

    assert constants.BLACKLISTS_PATH in paths
    assert constants.BLACKLIST_EMAIL_PATH in paths
