from app.domain.email import normalize_email


def test_normalize_email_lowercases_and_strips_spaces():
    assert normalize_email("  Foo@Example.COM \n") == "foo@example.com"
