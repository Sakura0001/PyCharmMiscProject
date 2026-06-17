package dbradar;

import dbradar.common.log.LoggableFactory;
import dbradar.common.log.SQLLoggableFactory;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class TestSQLConnectionLogging {

    @Test
    public void testStatementSqlIsLoggedThroughConnectionWrapper() throws Exception {
        TestProvider provider = new TestProvider("sql_logging_statement");
        StateLogger.resetInitializedProviders();
        StateLogger logger = new StateLogger("logging_db", provider, new MainOptions());
        SQLConnection connection = new SQLConnection(createConnectionProxy(), logger);

        try (Statement statement = connection.createStatement()) {
            statement.execute("CREATE TABLE t0 (c1 INT)");
        }

        StateToReproduce state = provider.getStateToReproduce("logging_db");
        state.databaseVersion = "test";
        state.seedValue = 1L;
        logger.writeCurrent(state);

        String log = Files.readString(logPath(provider.getDBMSName(), "logging_db"));
        assertTrue(log.contains("CREATE TABLE t0 (c1 INT);"), log);
    }

    @Test
    public void testPreparedStatementSqlIsLoggedThroughConnectionWrapper() throws Exception {
        TestProvider provider = new TestProvider("sql_logging_prepared");
        StateLogger.resetInitializedProviders();
        StateLogger logger = new StateLogger("logging_db", provider, new MainOptions());
        SQLConnection connection = new SQLConnection(createConnectionProxy(), logger);

        try (PreparedStatement statement = (PreparedStatement) connection.prepareStatement(
                "INSERT INTO t0 (c1) VALUES (?)")) {
            statement.setInt(1, 7);
            statement.execute();
        }

        StateToReproduce state = provider.getStateToReproduce("logging_db");
        state.databaseVersion = "test";
        state.seedValue = 2L;
        logger.writeCurrent(state);

        String log = Files.readString(logPath(provider.getDBMSName(), "logging_db"));
        assertTrue(log.contains("INSERT INTO t0 (c1) VALUES (?);"), log);
    }

    @Test
    public void testLifecycleSqlCanBeAppendedAfterCurrentLogHeaderExists() throws Exception {
        TestProvider provider = new TestProvider("sql_logging_lifecycle");
        StateLogger.resetInitializedProviders();
        StateLogger logger = new StateLogger("logging_db", provider, new MainOptions());

        logger.writeCurrentIfStateWritten("DROP DATABASE IF EXISTS logging_db");
        StateToReproduce state = provider.getStateToReproduce("logging_db");
        state.databaseVersion = "test";
        state.seedValue = 3L;
        logger.writeCurrent(state);
        logger.writeCurrentIfStateWritten("CREATE DATABASE logging_db");

        String log = Files.readString(logPath(provider.getDBMSName(), "logging_db"));
        assertTrue(!log.contains("DROP DATABASE IF EXISTS logging_db;"), log);
        assertTrue(log.contains("CREATE DATABASE logging_db;"), log);
    }

    @Test
    public void testConnectionWrapperDoesNotWriteWhenCurrentLoggingIsDisabled() throws Exception {
        TestProvider provider = new TestProvider("sql_logging_disabled");
        MainOptions options = new MainOptions();
        setBooleanOption(options, "logEachSelect", false);
        StateLogger logger = new StateLogger("logging_db", provider, options);
        SQLConnection connection = new SQLConnection(createConnectionProxy(), logger);

        try (Statement statement = connection.createStatement()) {
            statement.execute("CREATE TABLE t0 (c1 INT)");
        }

        assertTrue(!Files.exists(logPath(provider.getDBMSName(), "logging_db")));
    }

    private static Path logPath(String dbmsName, String databaseName) {
        return Main.LOG_DIRECTORY.toPath().resolve(dbmsName).resolve(databaseName + "-cur.log");
    }

    private static void setBooleanOption(MainOptions options, String fieldName, boolean value) throws Exception {
        Field field = MainOptions.class.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.setBoolean(options, value);
    }

    private static Connection createConnectionProxy() {
        Statement statement = (Statement) Proxy.newProxyInstance(
                Statement.class.getClassLoader(),
                new Class[]{Statement.class},
                (proxy, method, args) -> defaultValue(method.getReturnType()));
        PreparedStatement preparedStatement = (PreparedStatement) Proxy.newProxyInstance(
                PreparedStatement.class.getClassLoader(),
                new Class[]{PreparedStatement.class},
                (proxy, method, args) -> defaultValue(method.getReturnType()));
        return (Connection) Proxy.newProxyInstance(
                Connection.class.getClassLoader(),
                new Class[]{Connection.class},
                (proxy, method, args) -> {
                    if ("createStatement".equals(method.getName())) {
                        return statement;
                    }
                    if ("prepareStatement".equals(method.getName())) {
                        return preparedStatement;
                    }
                    return defaultValue(method.getReturnType());
                });
    }

    private static Object defaultValue(Class<?> returnType) {
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

    private static final class TestProvider implements DatabaseProvider {
        private final String dbmsName;

        private TestProvider(String dbmsName) {
            this.dbmsName = dbmsName;
        }

        @Override
        public Class<? extends GlobalState> getGlobalStateClass() {
            throw new UnsupportedOperationException();
        }

        @Override
        public Class<? extends DBMSSpecificOptions> getOptionClass() {
            throw new UnsupportedOperationException();
        }

        @Override
        public Reproducer generateAndTestDatabase(GlobalState globalState) {
            throw new UnsupportedOperationException();
        }

        @Override
        public DatabaseConnection createDatabase(GlobalState globalState) {
            throw new UnsupportedOperationException();
        }

        @Override
        public String getDBMSName() {
            return dbmsName;
        }

        @Override
        public LoggableFactory getLoggableFactory() {
            return new SQLLoggableFactory();
        }

        @Override
        public StateToReproduce getStateToReproduce(String databaseName) {
            return new StateToReproduce(databaseName, this);
        }
    }
}
