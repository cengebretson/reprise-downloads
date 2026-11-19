import json
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from prepare_release import stage


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.packages = self.root / "packages"
        self.packages.mkdir()
        self.output = self.root / "staged"

    def tearDown(self):
        self.temporary.cleanup()

    def fixture(self, platform="linux-x86_64", kind="catalog-checksums"):
        manifest = json.dumps(dict(platform=platform, signing=dict(kind=kind))).encode()
        archive = self.packages / f"reprise-sketch-tools-0.1.0-{platform}.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("package.json", manifest)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        asset = dict(
            url=archive.as_uri(),
            sha256=digest,
            manifestSha256=hashlib.sha256(manifest).hexdigest(),
            bytes=archive.stat().st_size,
            installedBytes=100,
        )
        catalog = dict(schema=1, version="0.1.0", models=[], platforms={platform: asset})
        (self.packages / f"catalog-{platform}.json").write_text(json.dumps(catalog))
        report = dict(kind=kind, platform=platform, archiveSha256=digest)
        signing = self.packages / f"signing-{platform}.json"
        signing.write_text(json.dumps(report))
        smoke = dict(
            status="PASS",
            archiveSha256=digest,
            independentPlaybackAfterRemoval="PASS",
            plan=dict(platform=platform, downloadBytes=archive.stat().st_size),
        )
        (self.packages / "smoke.json").write_text(json.dumps(smoke))
        return signing, report

    def stage(self):
        stage(self.packages, "cengebretson/reprise-downloads", "music-sketch-tools-v0.1.0", self.output)

    def test_verified_assets_get_versioned_public_urls(self):
        self.fixture()
        self.stage()
        catalog = json.loads((self.output / "catalog.json").read_text())
        self.assertEqual(
            catalog["platforms"]["linux-x86_64"]["url"],
            "https://github.com/cengebretson/reprise-downloads/releases/download/music-sketch-tools-v0.1.0/reprise-sketch-tools-0.1.0-linux-x86_64.zip",
        )

    def test_unsigned_and_unnotarized_mac_cannot_be_staged(self):
        path, report = self.fixture("macos-arm64", "unsigned")
        with self.assertRaisesRegex(ValueError, "Unsigned"):
            self.stage()
        report["kind"] = "developer-id"
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "notarization"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_explicit_unsigned_preview_keeps_hash_and_smoke_validation(self):
        self.fixture("macos-arm64", "unsigned")
        stage(
            self.packages,
            "cengebretson/reprise-downloads",
            "music-sketch-tools-v0.1.0-preview.1",
            self.output,
            unsigned_preview=True,
        )
        catalog = json.loads((self.output / "catalog.json").read_text())
        self.assertEqual(catalog["releaseChannel"], "unsigned-preview")
        self.assertEqual(catalog["platforms"]["macos-arm64"]["signing"], "unsigned")
        self.assertIn("Unsigned developer preview", (self.output / "RELEASE.md").read_text())

    def test_unsigned_opt_in_cannot_use_a_stable_tag(self):
        self.fixture("macos-arm64", "unsigned")
        with self.assertRaisesRegex(ValueError, "preview.N"):
            stage(
                self.packages,
                "cengebretson/reprise-downloads",
                "music-sketch-tools-v0.1.0",
                self.output,
                unsigned_preview=True,
            )
        self.assertFalse(self.output.exists())

    def test_preview_does_not_waive_lifecycle_evidence(self):
        self.fixture("macos-arm64", "unsigned")
        (self.packages / "smoke.json").unlink()
        with self.assertRaisesRegex(ValueError, "evidence"):
            stage(
                self.packages,
                "cengebretson/reprise-downloads",
                "music-sketch-tools-v0.1.0-preview.1",
                self.output,
                unsigned_preview=True,
            )
        self.assertFalse(self.output.exists())

    def test_approved_source_asset_is_hashed_and_copied(self):
        self.fixture("macos-arm64", "unsigned")
        source = self.root / "helper-source.zip"
        source.write_bytes(b"original source fixture")
        stage(
            self.packages,
            "cengebretson/reprise-downloads",
            "music-sketch-tools-v0.1.0-preview.1",
            self.output,
            unsigned_preview=True,
            source_assets=[source],
        )
        catalog = json.loads((self.output / "catalog.json").read_text())
        self.assertEqual(
            catalog["sourceAssets"][source.name]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest()
        )
        self.assertEqual((self.output / source.name).read_bytes(), source.read_bytes())

    def test_source_asset_cannot_overwrite_platform_archive(self):
        self.fixture()
        archive = next(self.packages.glob("*.zip"))
        with self.assertRaisesRegex(ValueError, "conflicting source asset"):
            stage(
                self.packages,
                "cengebretson/reprise-downloads",
                "music-sketch-tools-v0.1.0",
                self.output,
                source_assets=[archive],
            )
        self.assertFalse(self.output.exists())

    def test_different_smoke_archive_is_rejected(self):
        self.fixture()
        path = self.packages / "smoke.json"
        report = json.loads(path.read_text())
        report["archiveSha256"] = "0" * 64
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "evidence"):
            self.stage()
        self.assertFalse(self.output.exists())

    def test_changed_archive_is_rejected_before_staging(self):
        self.fixture()
        archive = next(self.packages.glob("*.zip"))
        archive.write_bytes(archive.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "hash/size"):
            self.stage()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
