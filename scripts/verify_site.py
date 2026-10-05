#!/usr/bin/env python3
"""Validate the dependency-free Envuscator public site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
INDEX = WEB / "index.html"
PRIMARY_CSS = WEB / "styles.css"
SECURITY_POLICY = ROOT / "SECURITY.md"
COMPATIBILITY = ROOT / "docs" / "compatibility.md"
LOCAL_RUNNER = ROOT / "docs" / "local-runner.md"
SECURITY_TXT = WEB / ".well-known" / "security.txt"
SECURITY_POLICY_URL = "https://github.com/hackelia-micrantha/envuscator-community/security/policy"
COMPATIBILITY_URL = "https://github.com/hackelia-micrantha/envuscator-community/blob/main/docs/compatibility.md"
LOCAL_RUNNER_URL = "https://github.com/hackelia-micrantha/envuscator-community/blob/main/docs/local-runner.md"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.stylesheets: list[str] = []
        self.meta_names: set[str] = set()
        self.meta_properties: set[str] = set()
        self.title_parts: list[str] = []
        self.heading_counts = {"h1": 0, "h2": 0, "h3": 0}
        self.ordered_lists = 0
        self.phyllotaxis_profiles: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs if value is not None}
        if element_id := values.get("id"):
            if element_id in self.ids:
                raise AssertionError(f"duplicate id: {element_id}")
            self.ids.add(element_id)
        if tag == "a" and (href := values.get("href")):
            self.hrefs.append(href)
        if tag == "link" and values.get("rel") == "stylesheet":
            if href := values.get("href"):
                self.stylesheets.append(href)
        if tag == "meta":
            if name := values.get("name"):
                self.meta_names.add(name)
            if prop := values.get("property"):
                self.meta_properties.add(prop)
        if tag in self.heading_counts:
            self.heading_counts[tag] += 1
        if profile := values.get("data-phyllotaxis-profile"):
            self.phyllotaxis_profiles.append(profile)
        if tag == "ol":
            self.ordered_lists += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)


def resolve_local_path(href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith("mailto:") or href.startswith("#"):
        return None
    relative = parsed.path.removeprefix("./")
    return WEB / relative


def main() -> None:
    assert INDEX.is_file(), "web/index.html is missing"
    assert PRIMARY_CSS.is_file(), "web/styles.css is missing"
    assert SECURITY_POLICY.is_file(), "SECURITY.md is missing"
    assert COMPATIBILITY.is_file(), "docs/compatibility.md is missing"
    assert LOCAL_RUNNER.is_file(), "docs/local-runner.md is missing"
    assert SECURITY_TXT.is_file(), "web/.well-known/security.txt is missing"

    parser = SiteParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    parser.close()

    title = "".join(parser.title_parts).strip()
    assert title, "document title is missing"
    assert "description" in parser.meta_names, "meta description is missing"
    assert "viewport" in parser.meta_names, "viewport metadata is missing"
    assert "og:title" in parser.meta_properties, "Open Graph title is missing"
    assert parser.heading_counts["h1"] == 1, "site must contain exactly one h1"
    assert parser.heading_counts["h2"] >= 3, "site needs meaningful section headings"
    assert parser.ordered_lists >= 1, "architecture flow must be an ordered list"
    assert parser.phyllotaxis_profiles == ["utility"], (
        "site must declare exactly one coherent Phyllotaxis Utility profile surface"
    )
    assert SECURITY_POLICY_URL in parser.hrefs, "public site must link security reporting guidance"
    assert COMPATIBILITY_URL in parser.hrefs, "public site must link compatibility guidance"
    assert LOCAL_RUNNER_URL in parser.hrefs, "public site must link local-runner guidance"

    for href in parser.hrefs:
        if href.startswith("#"):
            fragment = href[1:]
            assert fragment in parser.ids, f"unresolved fragment link: {href}"
            continue
        local = resolve_local_path(href)
        if local is not None:
            assert local.exists(), f"unresolved local link: {href}"

    assert parser.stylesheets, "no stylesheet linked"
    stylesheet_paths: list[Path] = []
    for href in parser.stylesheets:
        local = resolve_local_path(href)
        assert local is not None and local.is_file(), f"missing stylesheet: {href}"
        stylesheet_paths.append(local)

    for stylesheet in stylesheet_paths:
        css = stylesheet.read_text(encoding="utf-8")
        assert css.count("{") == css.count("}"), (
            f"CSS braces are unbalanced: {stylesheet.relative_to(ROOT)}"
        )

    security_txt = SECURITY_TXT.read_text(encoding="utf-8")
    assert "Contact: mailto:security.envuscator@micrantha.com" in security_txt
    assert "Expires:" in security_txt
    assert f"Policy: {SECURITY_POLICY_URL}" in security_txt

    primary_css = PRIMARY_CSS.read_text(encoding="utf-8")
    for token in (
        "--phyllotaxis-space-sm: 0.5rem",
        "--phyllotaxis-content-width-readable: 70rem",
        '--phyllotaxis-font-body: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "--phyllotaxis-type-body-line-height: 1.45",
        "--phyllotaxis-type-title-size: 1.75rem",
        "--phyllotaxis-color-canvas: #ffffff",
        "--phyllotaxis-color-text: #111111",
        "--phyllotaxis-color-text-muted: #555555",
        "--phyllotaxis-color-border: #a0a0a0",
        "--phyllotaxis-color-link: #0000ee",
        "--phyllotaxis-color-link-visited: #551a8b",
        "--phyllotaxis-color-focus: #111111",
    ):
        assert token in primary_css, f"Phyllotaxis Utility token missing: {token}"

    for token in (
        "--brand-ink: #1f2a2a",
        "--brand-leaf: #2f6b55",
        "--brand-mist: #d3e4de",
        "--brand-sky: #dbeaf7",
        "--brand-sand: #f4efe3",
        "--brand-paper: #fcfbf7",
    ):
        assert token in primary_css, f"Micrantha brand token missing: {token}"

    html = INDEX.read_text(encoding="utf-8")
    for required_copy in ("Available now", "Target v1 architecture", "In progress", "Planned"):
        assert required_copy in html, f"project-state label missing: {required_copy}"

    print("Envuscator static site validation passed")


if __name__ == "__main__":
    main()
