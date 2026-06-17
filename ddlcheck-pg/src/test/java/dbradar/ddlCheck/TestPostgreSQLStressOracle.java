package dbradar.ddlCheck;

import dbradar.Main;
import dbradar.MainOptions;
import dbradar.Randomly;
import dbradar.SQLConnection;
import dbradar.StateLogger;
import dbradar.StateToReproduce;
import dbradar.postgresql.PostgreSQLGlobalState;
import dbradar.postgresql.PostgreSQLOptions;
import dbradar.postgresql.PostgreSQLProvider;
import dbradar.postgresql.PostgreSQLSchema;
import dbradar.postgresql.oracle.PostgreSQLStressOracle;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class TestPostgreSQLStressOracle {

    private static final String DB_NAME = "postgresql";
    private static final String HOST = "127.0.0.1";
    private static final int PORT = 5432;
    private static final String USERNAME = "postgres";
    private static final String PASSWORD = "Taurus_123";
    private static final String DATABASE_PREFIX = "stress_startup_";
    private static final String THREADS_PER_DB_PREFIX = "stress_threads_per_db_";
    private static final Path STRESS_LOG = Path.of("logs", "postgresql", DATABASE_PREFIX + "1-cur.log");

    @Test
    public void testStressDqlWarmUpCreatesTableWhenSchemaIsEmpty() throws Exception {
        PostgreSQLProvider provider = new PostgreSQLProvider();
        MainOptions options = new MainOptions();
        PostgreSQLOptions postgreSQLOptions = new PostgreSQLOptions();
        postgreSQLOptions.oracle = List.of(PostgreSQLOptions.PostgreSQLOracleFactory.STRESS);

        NoTableFallbackState state = new NoTableFallbackState();
        state.setMainOptions(options);
        state.setDbmsSpecificOptions(postgreSQLOptions);
        state.setRandomly(new Randomly(20260428));
        state.setDatabaseName("stress_empty_schema_fallback");
        state.setThreadId(1);
        state.setGeneratedObjectNamePrefix("thr_test_");
        state.setState(new StateToReproduce(state.getDatabaseName(), provider));
        state.setStateLogger(new StateLogger("stress_empty_schema_fallback", provider, options));
        state.installRecordingConnection();

        PostgreSQLStressOracle oracle = new PostgreSQLStressOracle(state);
        Method executeDql = PostgreSQLStressOracle.class.getDeclaredMethod("executeDql", boolean.class);
        executeDql.setAccessible(true);

        boolean attempted = (boolean) executeDql.invoke(oracle, false);

        assertTrue(attempted, "Expected DQL warm-up to create a table and emit SELECT when schema is empty");
        assertTrue(state.executedSql.stream().map(TestPostgreSQLStressOracle::normalize)
                        .anyMatch(sql -> sql.startsWith("CREATE TABLE")),
                "Expected empty-schema DQL warm-up to use CREATE TABLE grammar");
        assertTrue(state.executedSql.stream().map(TestPostgreSQLStressOracle::normalize)
                        .anyMatch(sql -> sql.contains("SELECT ")),
                "Expected DQL warm-up to emit SELECT after creating the table");
    }

    @Test
    public void testPostgreSQLStressOracleStarts() throws Exception {
        Files.deleteIfExists(STRESS_LOG);

        int exitCode = Main.executeMain(
                "--num-threads", "40",
                "--num-tries", "10000",
                "--num-queries", "300",
                "--max-generated-databases", "100000",
                "--random-seed", "20260428",
                "--ddl-count", "100",
                "--dml-count", "100",
                "--timeout-seconds", "3000000",
                "--print-progress-information", "false",
                "--database-prefix", DATABASE_PREFIX,
                "--host", HOST,
                "--port", String.valueOf(PORT),
                "--username", USERNAME,
                "--password", PASSWORD,
                DB_NAME, "--oracle", "stress", "--stress-topology", "isolated");

        assertEquals(0, exitCode);
        assertTrue(Files.exists(STRESS_LOG), "Expected stress current log to be created");

        List<String> statements = Files.readAllLines(STRESS_LOG).stream()
                .map(String::trim)
                .filter(line -> !line.isEmpty())
                .filter(line -> !line.startsWith("--"))
                .toList();

        assertFalse(statements.isEmpty(), "Expected stress mode to emit SQL statements");
        assertFalse(statements.stream().anyMatch(line -> line.contains("SemiState")),
                "Stress mode should not use the EDC semi-state replay path");
        assertTrue(containsStatementStartingWith(statements, "CREATE", "ALTER", "DROP", "TRUNCATE", "REINDEX"),
                "Expected stress startup to emit DDL");
        assertTrue(containsStatementStartingWith(statements, "INSERT", "UPDATE", "DELETE", "MERGE"),
                "Expected stress startup to emit DML");
        assertTrue(containsStatementStartingWith(statements, "SELECT"),
                "Expected stress startup to emit DQL");
    }

    @Test
    public void testPostgreSQLStressOracleStartsWithCustomThreadsPerDatabase() throws Exception {
        List<Path> threadLogs = List.of(
                Path.of("logs", "postgresql", THREADS_PER_DB_PREFIX + "1-cur.log"),
                Path.of("logs", "postgresql", THREADS_PER_DB_PREFIX + "2-cur.log"),
                Path.of("logs", "postgresql", THREADS_PER_DB_PREFIX + "3-cur.log"),
                Path.of("logs", "postgresql", THREADS_PER_DB_PREFIX + "4-cur.log"));
        for (Path threadLog : threadLogs) {
            Files.deleteIfExists(threadLog);
        }

        int exitCode = Main.executeMain(
                "--num-threads", "4",
                "--num-tries", "1",
                "--num-queries", "3",
                "--max-generated-databases", "1",
                "--random-seed", "20260428",
                "--ddl-count", "4",
                "--dml-count", "3",
                "--timeout-seconds", "30",
                "--print-progress-information", "false",
                "--database-prefix", THREADS_PER_DB_PREFIX,
                "--host", HOST,
                "--port", String.valueOf(PORT),
                "--username", USERNAME,
                "--password", PASSWORD,
                DB_NAME, "--oracle", "stress", "--stress-threads-per-db", "2");

        assertEquals(0, exitCode);
        assertStressLog(threadLogs.get(0), THREADS_PER_DB_PREFIX + "0_g0");
        assertStressLog(threadLogs.get(1), THREADS_PER_DB_PREFIX + "0_g0");
        assertStressLog(threadLogs.get(2), THREADS_PER_DB_PREFIX + "0_g1");
        assertStressLog(threadLogs.get(3), THREADS_PER_DB_PREFIX + "0_g1");
    }

    private static void assertStressLog(Path logFile, String expectedDatabaseName) throws Exception {
        assertTrue(Files.exists(logFile), "Expected stress current log to be created: " + logFile);
        List<String> lines = Files.readAllLines(logFile);
        assertTrue(lines.stream().anyMatch(line -> line.equals("-- Database: " + expectedDatabaseName)),
                "Expected " + logFile + " to run against " + expectedDatabaseName);

        List<String> statements = lines.stream()
                .map(String::trim)
                .filter(line -> !line.isEmpty())
                .filter(line -> !line.startsWith("--"))
                .toList();
        assertFalse(statements.isEmpty(), "Expected stress mode to emit SQL statements");
        assertFalse(statements.stream().anyMatch(line -> line.contains("SemiState")),
                "Stress mode should not use the EDC semi-state replay path");
    }

    private static boolean containsStatementStartingWith(List<String> statements, String... prefixes) {
        for (String statement : statements) {
            String normalized = normalize(statement);
            for (String prefix : prefixes) {
                if (normalized.startsWith(prefix + " ")) {
                    return true;
                }
            }
        }
        return false;
    }

    private static String normalize(String statement) {
        return statement.toUpperCase(Locale.ROOT);
    }

    private static final class NoTableFallbackState extends PostgreSQLGlobalState {
        private final List<String> executedSql = new ArrayList<>();
        private SQLConnection recordingConnection;
        private boolean tableCreated;

        private void installRecordingConnection() {
            Connection connection = (Connection) Proxy.newProxyInstance(Connection.class.getClassLoader(),
                    new Class[]{Connection.class}, (proxy, method, args) -> {
                        if ("createStatement".equals(method.getName())) {
                            return createStatementProxy();
                        }
                        if ("close".equals(method.getName())) {
                            return null;
                        }
                        if ("isClosed".equals(method.getName())) {
                            return false;
                        }
                        return defaultValue(method.getReturnType());
                    });
            recordingConnection = new SQLConnection(connection);
        }

        @Override
        public SQLConnection getConnection() {
            return recordingConnection;
        }

        @Override
        protected PostgreSQLSchema readSchema() {
            if (!tableCreated) {
                return new PostgreSQLSchema(List.of());
            }
            PostgreSQLSchema.PostgreSQLColumn column = new PostgreSQLSchema.PostgreSQLColumn(
                    "c1", null, true, "integer", "int4", null, null, 0, 32, 0);
            PostgreSQLSchema.PostgreSQLTable table = new PostgreSQLSchema.PostgreSQLTable(
                    "fallback_t", List.of(column), Collections.emptyList(),
                    PostgreSQLSchema.PostgreSQLTable.TableType.STANDARD, Collections.emptyList(), false,
                    true, false, false, null, null, null);
            column.setTable(table);
            return new PostgreSQLSchema(List.of(table));
        }

        @Override
        public String getRandomTableAccessMethod() {
            return "heap";
        }

        private Statement createStatementProxy() {
            return (Statement) Proxy.newProxyInstance(Statement.class.getClassLoader(),
                    new Class[]{Statement.class}, (proxy, method, args) -> {
                        if ("execute".equals(method.getName())) {
                            recordSql((String) args[0]);
                            return true;
                        }
                        if ("executeQuery".equals(method.getName())) {
                            recordSql((String) args[0]);
                            return createResultSetProxy((Statement) proxy);
                        }
                        if ("close".equals(method.getName())) {
                            return null;
                        }
                        return defaultValue(method.getReturnType());
                    });
        }

        private ResultSet createResultSetProxy(Statement statement) {
            return (ResultSet) Proxy.newProxyInstance(ResultSet.class.getClassLoader(),
                    new Class[]{ResultSet.class}, (proxy, method, args) -> {
                        if ("getStatement".equals(method.getName())) {
                            return statement;
                        }
                        if ("next".equals(method.getName())) {
                            return false;
                        }
                        if ("close".equals(method.getName())) {
                            return null;
                        }
                        return defaultValue(method.getReturnType());
                    });
        }

        private void recordSql(String sql) {
            executedSql.add(sql);
            if (normalize(sql).startsWith("CREATE TABLE")) {
                tableCreated = true;
            }
        }

        private static Object defaultValue(Class<?> returnType) {
            if (!returnType.isPrimitive() || returnType == Void.TYPE) {
                return null;
            }
            if (returnType == Boolean.TYPE) {
                return false;
            }
            if (returnType == Character.TYPE) {
                return '\0';
            }
            return 0;
        }
    }
}
