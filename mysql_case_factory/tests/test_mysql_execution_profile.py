from __future__ import annotations

import pytest

from mysql_case_factory.contracts import ContractValidationError, ExecutionProfile


def profile(version: str) -> dict:
    number = version.replace(".", "")
    return {
        "schema_version": 1,
        "kind": "execution_profile",
        "compatibility_target": f"mysql-community-{version}",
        "reference": {
            "login_path": f"mysql{number}_reference",
            "database": "regression",
            "expected_server_uuid": "11111111-1111-1111-1111-111111111111",
            "expected_current_user": "regression_user@%",
        },
        "dut": {
            "login_path": f"mysql{number}_dut",
            "database": "regression",
            "expected_server_uuid": "22222222-2222-2222-2222-222222222222",
            "expected_current_user": "regression_user@%",
        },
        "runner": {"executable": "mysql", "timeout_seconds": 30, "stop_on_error": True},
        "comparison": {
            "mode": "exact_text",
            "normalization": {
                "drop_line_patterns": [],
                "replacements": [],
                "strip_trailing_whitespace": False,
            },
        },
        "security": {
            "credential_source": "external-mysql-login-path",
            "persist_credentials": False,
        },
    }


@pytest.mark.parametrize(("version", "number"), [("8.0.22", 80022), ("8.0.41", 80041)])
def test_profile_supports_each_exact_edition(version: str, number: int) -> None:
    loaded = ExecutionProfile.from_dict(profile(version))
    assert loaded.target_version_num == number
    assert loaded.reference.login_path.endswith("_reference")


def test_profile_rejects_rolling_target() -> None:
    document = profile("8.0.22")
    document["compatibility_target"] = "mysql-community-8.0"
    with pytest.raises(ContractValidationError, match="8.0.22 or mysql-community-8.0.41"):
        ExecutionProfile.from_dict(document)


def test_profile_rejects_password_or_connection_material() -> None:
    document = profile("8.0.22")
    document["reference"]["login_path"] = "--password=secret"
    with pytest.raises(ContractValidationError, match="login_path"):
        ExecutionProfile.from_dict(document)


def test_profile_rejects_non_uuid_identity_anchor() -> None:
    document = profile("8.0.41")
    document["dut"]["expected_server_uuid"] = "12345"
    with pytest.raises(ContractValidationError, match="canonical UUID"):
        ExecutionProfile.from_dict(document)
