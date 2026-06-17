package dbradar;

import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class SQLConnection implements DatabaseConnection {

    private final Connection connection;
    private StateLogger stateLogger;

    public SQLConnection(Connection connection) {
        this.connection = connection;
    }

    public SQLConnection(Connection connection, StateLogger stateLogger) {
        this.connection = connection;
        this.stateLogger = stateLogger;
    }

    @Override
    public String getDatabaseVersion() throws SQLException {
        DatabaseMetaData meta = connection.getMetaData();
        return meta.getDatabaseProductVersion();
    }

    @Override
    public void close() throws SQLException {
        connection.close();
    }

    public void setStateLogger(StateLogger stateLogger) {
        this.stateLogger = stateLogger;
    }

    public boolean isLoggingEnabled() {
        return stateLogger != null && stateLogger.logsCurrentStatements();
    }

    public PreparedStatement prepareStatement(String arg) throws SQLException {
        return wrapPreparedStatement(connection.prepareStatement(arg), arg);
    }

    public Statement createStatement() throws SQLException {
        return wrapStatement(connection.createStatement());
    }

    public boolean isClosed() throws SQLException {
        return connection.isClosed();
    }

    private Statement wrapStatement(Statement statement) {
        return (Statement) Proxy.newProxyInstance(Statement.class.getClassLoader(),
                new Class[]{Statement.class}, new LoggingStatementHandler(statement, null));
    }

    private PreparedStatement wrapPreparedStatement(PreparedStatement statement, String sql) {
        return (PreparedStatement) Proxy.newProxyInstance(PreparedStatement.class.getClassLoader(),
                new Class[]{PreparedStatement.class}, new LoggingStatementHandler(statement, sql));
    }

    private void logSQL(String sql) {
        if (isLoggingEnabled() && sql != null) {
            stateLogger.writeCurrent(sql);
        }
    }

    private final class LoggingStatementHandler implements InvocationHandler {
        private final Statement statement;
        private final String preparedSql;

        private LoggingStatementHandler(Statement statement, String preparedSql) {
            this.statement = statement;
            this.preparedSql = preparedSql;
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            String sql = getSQLToLog(method, args);
            if (sql != null) {
                logSQL(sql);
            }
            try {
                return method.invoke(statement, args);
            } catch (InvocationTargetException e) {
                throw e.getCause();
            }
        }

        private String getSQLToLog(Method method, Object[] args) {
            String methodName = method.getName();
            if (!isSQLExecutionMethod(methodName)) {
                return null;
            }
            if (args != null && args.length > 0 && args[0] instanceof String) {
                return (String) args[0];
            }
            if (preparedSql != null && isPreparedSQLExecutionMethod(methodName)) {
                return preparedSql;
            }
            return null;
        }

        private boolean isSQLExecutionMethod(String methodName) {
            return methodName.equals("execute")
                    || methodName.equals("executeQuery")
                    || methodName.equals("executeUpdate")
                    || methodName.equals("executeLargeUpdate")
                    || methodName.equals("addBatch");
        }

        private boolean isPreparedSQLExecutionMethod(String methodName) {
            return methodName.equals("execute")
                    || methodName.equals("executeQuery")
                    || methodName.equals("executeUpdate")
                    || methodName.equals("executeLargeUpdate")
                    || methodName.equals("addBatch");
        }
    }
}
