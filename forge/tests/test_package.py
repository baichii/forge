import forge


def test_package_exposes_version() -> None:
    assert isinstance(forge.__version__, str)
