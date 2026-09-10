import io

from tools.refresh_matt_editor_catalogs import extract_image_from_detail, log, lootlemon_catalog_key


def test_same_name_in_different_categories_has_distinct_key() -> None:
    assert lootlemon_catalog_key("Shields", "Collector") != lootlemon_catalog_key(
        "Enhancements", "Collector"
    )


def test_detail_image_extracts_absolute_og_image() -> None:
    html = '<meta content="/images/collector.webp" property="og:image">'
    assert extract_image_from_detail(html, "https://www.lootlemon.com/shield/collector-bl4") == (
        "https://www.lootlemon.com/images/collector.webp"
    )


def test_refresh_log_survives_windows_console_encoding(monkeypatch) -> None:
    buffer = io.BytesIO()
    output = io.TextIOWrapper(buffer, encoding="cp1252", newline="\n")
    monkeypatch.setattr("sys.stdout", output)

    log("Catalog complete \u2192 Loveless \ufffd")

    assert buffer.getvalue().decode("cp1252") == "Catalog complete \\u2192 Loveless \\ufffd\n"
