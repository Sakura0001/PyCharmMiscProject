package dbradar;

import java.sql.SQLException;
import java.lang.reflect.Field;
import java.util.Collections;
import java.util.List;
import java.nio.file.Files;
import java.nio.file.Path;

import dbradar.common.query.SQLExecutionErrorClassifier;
import dbradar.postgresql.PostgreSQLErrorClassifier;
import dbradar.postgresql.PostgreSQLGlobalState;
import dbradar.postgresql.PostgreSQLProvider;
import dbradar.postgresql.PostgreSQLSchema;

public final class PostgreSQLErrorHandlingTest {

    private PostgreSQLErrorHandlingTest() {
    }

    public static void main(String[] args) throws Exception {
        classifiesFatalInfrastructureErrorsBySqlStateAndConnectionMessages();
        classifiesExpectedConcurrentStatementConflictsAsNonFatal();
        classifiesCatalogLookupRaceAsTransientSchemaRefreshError();
        disabledCurrentLoggingIsANoop();
        schemaRefreshKeepsPreviousSchemaAfterTransientCatalogRaceRetries();
        schemaRefreshThrowsFatalConnectionErrors();
    }

    private static void classifiesFatalInfrastructureErrorsBySqlStateAndConnectionMessages() {
        assertTrue(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("server closed the connection unexpectedly", "08006")));
        assertTrue(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: internal error", "XX000")));
        assertTrue(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: could not write to file", "58030")));

        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: relation \"missing_table\" does not exist", "42P01")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: duplicate key value violates unique constraint", "23505")));
    }

    private static void classifiesExpectedConcurrentStatementConflictsAsNonFatal() {
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: tuple concurrently updated", "XX000")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: tuple concurrently deleted", "XX000")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: could not open relation with OID 1288597", "XX000")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: cache lookup failed for attribute 1 of relation 23185276", "XX000")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: could not find tuple for parent of relation 6108297", "XX000")));
        assertFalse(SQLExecutionErrorClassifier.isFatalInfrastructureError(
                new SQLException("ERROR: current transaction is aborted, commands ignored until end of transaction block",
                        "25P02")));
    }

    private static void classifiesCatalogLookupRaceAsTransientSchemaRefreshError() {
        assertTrue(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: could not open relation with OID 1288597", "XX000")));
        assertTrue(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: cache lookup failed for relation 1288597", "XX000")));
        assertTrue(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: cache lookup failed for attribute 1 of relation 23185276", "XX000")));
        assertTrue(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: could not find tuple for parent of relation 6108297", "XX000")));
        assertTrue(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: relation \"thr1_t0\" does not exist", "42P01")));

        assertFalse(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("ERROR: column \"relpartbound\" does not exist", "42703")));
        assertFalse(PostgreSQLErrorClassifier.isTransientSchemaRefreshError(
                new SQLException("server closed the connection unexpectedly", "08006")));
    }

    private static void disabledCurrentLoggingIsANoop() throws Exception {
        String logName = "state_logger_disabled_current_logging";
        Path currentLog = Path.of("logs", "postgresql", logName + "-cur.log");
        Files.deleteIfExists(currentLog);

        MainOptions options = new MainOptions();
        Field logEachSelect = MainOptions.class.getDeclaredField("logEachSelect");
        logEachSelect.setAccessible(true);
        logEachSelect.setBoolean(options, false);

        StateLogger logger = new StateLogger(logName, new PostgreSQLProvider(), options);
        logger.writeCurrent("SELECT 1");
        logger.writeCurrentNoLineBreak("SELECT 1");
        logger.writeCurrent(new StateToReproduce("logger_disabled_db", new PostgreSQLProvider()));

        assertFalse(Files.exists(currentLog));
    }

    private static void schemaRefreshKeepsPreviousSchemaAfterTransientCatalogRaceRetries() throws Exception {
        PostgreSQLSchema previousSchema = new PostgreSQLSchema(Collections.emptyList());
        RefreshState state = new RefreshState(List.of(
                new SQLException("ERROR: could not open relation with OID 1288597", "XX000"),
                new SQLException("ERROR: could not open relation with OID 1288597", "XX000"),
                new SQLException("ERROR: could not open relation with OID 1288597", "XX000")));
        state.installSchema(previousSchema);

        state.updateSchema();

        assertSame(previousSchema, state.getSchema());
        assertEquals(3, state.getReadAttempts());
    }

    private static void schemaRefreshThrowsFatalConnectionErrors() {
        RefreshState state = new RefreshState(List.of(
                new SQLException("server closed the connection unexpectedly", "08006")));
        state.installSchema(new PostgreSQLSchema(Collections.emptyList()));

        try {
            state.updateSchema();
            throw new AssertionError("Expected fatal connection errors to be thrown from schema refresh");
        } catch (SQLException expected) {
            // expected
        } catch (Exception e) {
            throw new AssertionError("Expected SQLException, got " + e.getClass().getName(), e);
        }
        assertEquals(1, state.getReadAttempts());
    }

    private static void assertTrue(boolean condition) {
        if (!condition) {
            throw new AssertionError("Expected condition to be true");
        }
    }

    private static void assertFalse(boolean condition) {
        if (condition) {
            throw new AssertionError("Expected condition to be false");
        }
    }

    private static void assertSame(Object expected, Object actual) {
        if (expected != actual) {
            throw new AssertionError("Expected the same object reference");
        }
    }

    private static void assertEquals(int expected, int actual) {
        if (expected != actual) {
            throw new AssertionError("Expected " + expected + ", got " + actual);
        }
    }

    private static final class RefreshState extends PostgreSQLGlobalState {

        private final List<Exception> outcomes;
        private int readAttempts;

        private RefreshState(List<Exception> outcomes) {
            this.outcomes = outcomes;
        }

        private void installSchema(PostgreSQLSchema schema) {
            setSchema(schema);
        }

        private int getReadAttempts() {
            return readAttempts;
        }

        @Override
        protected PostgreSQLSchema readSchema() throws Exception {
            Exception outcome = outcomes.get(Math.min(readAttempts, outcomes.size() - 1));
            readAttempts++;
            throw outcome;
        }

        @Override
        protected long getSchemaRefreshRetryDelayMillis() {
            return 0;
        }
    }
}
