"""Falsifier for the ufo-hackers-such-as-e2dece permalink collision cure.

Before the cure, two truncated permalinks were claimed by four and two
level-3 ``*_index.md`` documents respectively, shadowing indexes on
ufo-hackers.isaackoi.com. The cure keeps each shared route's live
winner and gives every shadowed index a unique suffixed permalink.
"""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
PERMALINK = re.compile(r"^permalink:\s*[\"']?([^\s\"'#]+)[\"']?\s*$", re.M)
LOGICAL_ID = re.compile(r"^logical_id:\s*[\"']?([^\s\"'#]+)[\"']?\s*$", re.M)


def page_permalinks():
    out = {}
    for p in PAGES.glob("*.md"):
        m = FRONT_MATTER.match(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        pm = PERMALINK.search(m.group(1))
        if pm:
            out[p.name] = pm.group(1)
    return out


SHARED_SLUGS = {
    "/ufo-hackers-such-as-e2dece-mckinnon/",
    "/ufo-hackers-such-as-e2dece-ufo-hacker/",
}

EXPECTED_CURED = {
    "/ufo-hackers-such-as-e2dece-mckinnon-access-methods/",
    "/ufo-hackers-such-as-e2dece-mckinnon-case-timeline/",
    "/ufo-hackers-such-as-e2dece-mckinnon-damage-claims/",
    "/ufo-hackers-such-as-e2dece-ufo-hacker-case-comparison/",
}


class TestPermalinkUniqueness(unittest.TestCase):
    def test_all_permalinks_unique(self):
        pls = page_permalinks()
        counts = Counter(pls.values())
        dups = {k: v for k, v in counts.items() if v > 1}
        owners = {k: sorted(n for n, v in pls.items() if v == k) for k in dups}
        self.assertEqual({}, owners)

    def test_shared_family_slugs_claimed_by_one_document(self):
        pls = page_permalinks()
        for slug in SHARED_SLUGS:
            owners = sorted(n for n, v in pls.items() if v == slug)
            self.assertEqual(1, len(owners), f"{slug} claimed by {owners}")

    def test_expected_cured_index_routes_exist(self):
        pls = set(page_permalinks().values())
        self.assertEqual(set(), EXPECTED_CURED - pls)

    def test_manifest_canonical_urls_match_cured_front_matter(self):
        lids = {}
        for p in PAGES.glob("*.md"):
            m = FRONT_MATTER.match(p.read_text(encoding="utf-8", errors="replace"))
            if not m:
                continue
            lm = LOGICAL_ID.search(m.group(1))
            pm = PERMALINK.search(m.group(1))
            if lm and pm:
                lids[lm.group(1)] = pm.group(1)
        manifest = json.loads((ROOT / "phoenix-manifest.json").read_text(encoding="utf-8"))
        entries = manifest if isinstance(manifest, list) else manifest.get("pages", manifest.get("entries", []))
        mismatches = []
        for e in entries:
            lid = e.get("logical_id")
            if lid in lids and lids[lid] in EXPECTED_CURED:
                url = str(e.get("canonical_url", ""))
                if not url.endswith(lids[lid]):
                    mismatches.append((lid, url, lids[lid]))
        self.assertEqual([], mismatches)

    def test_index_bodies_link_only_existing_routes(self):
        existing = set(page_permalinks().values())
        dangling = []
        for p in PAGES.glob("*_index.md"):
            for m in re.finditer(r"\{\{\s*'(/[^']*?)'\s*\|\s*relative_url", p.read_text(encoding="utf-8", errors="replace")):
                if m.group(1) not in existing:
                    dangling.append((p.name, m.group(1)))
        self.assertEqual([], dangling)


if __name__ == "__main__":
    unittest.main()
