from __future__ import annotations

import pytest

from mysql_case_factory.sql_safety import SqlSafetyError, validate_sql_for_basic_runner


@pytest.mark.parametrize(
    "sql",
    [
        "SOURCE /tmp/secret.sql;",
        "SYSTEM cat /etc/passwd;",
        "SELECT 1 INTO OUTFILE '/tmp/result';",
        "SELECT LOAD_FILE('/etc/passwd');",
        "LOAD DATA LOCAL INFILE '/tmp/data' INTO TABLE t;",
        "INSTALL PLUGIN auth_socket SONAME 'auth_socket.so';",
        "INSTALL COMPONENT 'file://component_keyring_file';",
        "SHUTDOWN;",
        "RESTART;",
        "SET PERSIST max_connections = 10;",
        "CHANGE REPLICATION SOURCE TO SOURCE_HOST='example';",
    ],
)
def test_basic_runner_rejects_external_or_privileged_sql(sql: str) -> None:
    with pytest.raises(SqlSafetyError):
        validate_sql_for_basic_runner(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 'SOURCE /tmp/not-a-command';",
        "SELECT 'INTO OUTFILE'; -- LOAD_FILE('/tmp/x')\n",
        "/* INSTALL PLUGIN x */ SELECT 1;",
        "CREATE TABLE t(id BIGINT PRIMARY KEY); INSERT INTO t VALUES (1); SELECT * FROM t;",
    ],
)
def test_basic_runner_accepts_safe_sql_and_ignores_literals_comments(sql: str) -> None:
    validate_sql_for_basic_runner(sql)
