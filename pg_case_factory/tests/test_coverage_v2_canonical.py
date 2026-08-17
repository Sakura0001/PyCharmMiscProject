from __future__ import annotations

import unittest

from pg_case_factory.coverage_v2.canonical import canonical_json_bytes
from pg_case_factory.coverage_v2.errors import CoverageV2ContractError
from pg_case_factory.coverage_v2.ids import (
    ALLOWED_ID_KINDS,
    LogicalIdRegistry,
    logical_id,
)


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


class LogicalIdTest(unittest.TestCase):
    def test_kind_set_matches_the_frozen_spec(self) -> None:
        self.assertEqual(
            {
                "GRM", "FOB", "INV", "RISK", "NA", "INT", "AXI", "ITUP",
                "PROD", "PTUP", "STUP", "ATOM", "SUB", "PROGRAM",
                "BUNDLE", "SHARD", "WIT",
            },
            ALLOWED_ID_KINDS,
        )

    def test_fixed_vector_kind_separation_and_id_only_nfc(self) -> None:
        components = ["insert", "branch", "intent", "sfv-1", "ctx", "role"]
        factor = logical_id("FOB", components)
        grammar = logical_id("GRM", components)
        self.assertEqual(
            "FOB-17f39272f8c543a6fad7053797ece535da1051eec798bf0f98c1e52e07b060e0",
            factor,
        )
        self.assertNotEqual(factor.split("-", 1)[1], grammar.split("-", 1)[1])
        composed = ["insert", "caf\N{LATIN SMALL LETTER E WITH ACUTE}"]
        decomposed = ["insert", "cafe\N{COMBINING ACUTE ACCENT}"]
        self.assertEqual(logical_id("INV", composed), logical_id("INV", decomposed))

    def test_unknown_kind_empty_component_and_false_declaration_fail(self) -> None:
        registry = LogicalIdRegistry()
        components = ["insert", "branch", "intent", "sfv-1", "ctx", "role"]
        invalid_calls = (
            lambda: logical_id("fob", components),
            lambda: logical_id("UNKNOWN", components),
            lambda: logical_id("FOB", ["insert", ""]),
            lambda: registry.register_declared("GRM-" + "0" * 64, "FOB", components),
            lambda: registry.register_declared("FOB-" + "0" * 64, "FOB", components),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(CoverageV2ContractError):
                    call()


if __name__ == "__main__":
    unittest.main()
