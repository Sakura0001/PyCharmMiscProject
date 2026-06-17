package dbradar.postgresql;

import java.util.Locale;

public final class PostgreSQLErrorClassifier {

    private PostgreSQLErrorClassifier() {
    }

    public static boolean isTransientSchemaRefreshError(Throwable throwable) {
        Throwable current = throwable;
        while (current != null) {
            String message = current.getMessage();
            if (message != null && isTransientSchemaRefreshMessage(message)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    private static boolean isTransientSchemaRefreshMessage(String message) {
        String normalized = message.toLowerCase(Locale.ROOT);
        return normalized.contains("could not open relation with oid")
                || normalized.contains("could not find tuple for parent of relation")
                || normalized.contains("cache lookup failed for relation")
                || normalized.contains("cache lookup failed for attribute")
                || transientCatalogObjectDoesNotExist(normalized);
    }

    private static boolean transientCatalogObjectDoesNotExist(String normalizedMessage) {
        if (!normalizedMessage.contains("does not exist")) {
            return false;
        }
        return normalizedMessage.contains("relation ")
                || normalizedMessage.contains("table ")
                || normalizedMessage.contains("index ")
                || normalizedMessage.contains("view ")
                || normalizedMessage.contains("materialized view ")
                || normalizedMessage.contains("sequence ");
    }
}
