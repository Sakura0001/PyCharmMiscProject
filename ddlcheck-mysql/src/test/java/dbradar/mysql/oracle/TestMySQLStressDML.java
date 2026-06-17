package dbradar.mysql.oracle;

import dbradar.GlobalState;
import dbradar.Randomly;
import dbradar.mysql.MySQLGlobalState;
import dbradar.mysql.schema.MySQLSchema;
import dbradar.mysql.schema.MySQLSchema.MySQLColumn;
import dbradar.mysql.schema.MySQLSchema.MySQLForeignKey;
import dbradar.mysql.schema.MySQLSchema.MySQLTable;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class TestMySQLStressDML {

    @Test
    public void testStressSafeIntegerLiteralStaysNonNegativeForUnsignedCompatibility() {
        new Randomly(0);
        String value = MySQLStressValueHelper.generateStressSafeValue(
                new MySQLColumn("c1", null, false, "int", 0L, 10, 0, ""),
                new MySQLGlobalState());

        assertTrue(new BigInteger(value).signum() >= 0,
                "stress-safe integer literals should stay non-negative to remain valid for unsigned columns, but was: "
                        + value);
    }

    @Test
    public void testStressSafeDecimalLiteralFitsPrecisionAndScale() {
        new Randomly(0);
        String value = MySQLStressValueHelper.generateStressSafeValue(
                new MySQLColumn("c1", null, false, "decimal", 0L, 2, 1, ""),
                new MySQLGlobalState());
        BigDecimal decimal = new BigDecimal(value);

        assertTrue(decimal.signum() >= 0, "stress-safe decimal literals should stay non-negative, but was: " + value);
        assertTrue(fitsPrecisionAndScale(decimal, 2, 1),
                "stress-safe decimal literal should fit DECIMAL(2,1), but was: " + value);
    }

    @Test
    public void testStressSafeEnumAndSetLiteralsStayWithinGrammarDomain() {
        MySQLGlobalState state = new MySQLGlobalState();

        new Randomly(32);
        String enumValue = MySQLStressValueHelper.generateStressSafeValue(
                new MySQLColumn("c1", null, false, "enum", 0L, 0, 0, ""),
                state);
        assertTrue(Set.of("'a'", "'b'").contains(enumValue),
                "stress-safe enum literal should stay within ENUM('a','b'), but was: " + enumValue);

        new Randomly(32);
        String setValue = MySQLStressValueHelper.generateStressSafeValue(
                new MySQLColumn("c2", null, false, "set", 0L, 0, 0, ""),
                state);
        assertTrue(Set.of("'a'", "'b'", "'a,b'").contains(setValue),
                "stress-safe set literal should stay within SET('a','b'), but was: " + setValue);
    }

    @Test
    public void testStressDmlDoesNotDeleteFromForeignKeyParentTables() throws Exception {
        new Randomly(2);

        FakeMySQLState state = new FakeMySQLState();
        state.installSchema(createParentChildSchema());

        Object query = invokeGenerateStressDml(state);
        assertNotNull(query, "stress DML generation should still produce a statement");
        String sql = extractQueryString(query);

        assertFalse(sql.startsWith("DELETE FROM parent"),
                "stress DML should not delete from a foreign-key parent table, but was: " + sql);
    }

    @Test
    public void testStressDmlIncludesControlledExtendedForms() throws Exception {
        FakeMySQLState state = new FakeMySQLState();
        state.installSchema(createWritableSchemaWithRows());

        boolean sawMultiRowInsert = false;
        boolean sawInsertSelect = false;
        boolean sawOnDuplicateKeyUpdate = false;
        boolean sawPredicateUpdate = false;
        boolean sawPredicateDelete = false;

        for (int seed = 0; seed < 400; seed++) {
            new Randomly(seed);
            Object query = invokeGenerateStressDml(state);
            assertNotNull(query, "stress DML generation should produce a statement for writable non-empty tables");
            String sql = extractQueryString(query).toUpperCase();
            sawMultiRowInsert |= sql.startsWith("INSERT IGNORE INTO") && sql.contains("), (");
            sawInsertSelect |= sql.startsWith("INSERT IGNORE INTO") && sql.contains(" SELECT ");
            sawOnDuplicateKeyUpdate |= sql.startsWith("INSERT INTO") && sql.contains(" ON DUPLICATE KEY UPDATE ");
            sawPredicateUpdate |= sql.startsWith("UPDATE IGNORE") && sql.contains(" WHERE ") && sql.contains(" LIMIT 1");
            sawPredicateDelete |= sql.startsWith("DELETE FROM") && sql.contains(" WHERE ") && sql.contains(" LIMIT 1");
        }

        assertTrue(sawMultiRowInsert, "stress DML should sometimes generate controlled multi-row INSERT IGNORE");
        assertTrue(sawInsertSelect, "stress DML should sometimes generate controlled INSERT IGNORE ... SELECT");
        assertTrue(sawOnDuplicateKeyUpdate,
                "stress DML should sometimes generate controlled INSERT ... ON DUPLICATE KEY UPDATE");
        assertTrue(sawPredicateUpdate, "stress DML should sometimes generate UPDATE IGNORE with a predicate");
        assertTrue(sawPredicateDelete, "stress DML should sometimes generate DELETE with a predicate");
    }

    private MySQLSchema createParentChildSchema() {
        MySQLColumn parentId = new MySQLColumn("id", null, false, "int", 0L, 10, 0, "PRI");
        MySQLTable parent = new MySQLTable("parent", List.of(parentId), List.of(),
                MySQLTable.MySQLEngine.INNO_DB, false) {
            @Override
            public long getNrRows(GlobalState globalState) {
                return 2;
            }
        };
        parentId.setTable(parent);

        MySQLColumn childParentId = new MySQLColumn("parent_id", null, true, "int", 0L, 10, 0, "");
        MySQLTable child = new MySQLTable("child", List.of(childParentId), List.of(),
                MySQLTable.MySQLEngine.INNO_DB, false) {
            @Override
            public long getNrRows(GlobalState globalState) {
                return 2;
            }
        };
        childParentId.setTable(child);

        MySQLForeignKey foreignKey = new MySQLForeignKey(
                "fk_child_parent",
                child,
                List.of(childParentId),
                parent,
                List.of(parentId));
        return new MySQLSchema(List.of(parent, child), List.of(foreignKey));
    }

    private MySQLSchema createWritableSchemaWithRows() {
        MySQLColumn c1 = new MySQLColumn("c1", null, false, "int", 0L, 10, 0, "PRI");
        MySQLColumn c2 = new MySQLColumn("c2", null, true, "int", 0L, 10, 0, "");
        MySQLTable table = new MySQLTable("t0", List.of(c1, c2), List.of(),
                MySQLTable.MySQLEngine.INNO_DB, false) {
            @Override
            public long getNrRows(GlobalState globalState) {
                return 3;
            }
        };
        c1.setTable(table);
        c2.setTable(table);
        return new MySQLSchema(List.of(table), List.of());
    }

    private Object invokeGenerateStressDml(MySQLGlobalState state) throws Exception {
        Method generateStressDML = MySQLStressOracle.class
                .getDeclaredMethod("generateStressDML", MySQLGlobalState.class);
        generateStressDML.setAccessible(true);
        return generateStressDML.invoke(new MySQLStressOracle(state), state);
    }

    private boolean fitsPrecisionAndScale(BigDecimal value, int precision, int scale) {
        BigDecimal normalized = value.abs().stripTrailingZeros();
        int actualScale = Math.max(0, normalized.scale());
        int integerDigits = Math.max(0, normalized.precision() - actualScale);
        return actualScale <= scale && integerDigits <= Math.max(0, precision - scale);
    }

    private String extractQueryString(Object query) throws Exception {
        Method getQueryString = query.getClass().getMethod("getQueryString");
        return (String) getQueryString.invoke(query);
    }

    private static final class FakeMySQLState extends MySQLGlobalState {
        void installSchema(MySQLSchema schema) {
            setSchema(schema);
        }
    }
}
