package dbradar.mysql.oracle;

import dbradar.Main;
import dbradar.MainOptions;
import dbradar.Randomly;
import dbradar.SQLConnection;
import dbradar.StateLogger;
import dbradar.mysql.MySQLGlobalState;
import dbradar.mysql.MySQLOptions;
import dbradar.mysql.MySQLProvider;
import dbradar.mysql.schema.MySQLSchema;
import dbradar.mysql.schema.MySQLSchema.MySQLColumn;
import dbradar.mysql.schema.MySQLSchema.MySQLTable;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.sql.SQLException;
import java.sql.Connection;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class TestMySQLStressTransactionScenario {

    @Test
    public void testTransactionScenarioExecutesClosedSavepointSequenceWithoutDDL() throws Exception {
        Main.nrSuccessfulActions.set(0);
        Main.nrUnsuccessfulActions.set(0);
        new Randomly(2);

        List<String> executedSql = new ArrayList<>();
        TrackingMySQLState state = new TrackingMySQLState();
        state.installSchema(createSchemaWithRows());
        state.setConnection(recordingConnection(executedSql));
        state.setDatabaseName("mysql_transaction_scenario_test");
        state.setMainOptions(new MainOptions());
        state.setDbmsSpecificOptions(new MySQLOptions());
        state.setStateLogger(new StateLogger("mysql_transaction_scenario_test", new MySQLProvider(), new MainOptions()));

        Method method = MySQLStressOracle.class.getDeclaredMethod("executeTransactionScenario", MySQLGlobalState.class);
        method.setAccessible(true);
        method.invoke(new MySQLStressOracle(state), state);

        assertTrue(executedSql.contains("START TRANSACTION"),
                "transaction scenario should start a transaction, but executed: " + executedSql);
        assertTrue(executedSql.stream().anyMatch(sql -> sql.startsWith("SAVEPOINT sp")),
                "transaction scenario should create a savepoint, but executed: " + executedSql);
        assertTrue(executedSql.stream().anyMatch(sql -> sql.startsWith("ROLLBACK TO SAVEPOINT sp")),
                "transaction scenario should roll back to the savepoint, but executed: " + executedSql);
        assertTrue(executedSql.stream().anyMatch(sql -> sql.startsWith("RELEASE SAVEPOINT sp")),
                "transaction scenario should release the savepoint, but executed: " + executedSql);
        assertTrue(executedSql.stream().anyMatch(sql -> sql.equals("COMMIT") || sql.equals("ROLLBACK")),
                "transaction scenario should close with COMMIT or ROLLBACK, but executed: " + executedSql);
        assertFalse(executedSql.stream().anyMatch(sql -> sql.matches("(?i).*(CREATE|ALTER|DROP|TRUNCATE)\\s+.*")),
                "transaction scenario should not execute DDL because MySQL DDL implicitly commits: " + executedSql);
    }

    @Test
    public void testTransactionScenarioRollsBackWholeTransactionWhenPostSavepointDmlFails() throws Exception {
        Main.nrSuccessfulActions.set(0);
        Main.nrUnsuccessfulActions.set(0);
        new Randomly(2);

        List<String> executedSql = new ArrayList<>();
        TrackingMySQLState state = new TrackingMySQLState();
        state.installSchema(createSchemaWithRows());
        state.setConnection(failingAfterSavepointConnection(executedSql));
        state.setDatabaseName("mysql_transaction_scenario_test");
        state.setMainOptions(new MainOptions());
        state.setDbmsSpecificOptions(new MySQLOptions());
        state.setStateLogger(new StateLogger("mysql_transaction_scenario_test", new MySQLProvider(), new MainOptions()));

        Method method = MySQLStressOracle.class.getDeclaredMethod("executeTransactionScenario", MySQLGlobalState.class);
        method.setAccessible(true);
        method.invoke(new MySQLStressOracle(state), state);

        assertTrue(executedSql.stream().anyMatch(sql -> sql.startsWith("SAVEPOINT sp")),
                "transaction scenario should reach savepoint setup, but executed: " + executedSql);
        assertTrue(executedSql.contains("ROLLBACK"),
                "transaction scenario should close the failed transaction with ROLLBACK, but executed: " + executedSql);
        assertFalse(executedSql.stream().anyMatch(sql -> sql.startsWith("ROLLBACK TO SAVEPOINT sp")),
                "transaction scenario should not use a savepoint after a post-savepoint DML failure: " + executedSql);
        assertFalse(executedSql.stream().anyMatch(sql -> sql.startsWith("RELEASE SAVEPOINT sp")),
                "transaction scenario should not release a savepoint after a post-savepoint DML failure: " + executedSql);
    }

    private SQLConnection recordingConnection(List<String> executedSql) {
        Statement statement = (Statement) Proxy.newProxyInstance(
                Statement.class.getClassLoader(),
                new Class[]{Statement.class},
                (proxy, method, args) -> {
                    String name = method.getName();
                    if ("execute".equals(name)) {
                        executedSql.add((String) args[0]);
                        return true;
                    }
                    if ("close".equals(name)) {
                        return null;
                    }
                    if ("isClosed".equals(name)) {
                        return false;
                    }
                    return defaultValue(method.getReturnType());
                });
        Connection connection = (Connection) Proxy.newProxyInstance(
                Connection.class.getClassLoader(),
                new Class[]{Connection.class},
                (proxy, method, args) -> {
                    String name = method.getName();
                    if ("createStatement".equals(name)) {
                        return statement;
                    }
                    if ("close".equals(name)) {
                        return null;
                    }
                    if ("isClosed".equals(name)) {
                        return false;
                    }
                    return defaultValue(method.getReturnType());
                });
        return new SQLConnection(connection);
    }

    private SQLConnection failingAfterSavepointConnection(List<String> executedSql) {
        boolean[] afterSavepoint = {false};
        Statement statement = (Statement) Proxy.newProxyInstance(
                Statement.class.getClassLoader(),
                new Class[]{Statement.class},
                (proxy, method, args) -> {
                    String name = method.getName();
                    if ("execute".equals(name)) {
                        String sql = (String) args[0];
                        executedSql.add(sql);
                        if (sql.startsWith("SAVEPOINT sp")) {
                            afterSavepoint[0] = true;
                            return true;
                        }
                        if (afterSavepoint[0] && isDml(sql)) {
                            throw new SQLException("simulated post-savepoint DML failure", "40001", 1213);
                        }
                        return true;
                    }
                    if ("close".equals(name)) {
                        return null;
                    }
                    if ("isClosed".equals(name)) {
                        return false;
                    }
                    return defaultValue(method.getReturnType());
                });
        Connection connection = (Connection) Proxy.newProxyInstance(
                Connection.class.getClassLoader(),
                new Class[]{Connection.class},
                (proxy, method, args) -> {
                    String name = method.getName();
                    if ("createStatement".equals(name)) {
                        return statement;
                    }
                    if ("close".equals(name)) {
                        return null;
                    }
                    if ("isClosed".equals(name)) {
                        return false;
                    }
                    return defaultValue(method.getReturnType());
                });
        return new SQLConnection(connection);
    }

    private boolean isDml(String sql) {
        String upper = sql.toUpperCase();
        return upper.startsWith("INSERT ") || upper.startsWith("REPLACE ") || upper.startsWith("UPDATE ")
                || upper.startsWith("DELETE ");
    }

    private Object defaultValue(Class<?> returnType) {
        if (returnType == boolean.class) {
            return false;
        }
        if (returnType == byte.class) {
            return (byte) 0;
        }
        if (returnType == short.class) {
            return (short) 0;
        }
        if (returnType == int.class) {
            return 0;
        }
        if (returnType == long.class) {
            return 0L;
        }
        if (returnType == float.class) {
            return 0f;
        }
        if (returnType == double.class) {
            return 0d;
        }
        if (returnType == char.class) {
            return '\0';
        }
        return null;
    }

    private MySQLSchema createSchemaWithRows() {
        MySQLColumn c1 = new MySQLColumn("c1", null, false, "int", 0L, 10, 0, "PRI");
        MySQLColumn c2 = new MySQLColumn("c2", null, true, "int", 0L, 10, 0, "");
        MySQLTable table = new MySQLTable("t0", List.of(c1, c2), List.of(), MySQLTable.MySQLEngine.INNO_DB, false) {
            @Override
            public long getNrRows(dbradar.GlobalState globalState) {
                return 3;
            }
        };
        c1.setTable(table);
        c2.setTable(table);
        return new MySQLSchema(List.of(table), List.of());
    }

    private static final class TrackingMySQLState extends MySQLGlobalState {
        private MySQLSchema schema;

        void installSchema(MySQLSchema schema) {
            this.schema = schema;
            setSchema(schema);
        }

        @Override
        public void updateSchema() {
            setSchema(schema);
        }
    }
}
