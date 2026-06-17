package dbradar;

import dbradar.common.query.Query;

import java.sql.Connection;
import java.sql.SQLException;

public abstract class SQLGlobalState extends GlobalState {

    @Override
    protected void executeEpilogue(Query q, boolean success, ExecutionTimer timer) throws Exception {
        boolean logExecutionTime = getOptions().logExecutionTime();
        if (success && getOptions().printSucceedingStatements()) {
            System.out.println(q.getQueryString());
        }
        if (logExecutionTime) {
            if (isConnectionLoggingEnabled()) {
                getLogger().writeCurrent("-- execution time: " + timer.end().asString());
            } else {
                getLogger().writeCurrent(" -- " + timer.end().asString());
            }
        }
        if (q.couldAffectSchema()) {
            updateSchema();
        }
    }

    @Override
    public SQLConnection getConnection() {
        return (SQLConnection) super.getConnection();
    }

    protected SQLConnection createLoggedConnection(Connection connection) {
        return new SQLConnection(connection, getLogger());
    }

    protected void logCurrentDatabaseStatement(String sql) {
        if (getLogger() != null) {
            getLogger().writeCurrentIfStateWritten(sql);
        }
    }

    public abstract SQLConnection createDatabase() throws SQLException;
}
