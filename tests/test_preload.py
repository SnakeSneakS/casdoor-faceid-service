import unittest

from casdoor_faceid_service.config import Settings
from casdoor_faceid_service.preload import get_preload_components, parse_url_rewrites, rewrite_model_url


class PreloadTest(unittest.TestCase):
    def test_core_preload_downloads_login_compare_models(self):
        components = get_preload_components(Settings(), "core")

        self.assertEqual(components, ["detector", "recognizer"])

    def test_all_preload_downloads_every_service_model(self):
        components = get_preload_components(Settings(), "all")

        self.assertEqual(components, ["detector", "recognizer", "spoofer", "parser"])

    def test_liveness_adds_spoofer_to_core_preload(self):
        components = get_preload_components(Settings(enable_liveness=True), "core")

        self.assertEqual(components, ["detector", "recognizer", "spoofer"])

    def test_parse_url_rewrites_supports_comma_separated_prefix_rules(self):
        rules = parse_url_rewrites("https://github.com/=https://mirror/https://github.com/, https://old/=https://new/")

        self.assertEqual(
            rules,
            [
                ("https://github.com/", "https://mirror/https://github.com/"),
                ("https://old/", "https://new/"),
            ],
        )

    def test_rewrite_model_url_replaces_matching_prefix(self):
        rules = [("https://github.com/", "https://mirror/https://github.com/")]

        rewritten = rewrite_model_url("https://github.com/yakhyo/uniface/releases/download/weights/a.onnx", rules)

        self.assertEqual(rewritten, "https://mirror/https://github.com/yakhyo/uniface/releases/download/weights/a.onnx")


if __name__ == "__main__":
    unittest.main()
