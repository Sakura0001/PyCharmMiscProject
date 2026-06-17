package dbradar.common.query;

import java.sql.SQLException;
import java.util.Locale;

public final class SQLExecutionErrorClassifier {

    private SQLExecutionErrorClassifier() {
    }

    public static boolean isFatalInfrastructureError(Throwable throwable) {
        Throwable current = throwable;
        while (current != null) {
            if (isExpectedConcurrentStatementConflict(current)) {
                current = current.getCause();
                continue;
            }
            if (current instanceof SQLException) {
                SQLException sqlException = (SQLException) current;
                if (isFatalSqlState(sqlException.getSQLState())) {
                    return true;
                }
            }
            if (hasFatalConnectionMessage(current)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private static boolean isFatalSqlState(String sqlState) {
        if (sqlState == null || sqlState.length() < 2) {
            return false;
        }
        String sqlStateClass = sqlState.substring(0, 2);
        return "08".equals(sqlStateClass)
                || "53".equals(sqlStateClass)
                || "58".equals(sqlStateClass)
                || "XX".equals(sqlStateClass)
                || "57P01".equals(sqlState)
                || "57P02".equals(sqlState)
                || "57P03".equals(sqlState);
    }

    private static boolean hasFatalConnectionMessage(Throwable throwable) {
        String message = throwable.getMessage();
        if (message == null) {
            return false;
        }
        String normalized = message.toLowerCase(Locale.ROOT);
        return normalized.contains("server closed the connection unexpectedly")
                || normalized.contains("connection reset")
                || normalized.contains("terminating connection")
                || normalized.contains("an i/o error occurred while sending to the backend")
                || normalized.contains("the connection attempt failed")
                || normalized.contains("connection has been closed")
                || normalized.contains("broken pipe")
                || normalized.contains("backend closed the channel")
                || normalized.contains("could not receive data from server")
                || normalized.contains("connection refused");
    }

    private static boolean isExpectedConcurrentStatementConflict(Throwable throwable) {
        String message = throwable.getMessage();
        if (message == null) {
            return false;
        }
        String normalized = message.toLowerCase(Locale.ROOT);
        return normalized.contains("tuple concurrently updated")
                || normalized.contains("tuple concurrently deleted")
                || normalized.contains("could not find tuple for parent of relation")
                || normalized.contains("could not open relation with oid")
                || normalized.contains("cache lookup failed for relation")
                || normalized.contains("cache lookup failed for attribute");
    }
}
