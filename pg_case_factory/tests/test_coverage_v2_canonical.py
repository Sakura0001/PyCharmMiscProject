from __future__ import annotations

import unittest

from pg_case_factory.coverage_v2.canonical import canonical_json_bytes
from pg_case_factory.coverage_v2.errors import CoverageV2ContractError


class CanonicalJsonTest(unittest.TestCase):
    def test_mapping_order_is_canonical_and_utf8_is_preserved(self) -> None:
        left = {"b": 2, "a": "caf\N{LATIN SMALL LETTER E WITH ACUTE}"}
        right = {"a": "caf\N{LATIN SMALL LETTER E WITH ACUTE}", "b": 2}
        expected = b'{"a":"caf\xc3\xa9","b":2}'
        self.assertEqual(expected, canonical_json_bytes(left))
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))

    def test_generic_jcs_does_not_apply_unicode_normalization(self) -> None:
        composed = {"value": "caf\N{LATIN SMALL LETTER E WITH ACUTE}"}
        decomposed = {"value": "cafe\N{COMBINING ACUTE ACCENT}"}
        self.assertNotEqual(
            canonical_json_bytes(composed),
            canonical_json_bytes(decomposed),
        )

    def test_float_non_string_key_and_non_json_value_are_rejected(self) -> None:
        invalid = (
            {"value": 1.5},
            {1: "not-a-string-key"},
            {"value": (1, 2)},
            {"value": b"bytes"},
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(CoverageV2ContractError):
                    canonical_json_bytes(value)


if __name__ == "__main__":
    unittest.main()
