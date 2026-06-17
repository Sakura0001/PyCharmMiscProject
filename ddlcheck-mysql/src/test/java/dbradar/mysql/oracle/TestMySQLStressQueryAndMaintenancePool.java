package dbradar.mysql.oracle;

import dbradar.Randomly;
import dbradar.common.query.SQLQueryAdapter;
import dbradar.mysql.MySQLGlobalState;
import dbradar.mysql.MySQLOptions;
import dbradar.mysql.schema.MySQLSchema;
import dbradar.mysql.schema.MySQLSchema.MySQLColumn;
import dbradar.mysql.schema.MySQLSchema.MySQLTable;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class TestMySQLStressQueryAndMaintenancePool {

    @Test
    public void testStressQueryPoolGeneratesReadOnlyMetadataStatements() throws Exception {
        new Randomly(0);
        FakeMySQLState state = new FakeMySQLState();
        state.installSchema(createSchema());

        Set<String> observed = new HashSet<>();
        for (int i = 0; i < 200; i++) {
            String sql = invokeGeneratedSql("generateStressQuery", state);
            String normalized = sql.toUpperCase();
            if (normalized.startsWith("SELECT ")) {
                observed.add("SELECT");
            } else if (normalized.startsWith("EXPLAIN ")) {
                observed.add("EXPLAIN");
            } else if (normalized.startsWith("DESCRIBE ")) {
                observed.add("DESCRIBE");
            } else if (normalized.startsWith("SHOW TABLES")) {
                observed.add("SHOW_TABLES");
            } else if (normalized.startsWith("SHOW COLUMNS")) {
                observed.add("SHOW_COLUMNS");
            } else if (normalized.startsWith("SHOW INDEX")) {
                observed.add("SHOW_INDEX");
            } else if (normalized.startsWith("SHOW CREATE TABLE")) {
                observed.add("SHOW_CREATE_TABLE");
            }
        }

        assertTrue(observed.containsAll(Set.of("SELECT", "EXPLAIN", "DESCRIBE", "SHOW_TABLES",
                "SHOW_COLUMNS", "SHOW_INDEX", "SHOW_CREATE_TABLE")),
                "stress query pool should cover SELECT plus safe metadata statements, but observed: " + observed);
    }

    @Test
    public void testMaintenancePoolGeneratesTableMaintenanceStatements() throws Exception {
        new Randomly(1);
        FakeMySQLState state = new FakeMySQLState();
        state.installSchema(createSchema());

        Set<String> observed = new HashSet<>();
        for (int i = 0; i < 200; i++) {
            String sql = invokeGeneratedSql("generateMaintenanceQuery", state);
            String normalized = sql.toUpperCase();
            if (normalized.startsWith("CHECK TABLE ")) {
                observed.add("CHECK");
            } else if (normalized.startsWith("ANALYZE TABLE ")) {
                observed.add("ANALYZE");
            } else if (normalized.startsWith("CHECKSUM TABLE ")) {
                observed.add("CHECKSUM");
            } else if (normalized.startsWith("OPTIMIZE TABLE ")) {
                observed.add("OPTIMIZE");
            } else if (normalized.startsWith("REPAIR TABLE ")) {
                observed.add("REPAIR");
            }
        }

        assertTrue(observed.containsAll(Set.of("CHECK", "ANALYZE", "CHECKSUM", "OPTIMIZE", "REPAIR")),
                "maintenance pool should cover table maintenance statements, but observed: " + observed);
    }

    @Test
    public void testMaintenanceAndTransactionCountsDoNotDependOnQueryCount() throws Exception {
        MySQLOptions options = new MySQLOptions();
        setOption(options, "stressDDLPerThread", 10);
        setOption(options, "stressDMLPerThread", 20);
        setOption(options, "stressQueryPerThread", 0);

        MySQLStressOracle oracle = new MySQLStressOracle(new MySQLGlobalState());

        assertTrue((int) invokePrivate(oracle, "getMaintenanceCount", options) > 0,
                "maintenance pool should still run when DDL/DML are enabled even if query count is zero");
        assertTrue((int) invokePrivate(oracle, "getTransactionScenarioCount", options) > 0,
                "transaction scenario should still run when DML is enabled even if query count is zero");
    }

    @Test
    public void testNewStressPoolsDoNotGenerateExcludedStatementFamilies() throws Exception {
        new Randomly(2);
        FakeMySQLState state = new FakeMySQLState();
        state.installSchema(createSchema());

        for (int i = 0; i < 300; i++) {
            assertNotExcluded(invokeGeneratedSql("generateStressQuery", state));
            assertNotExcluded(invokeGeneratedSql("generateMaintenanceQuery", state));
        }
    }

    private String invokeGeneratedSql(String methodName, MySQLGlobalState state) throws Exception {
        Method method = MySQLStressOracle.class.getDeclaredMethod(methodName, MySQLGlobalState.class);
        method.setAccessible(true);
        SQLQueryAdapter query = (SQLQueryAdapter) method.invoke(new MySQLStressOracle(state), state);
        return query.getQueryString();
    }

    private Object invokePrivate(MySQLStressOracle oracle, String methodName, MySQLOptions options) throws Exception {
        Method method = MySQLStressOracle.class.getDeclaredMethod(methodName, MySQLOptions.class);
        method.setAccessible(true);
        return method.invoke(oracle, options);
    }

    private void setOption(MySQLOptions options, String fieldName, int value) throws Exception {
        Field field = MySQLOptions.class.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.setInt(options, value);
    }

    private void assertNotExcluded(String sql) {
        String normalized = sql.toUpperCase();
        assertFalse(normalized.matches(".*\\b(CREATE USER|ALTER USER|DROP USER|GRANT|REVOKE|CREATE ROLE|DROP ROLE)\\b.*"),
                "DCL/account statements should not be generated by new STRESS pools: " + sql);
        assertFalse(normalized.matches(".*\\b(CHANGE REPLICATION|START REPLICA|STOP REPLICA|RESET REPLICA)\\b.*"),
                "replication statements should not be generated by new STRESS pools: " + sql);
        assertFalse(normalized.matches(".*\\b(INSTALL PLUGIN|UNINSTALL PLUGIN|INSTALL COMPONENT|UNINSTALL COMPONENT)\\b.*"),
                "plugin/component statements should not be generated by new STRESS pools: " + sql);
        assertFalse(normalized.matches(".*\\b(SHUTDOWN|RESTART|FLUSH|RESET PERSIST|SET GLOBAL|SET PERSIST|LOCK INSTANCE)\\b.*"),
                "server lifecycle/global/persistent statements should not be generated by new STRESS pools: " + sql);
        assertFalse(normalized.matches(".*\\b(LOAD DATA|LOAD XML|INTO OUTFILE|INTO DUMPFILE)\\b.*"),
                "file-system dependent statements should not be generated by new STRESS pools: " + sql);
    }

    private MySQLSchema createSchema() {
        MySQLColumn c1 = new MySQLColumn("c1", null, false, "int", 0L, 10, 0, "PRI");
        MySQLColumn c2 = new MySQLColumn("c2", null, true, "varchar", 32L, 0, 0, "");
        MySQLTable table = new MySQLTable("t0", List.of(c1, c2), List.of(), MySQLTable.MySQLEngine.INNO_DB, false);
        c1.setTable(table);
        c2.setTable(table);
        return new MySQLSchema(List.of(table), List.of());
    }

    private static final class FakeMySQLState extends MySQLGlobalState {
        void installSchema(MySQLSchema schema) {
            setSchema(schema);
        }
    }
}
