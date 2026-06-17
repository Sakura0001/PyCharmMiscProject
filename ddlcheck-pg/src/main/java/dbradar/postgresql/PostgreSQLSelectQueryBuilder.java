package dbradar.postgresql;

import dbradar.IgnoreMeException;
import dbradar.Randomly;
import dbradar.postgresql.PostgreSQLSchema.PostgreSQLColumn;
import dbradar.postgresql.PostgreSQLSchema.PostgreSQLDataType;
import dbradar.postgresql.PostgreSQLSchema.PostgreSQLTable;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public final class PostgreSQLSelectQueryBuilder {

    private static final int MAX_LIMIT = 100;
    private final PostgreSQLGlobalState state;

    private PostgreSQLSelectQueryBuilder(PostgreSQLGlobalState state) {
        this.state = state;
    }

    public static String generate(PostgreSQLGlobalState state) {
        return new PostgreSQLSelectQueryBuilder(state).generateSelect();
    }

    private String generateSelect() {
        List<PostgreSQLTable> tables = candidateTables();
        if (tables.isEmpty()) {
            throw new IgnoreMeException("There are no tables available for SELECT generation.");
        }

        for (SelectKind kind : Randomly.nonEmptySubset(SelectKind.SIMPLE, SelectKind.JOIN,
                SelectKind.AGGREGATE, SelectKind.COMPOUND, SelectKind.CTE, SelectKind.WINDOW,
                SelectKind.JSON, SelectKind.RANGE, SelectKind.ARRAY, SelectKind.REGEX,
                SelectKind.CROSS_JOIN, SelectKind.LOCKING, SelectKind.FUNCTIONS)) {
            String query = tryGenerate(kind, tables);
            if (query != null) {
                return query;
            }
        }
        return generateSimpleSelect(Randomly.fromList(tables));
    }

    private String tryGenerate(SelectKind kind, List<PostgreSQLTable> tables) {
        switch (kind) {
            case SIMPLE:
                return generateSimpleSelect(Randomly.fromList(tables));
            case JOIN:
                return generateJoinSelect(tables);
            case AGGREGATE:
                return generateAggregateSelect(tables);
            case COMPOUND:
                return generateCompoundSelect(tables);
            case CTE:
                return generateCteSelect(tables);
            case WINDOW:
                return generateWindowSelect(tables);
            case JSON:
                return generateJsonSelect(tables);
            case RANGE:
                return generateRangeSelect(tables);
            case ARRAY:
                return generateArraySelect(tables);
            case REGEX:
                return generateRegexSelect(tables);
            case CROSS_JOIN:
                return generateCrossJoinSelect(tables);
            case LOCKING:
                return generateLockingSelect(tables);
            case FUNCTIONS:
                return generateFunctionSelect(tables);
            default:
                throw new AssertionError("Unhandled SELECT kind: " + kind);
        }
    }

    private String generateSimpleSelect(PostgreSQLTable table) {
        List<PostgreSQLColumn> columns = selectableColumns(table);
        if (columns.isEmpty()) {
            return "SELECT COUNT(*) AS ca1 FROM " + quoteIdentifier(table.getName()) + " AS t0"
                    + deterministicLimit(1);
        }
        List<PostgreSQLColumn> selectedColumns = Randomly.nonEmptySubset(columns,
                Randomly.getNotCachedInteger(1, Math.min(columns.size(), 3) + 1));
        String projection = projectionList(selectedColumns, "t0", 1);
        StringBuilder query = new StringBuilder("SELECT ");
        query.append(projection)
                .append(" FROM ")
                .append(quoteIdentifier(table.getName()))
                .append(" AS t0");
        appendWhereClause(query, table, "t0");
        query.append(deterministicLimit(selectedColumns.size()));
        return query.toString();
    }

    private String generateJoinSelect(List<PostgreSQLTable> tables) {
        if (tables.size() < 2) {
            return null;
        }
        PostgreSQLTable left = Randomly.fromList(tables);
        PostgreSQLTable right = Randomly.fromList(tables);
        List<ColumnPair> joinPairs = compatibleJoinPairs(left, right);
        if (joinPairs.isEmpty()) {
            return null;
        }
        ColumnPair joinPair = Randomly.fromList(joinPairs);
        List<ProjectedColumn> projectedColumns = new ArrayList<>();
        for (PostgreSQLColumn column : selectableColumns(left)) {
            projectedColumns.add(new ProjectedColumn("t0", column));
        }
        for (PostgreSQLColumn column : selectableColumns(right)) {
            projectedColumns.add(new ProjectedColumn("t1", column));
        }
        if (projectedColumns.isEmpty()) {
            return null;
        }
        List<ProjectedColumn> selectedColumns = Randomly.nonEmptySubset(projectedColumns,
                Randomly.getNotCachedInteger(1, Math.min(projectedColumns.size(), 3) + 1));
        String projection = projectedColumns(selectedColumns);
        return "SELECT " + projection
                + " FROM " + quoteIdentifier(left.getName()) + " AS t0"
                + " INNER JOIN " + quoteIdentifier(right.getName()) + " AS t1"
                + " ON " + qualifiedColumn("t0", joinPair.left)
                + " = " + qualifiedColumn("t1", joinPair.right)
                + deterministicLimit(selectedColumns.size());
    }

    private String generateAggregateSelect(List<PostgreSQLTable> tables) {
        PostgreSQLTable table = Randomly.fromList(tables);
        List<PostgreSQLColumn> groupableColumns = table.getColumns().stream()
                .filter(this::isGroupable)
                .collect(Collectors.toList());
        if (groupableColumns.isEmpty()) {
            return null;
        }
        PostgreSQLColumn groupColumn = Randomly.fromList(groupableColumns);
        String groupExpression = qualifiedColumn("t0", groupColumn);
        return "SELECT " + castAsText(groupExpression) + " AS ca1, COUNT(*) AS ca2"
                + " FROM " + quoteIdentifier(table.getName()) + " AS t0"
                + " GROUP BY " + groupExpression
                + deterministicLimit(2);
    }

    private String generateCompoundSelect(List<PostgreSQLTable> tables) {
        if (tables.size() < 2) {
            return null;
        }
        PostgreSQLTable left = Randomly.fromList(tables);
        PostgreSQLTable right = Randomly.fromList(tables);
        List<PostgreSQLColumn> leftColumns = selectableColumns(left);
        List<PostgreSQLColumn> rightColumns = selectableColumns(right);
        if (leftColumns.isEmpty() || rightColumns.isEmpty()) {
            return null;
        }
        PostgreSQLColumn leftColumn = Randomly.fromList(leftColumns);
        PostgreSQLColumn rightColumn = Randomly.fromList(rightColumns);
        String operator = Randomly.fromOptions("UNION ALL", "UNION", "INTERSECT", "EXCEPT");
        return "SELECT CAST(" + qualifiedColumn("t0", leftColumn) + " AS TEXT) AS ca1"
                + " FROM " + quoteIdentifier(left.getName()) + " AS t0"
                + " " + operator + " "
                + "SELECT CAST(" + qualifiedColumn("t1", rightColumn) + " AS TEXT) AS ca1"
                + " FROM " + quoteIdentifier(right.getName()) + " AS t1"
                + deterministicLimit(1);
    }

    private String generateCteSelect(List<PostgreSQLTable> tables) {
        if (Randomly.getBoolean()) {
            return "WITH RECURSIVE q(n) AS ("
                    + "SELECT 1 "
                    + "UNION ALL SELECT n + 1 FROM q WHERE n < 3"
                    + ") SELECT n AS ca1 FROM q ORDER BY ca1 LIMIT " + randomLimit();
        }
        PostgreSQLTable table = Randomly.fromList(tables);
        List<PostgreSQLColumn> columns = selectableColumns(table);
        if (columns.isEmpty()) {
            return null;
        }
        List<PostgreSQLColumn> selectedColumns = Randomly.nonEmptySubset(columns,
                Randomly.getNotCachedInteger(1, Math.min(columns.size(), 3) + 1));
        String innerProjection = projectionList(selectedColumns, "t0", 1);
        String outerProjection = outerCteProjection(selectedColumns.size());
        StringBuilder cte = new StringBuilder("WITH q AS (SELECT ");
        cte.append(innerProjection)
                .append(" FROM ")
                .append(quoteIdentifier(table.getName()))
                .append(" AS t0");
        appendWhereClause(cte, table, "t0");
        cte.append(deterministicLimit(selectedColumns.size())).append(") ");
        cte.append("SELECT ").append(outerProjection).append(" FROM q")
                .append(deterministicLimit(selectedColumns.size()));
        return cte.toString();
    }

    private String generateWindowSelect(List<PostgreSQLTable> tables) {
        List<PostgreSQLTable> candidateTables = tables.stream()
                .filter(table -> !orderableColumns(table).isEmpty() && !selectableColumns(table).isEmpty())
                .collect(Collectors.toList());
        if (candidateTables.isEmpty()) {
            return null;
        }
        PostgreSQLTable table = Randomly.fromList(candidateTables);
        PostgreSQLColumn orderColumn = Randomly.fromList(orderableColumns(table));
        PostgreSQLColumn valueColumn = Randomly.fromList(selectableColumns(table));
        List<PostgreSQLColumn> partitionColumns = table.getColumns().stream()
                .filter(this::isGroupable)
                .collect(Collectors.toList());
        String partitionClause = partitionColumns.isEmpty() || Randomly.getBoolean()
                ? ""
                : "PARTITION BY " + qualifiedColumn("t0", Randomly.fromList(partitionColumns)) + " ";
        String frameClause = Randomly.fromOptions("",
                " ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW",
                " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING");
        String orderExpression = qualifiedColumn("t0", orderColumn);
        String valueExpression = castAsText(qualifiedColumn("t0", valueColumn));
        String windowSpec = "OVER (" + partitionClause + "ORDER BY " + orderExpression + frameClause + ")";
        String windowFunction = Randomly.fromOptions(
                "row_number()",
                "rank()",
                "dense_rank()",
                "percent_rank()",
                "cume_dist()",
                "ntile(4)",
                "lag(" + valueExpression + ", 1)",
                "lead(" + valueExpression + ", 1)",
                "first_value(" + valueExpression + ")",
                "last_value(" + valueExpression + ")",
                "nth_value(" + valueExpression + ", 1)");
        return "SELECT CAST(" + windowFunction + " " + windowSpec + " AS TEXT) AS ca1, "
                + castAsText(qualifiedColumn("t0", valueColumn)) + " AS ca2"
                + " FROM " + quoteIdentifier(table.getName()) + " AS t0"
                + " ORDER BY ca1, ca2 LIMIT " + randomLimit();
    }

    private String generateJsonSelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isJsonColumn);
        if (location == null) {
            return null;
        }
        String column = qualifiedColumn("t0", location.column);
        String jsonbExpression = "(" + column + "::jsonb)";
        return "SELECT jsonb_typeof(" + jsonbExpression + ") AS ca1, "
                + "CAST((" + jsonbExpression + " -> 'value') AS TEXT) AS ca2, "
                + "CAST((" + jsonbExpression + " ->> 'value') AS TEXT) AS ca3, "
                + "CAST((" + jsonbExpression + " #> '{value}') AS TEXT) AS ca4, "
                + "CAST((" + jsonbExpression + " #>> '{value}') AS TEXT) AS ca5, "
                + "CAST((" + jsonbExpression + " @> '{}'::jsonb) AS TEXT) AS ca6, "
                + "CAST((" + jsonbExpression + " <@ " + jsonbExpression + ") AS TEXT) AS ca7, "
                + "CAST((" + jsonbExpression + " ? 'value') AS TEXT) AS ca8, "
                + "CAST((" + jsonbExpression + " ?| ARRAY['value','missing']) AS TEXT) AS ca9, "
                + "CAST((" + jsonbExpression + " ?& ARRAY['value']) AS TEXT) AS ca10, "
                + "CAST(jsonb_strip_nulls(" + jsonbExpression + ") AS TEXT) AS ca11"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + column + " IS NOT NULL"
                + " ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8, ca9, ca10, ca11 LIMIT " + randomLimit();
    }

    private String generateRangeSelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isRangeColumn);
        if (location == null) {
            return null;
        }
        String column = qualifiedColumn("t0", location.column);
        String rangeLiteral = "'[0,100)'::" + location.column.getDataType();
        return "SELECT lower(" + column + ") AS ca1, upper(" + column + ") AS ca2, "
                + "CAST(isempty(" + column + ") AS TEXT) AS ca3, "
                + "CAST(lower_inc(" + column + ") AS TEXT) AS ca4, "
                + "CAST(upper_inc(" + column + ") AS TEXT) AS ca5, "
                + "CAST(lower_inf(" + column + ") AS TEXT) AS ca6, "
                + "CAST(upper_inf(" + column + ") AS TEXT) AS ca7, "
                + "CAST((" + column + " && " + rangeLiteral + ") AS TEXT) AS ca8, "
                + "CAST((" + column + " @> lower(" + column + ")) AS TEXT) AS ca9, "
                + "CAST((" + column + " + " + column + ") AS TEXT) AS ca10, "
                + "CAST((" + column + " * " + column + ") AS TEXT) AS ca11, "
                + "CAST((" + column + " - " + column + ") AS TEXT) AS ca12, "
                + "CAST(range_merge(" + column + ", " + rangeLiteral + ") AS TEXT) AS ca13"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + column + " IS NOT NULL"
                + " ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8, ca9, ca10, ca11, ca12, ca13 LIMIT "
                + randomLimit();
    }

    private String generateArraySelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isArrayColumn);
        if (location == null) {
            return null;
        }
        String column = qualifiedColumn("t0", location.column);
        return "SELECT array_length(" + column + ", 1) AS ca1, cardinality(" + column + ") AS ca2, "
                + "CAST(" + column + "[1] AS TEXT) AS ca3, "
                + "CAST(" + column + "[1:2] AS TEXT) AS ca4, "
                + "CAST(array_cat(" + column + ", " + column + ") AS TEXT) AS ca5, "
                + "CAST(array_position(" + column + ", " + column + "[1]) AS TEXT) AS ca6, "
                + "CAST(array_positions(" + column + ", " + column + "[1]) AS TEXT) AS ca7"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + column + " IS NOT NULL"
                + " ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7 LIMIT " + randomLimit();
    }

    private String generateRegexSelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isTextLikeColumn);
        if (location == null) {
            return null;
        }
        String textExpression = castAsText(qualifiedColumn("t0", location.column));
        String regexOperator = Randomly.fromOptions("~", "~*", "!~", "!~*");
        return "SELECT " + textExpression + " AS ca1"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + textExpression + " " + regexOperator + " '^[[:alnum:]_ -]*$'"
                + " ORDER BY ca1 LIMIT " + randomLimit();
    }

    private String generateCrossJoinSelect(List<PostgreSQLTable> tables) {
        if (tables.size() < 2) {
            return null;
        }
        PostgreSQLTable left = Randomly.fromList(tables);
        List<PostgreSQLTable> rightCandidates = tables.stream()
                .filter(table -> !table.getName().equals(left.getName()))
                .collect(Collectors.toList());
        if (rightCandidates.isEmpty()) {
            return null;
        }
        PostgreSQLTable right = Randomly.fromList(rightCandidates);
        List<ProjectedColumn> projectedColumns = new ArrayList<>();
        selectableColumns(left).forEach(column -> projectedColumns.add(new ProjectedColumn("t0", column)));
        selectableColumns(right).forEach(column -> projectedColumns.add(new ProjectedColumn("t1", column)));
        if (projectedColumns.isEmpty()) {
            return null;
        }
        List<ProjectedColumn> selectedColumns = Randomly.nonEmptySubset(projectedColumns,
                Randomly.getNotCachedInteger(1, Math.min(projectedColumns.size(), 3) + 1));
        return "SELECT " + projectedColumns(selectedColumns)
                + " FROM " + quoteIdentifier(left.getName()) + " AS t0"
                + " CROSS JOIN " + quoteIdentifier(right.getName()) + " AS t1"
                + deterministicLimit(selectedColumns.size());
    }

    private String generateLockingSelect(List<PostgreSQLTable> tables) {
        List<PostgreSQLTable> candidateTables = tables.stream()
                .filter(table -> !table.isPartitionedTable() && !selectableColumns(table).isEmpty())
                .collect(Collectors.toList());
        if (candidateTables.isEmpty()) {
            return null;
        }
        PostgreSQLTable table = Randomly.fromList(candidateTables);
        PostgreSQLColumn column = Randomly.fromList(selectableColumns(table));
        String lockClause = state.getDbmsSpecificOptions().useSharedStressTopology()
                ? Randomly.fromOptions("FOR SHARE", "FOR KEY SHARE")
                : Randomly.fromOptions("FOR UPDATE", "FOR NO KEY UPDATE", "FOR SHARE", "FOR KEY SHARE");
        return "SELECT " + castAsText(qualifiedColumn("t0", column)) + " AS ca1"
                + " FROM " + quoteIdentifier(table.getName()) + " AS t0"
                + " ORDER BY ca1 LIMIT " + randomLimit()
                + " " + lockClause;
    }

    private String generateFunctionSelect(List<PostgreSQLTable> tables) {
        List<FunctionSelectKind> functionKinds = new ArrayList<>();
        functionKinds.add(FunctionSelectKind.SYSTEM);
        if (randomColumnLocation(tables, this::isTextLikeColumn) != null) {
            functionKinds.add(FunctionSelectKind.STRING);
        }
        if (randomColumnLocation(tables, this::isNetworkColumn) != null) {
            functionKinds.add(FunctionSelectKind.NETWORK);
        }
        switch (Randomly.fromList(functionKinds)) {
            case STRING:
                return generateStringFunctionSelect(tables);
            case NETWORK:
                return generateNetworkFunctionSelect(tables);
            case SYSTEM:
                return "SELECT current_database() AS ca1, current_schema() AS ca2, "
                        + "CAST(pg_backend_pid() AS TEXT) AS ca3, "
                        + "CAST(pg_trigger_depth() AS TEXT) AS ca4, "
                        + "CAST(pg_jit_available() AS TEXT) AS ca5, "
                        + "CAST(pg_notification_queue_usage() AS TEXT) AS ca6, "
                        + "CAST(inet_client_port() AS TEXT) AS ca7, "
                        + "COALESCE(pg_current_logfile(), '') AS ca8, "
                        + "CAST(pg_is_other_temp_schema(0) AS TEXT) AS ca9 "
                        + "ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8, ca9 LIMIT 1";
            default:
                throw new AssertionError("Unhandled function SELECT kind");
        }
    }

    private String generateStringFunctionSelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isTextLikeColumn);
        if (location == null) {
            return null;
        }
        String textExpression = castAsText(qualifiedColumn("t0", location.column));
        String shortText = "left(" + textExpression + ", 32)";
        return "SELECT ascii(left(" + textExpression + ", 1)) AS ca1, "
                + "substr(" + textExpression + ", 1, 5) AS ca2, "
                + "strpos(" + textExpression + ", 'a') AS ca3, "
                + "btrim(" + textExpression + ") AS ca4, "
                + "rtrim(" + textExpression + ") AS ca5, "
                + "lpad(" + shortText + ", 8, 'x') AS ca6, "
                + "rpad(" + shortText + ", 8, 'x') AS ca7, "
                + "md5(" + textExpression + ") AS ca8, "
                + "quote_literal(" + textExpression + ") AS ca9, "
                + "quote_ident('identifier') AS ca10, "
                + "to_ascii('abc', 'LATIN1') AS ca11, "
                + "translate(" + textExpression + ", 'abc', 'xyz') AS ca12, "
                + "convert_from(convert_to(" + textExpression + ", 'UTF8'), 'UTF8') AS ca13, "
                + "CAST(get_byte(convert_to(" + textExpression + ", 'UTF8'), 0) AS TEXT) AS ca14, "
                + "to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD') AS ca15"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + textExpression + " <> ''"
                + " ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8, ca9, ca10, ca11, ca12, ca13, ca14, ca15 LIMIT "
                + randomLimit();
    }

    private String generateNetworkFunctionSelect(List<PostgreSQLTable> tables) {
        ColumnLocation location = randomColumnLocation(tables, this::isNetworkColumn);
        if (location == null) {
            return null;
        }
        String column = qualifiedColumn("t0", location.column);
        return "SELECT masklen(" + column + ") AS ca1, host(" + column + ") AS ca2, abbrev(" + column + ") AS ca3, "
                + "CAST(broadcast(" + column + ") AS TEXT) AS ca4, "
                + "CAST(hostmask(" + column + ") AS TEXT) AS ca5, "
                + "CAST(netmask(" + column + ") AS TEXT) AS ca6, "
                + "CAST(set_masklen(" + column + ", 24) AS TEXT) AS ca7, "
                + "CAST(inet_same_family(" + column + ", " + column + ") AS TEXT) AS ca8"
                + " FROM " + quoteIdentifier(location.table.getName()) + " AS t0"
                + " WHERE " + column + " IS NOT NULL"
                + " ORDER BY ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8 LIMIT " + randomLimit();
    }

    private void appendWhereClause(StringBuilder query, PostgreSQLTable table, String alias) {
        List<PostgreSQLColumn> columns = table.getColumns().stream()
                .filter(this::isPredicateColumn)
                .collect(Collectors.toList());
        if (columns.isEmpty() || !Randomly.getBoolean()) {
            return;
        }
        PostgreSQLColumn column = Randomly.fromList(columns);
        query.append(" WHERE ").append(predicate(alias, column));
    }

    private String predicate(String alias, PostgreSQLColumn column) {
        String columnName = qualifiedColumn(alias, column);
        switch (column.getType()) {
            case INT:
                return columnName + " >= " + Randomly.getNotCachedInteger(-50, 51);
            case DECIMAL:
            case FLOAT:
            case REAL:
            case MONEY:
                return columnName + " IS NOT NULL";
            case BOOLEAN:
                return columnName + " IS " + (Randomly.getBoolean() ? "TRUE" : "FALSE");
            case TEXT:
            case ENUM:
                return "CAST(" + columnName + " AS TEXT) LIKE '" + Randomly.fromOptions("a", "b", "c") + "_%'";
            case DATE:
                return columnName + " >= DATE '2023-01-01'";
            case TIME:
            case TIMETZ:
            case TIMESTAMP:
            case TIMESTAMPTZ:
            case UUID:
            case INET:
            case CIDR:
            case MACADDR:
            case BIT:
                return columnName + " IS NOT NULL";
            default:
                return columnName + " IS NOT NULL";
        }
    }

    private List<PostgreSQLTable> candidateTables() {
        return state.getSchema().getDatabaseTablesWithoutViews().stream()
                .filter(table -> !table.getColumns().isEmpty())
                .collect(Collectors.toList());
    }

    private List<PostgreSQLColumn> selectableColumns(PostgreSQLTable table) {
        return table.getColumns().stream()
                .filter(this::isSelectable)
                .collect(Collectors.toList());
    }

    private List<ColumnPair> compatibleJoinPairs(PostgreSQLTable left, PostgreSQLTable right) {
        List<ColumnPair> pairs = new ArrayList<>();
        for (PostgreSQLColumn leftColumn : left.getColumns()) {
            if (!isJoinable(leftColumn)) {
                continue;
            }
            for (PostgreSQLColumn rightColumn : right.getColumns()) {
                if (areJoinCompatible(leftColumn, rightColumn)) {
                    pairs.add(new ColumnPair(leftColumn, rightColumn));
                }
            }
        }
        return pairs;
    }

    private String projectionList(List<PostgreSQLColumn> columns, String alias, int firstAliasIndex) {
        List<ProjectedColumn> projectedColumns = new ArrayList<>();
        for (PostgreSQLColumn column : columns) {
            projectedColumns.add(new ProjectedColumn(alias, column));
        }
        return projectedColumns(projectedColumns, firstAliasIndex);
    }

    private String projectedColumns(List<ProjectedColumn> columns) {
        return projectedColumns(columns, 1);
    }

    private String projectedColumns(List<ProjectedColumn> columns, int firstAliasIndex) {
        List<String> expressions = new ArrayList<>();
        int aliasIndex = firstAliasIndex;
        for (ProjectedColumn column : columns) {
            expressions.add(castAsText(qualifiedColumn(column.tableAlias, column.column)) + " AS ca" + aliasIndex++);
        }
        return String.join(", ", expressions);
    }

    private String outerCteProjection(int columnCount) {
        List<String> expressions = new ArrayList<>();
        for (int i = 1; i <= columnCount; i++) {
            expressions.add("q.ca" + i + " AS ca" + i);
        }
        return String.join(", ", expressions);
    }

    private boolean isSelectable(PostgreSQLColumn column) {
        return column.getType() != PostgreSQLDataType.COMPOSITE
                && column.getType() != PostgreSQLDataType.ARRAY
                && column.getType() != PostgreSQLDataType.TSVECTOR
                && column.getType() != PostgreSQLDataType.TSQUERY;
    }

    private boolean isPredicateColumn(PostgreSQLColumn column) {
        return typeFamily(column) != TypeFamily.OTHER;
    }

    private boolean isJoinable(PostgreSQLColumn column) {
        TypeFamily family = typeFamily(column);
        return family != TypeFamily.OTHER
                && family != TypeFamily.JSON
                && family != TypeFamily.RANGE
                && family != TypeFamily.ARRAY;
    }

    private boolean areJoinCompatible(PostgreSQLColumn leftColumn, PostgreSQLColumn rightColumn) {
        if (!isJoinable(leftColumn) || !isJoinable(rightColumn)) {
            return false;
        }
        PostgreSQLDataType leftType = leftColumn.getType();
        PostgreSQLDataType rightType = rightColumn.getType();
        if (typeFamily(leftColumn) == TypeFamily.NUMERIC && typeFamily(rightColumn) == TypeFamily.NUMERIC) {
            return true;
        }
        if ((leftType == PostgreSQLDataType.INET || leftType == PostgreSQLDataType.CIDR)
                && (rightType == PostgreSQLDataType.INET || rightType == PostgreSQLDataType.CIDR)) {
            return true;
        }
        if (leftType != rightType) {
            return false;
        }
        if (leftType == PostgreSQLDataType.ENUM) {
            String leftUdtName = leftColumn.getUdtName();
            String rightUdtName = rightColumn.getUdtName();
            return leftUdtName != null && leftUdtName.equals(rightUdtName);
        }
        return true;
    }

    private boolean isGroupable(PostgreSQLColumn column) {
        TypeFamily family = typeFamily(column);
        return family != TypeFamily.OTHER
                && family != TypeFamily.JSON
                && family != TypeFamily.ARRAY;
    }

    private List<PostgreSQLColumn> orderableColumns(PostgreSQLTable table) {
        return table.getColumns().stream()
                .filter(column -> {
                    TypeFamily family = typeFamily(column);
                    return family != TypeFamily.OTHER
                            && family != TypeFamily.JSON
                            && family != TypeFamily.RANGE
                            && family != TypeFamily.ARRAY;
                })
                .collect(Collectors.toList());
    }

    private ColumnLocation randomColumnLocation(List<PostgreSQLTable> tables, Predicate<PostgreSQLColumn> predicate) {
        List<ColumnLocation> locations = new ArrayList<>();
        for (PostgreSQLTable table : tables) {
            for (PostgreSQLColumn column : table.getColumns()) {
                if (predicate.test(column)) {
                    locations.add(new ColumnLocation(table, column));
                }
            }
        }
        if (locations.isEmpty()) {
            return null;
        }
        return Randomly.fromList(locations);
    }

    private boolean isTextLikeColumn(PostgreSQLColumn column) {
        return column.getType() == PostgreSQLDataType.TEXT || column.getType() == PostgreSQLDataType.ENUM;
    }

    private boolean isJsonColumn(PostgreSQLColumn column) {
        return column.getType() == PostgreSQLDataType.JSON || column.getType() == PostgreSQLDataType.JSONB;
    }

    private boolean isRangeColumn(PostgreSQLColumn column) {
        return column.getType() == PostgreSQLDataType.RANGE;
    }

    private boolean isArrayColumn(PostgreSQLColumn column) {
        return column.getType() == PostgreSQLDataType.ARRAY;
    }

    private boolean isNetworkColumn(PostgreSQLColumn column) {
        return column.getType() == PostgreSQLDataType.INET || column.getType() == PostgreSQLDataType.CIDR;
    }

    private TypeFamily typeFamily(PostgreSQLColumn column) {
        switch (column.getType()) {
            case INT:
            case DECIMAL:
            case FLOAT:
            case REAL:
                return TypeFamily.NUMERIC;
            case MONEY:
                return TypeFamily.MONEY;
            case TEXT:
            case ENUM:
                return TypeFamily.TEXT;
            case BOOLEAN:
                return TypeFamily.BOOLEAN;
            case DATE:
                return TypeFamily.DATE;
            case TIME:
            case TIMETZ:
                return TypeFamily.TIME;
            case TIMESTAMP:
            case TIMESTAMPTZ:
                return TypeFamily.TIMESTAMP;
            case UUID:
                return TypeFamily.UUID;
            case INET:
            case CIDR:
            case MACADDR:
                return TypeFamily.NETWORK;
            case BIT:
                return TypeFamily.BIT;
            case JSON:
            case JSONB:
                return TypeFamily.JSON;
            case RANGE:
            case MULTIRANGE:
                return TypeFamily.RANGE;
            case ARRAY:
                return TypeFamily.ARRAY;
            default:
                return TypeFamily.OTHER;
        }
    }

    private String qualifiedColumn(String alias, PostgreSQLColumn column) {
        return alias + "." + quoteIdentifier(column.getName());
    }

    private String castAsText(String expression) {
        return "CAST(" + expression + " AS TEXT)";
    }

    private String deterministicLimit(int columnCount) {
        return " ORDER BY " + orderByAliases(columnCount) + " LIMIT " + randomLimit();
    }

    private String orderByAliases(int columnCount) {
        List<String> aliases = new ArrayList<>();
        for (int i = 1; i <= columnCount; i++) {
            aliases.add("ca" + i);
        }
        return String.join(", ", aliases);
    }

    private String quoteIdentifier(String identifier) {
        return "\"" + identifier.replace("\"", "\"\"") + "\"";
    }

    private int randomLimit() {
        return Randomly.getNotCachedInteger(1, MAX_LIMIT + 1);
    }

    private enum SelectKind {
        SIMPLE,
        JOIN,
        AGGREGATE,
        COMPOUND,
        CTE,
        WINDOW,
        JSON,
        RANGE,
        ARRAY,
        REGEX,
        CROSS_JOIN,
        LOCKING,
        FUNCTIONS
    }

    private enum FunctionSelectKind {
        SYSTEM,
        STRING,
        NETWORK
    }

    private enum TypeFamily {
        NUMERIC,
        MONEY,
        TEXT,
        BOOLEAN,
        DATE,
        TIME,
        TIMESTAMP,
        UUID,
        NETWORK,
        BIT,
        JSON,
        RANGE,
        ARRAY,
        OTHER
    }

    private static final class ColumnPair {
        private final PostgreSQLColumn left;
        private final PostgreSQLColumn right;

        private ColumnPair(PostgreSQLColumn left, PostgreSQLColumn right) {
            this.left = left;
            this.right = right;
        }
    }

    private static final class ProjectedColumn {
        private final String tableAlias;
        private final PostgreSQLColumn column;

        private ProjectedColumn(String tableAlias, PostgreSQLColumn column) {
            this.tableAlias = tableAlias;
            this.column = column;
        }
    }

    private static final class ColumnLocation {
        private final PostgreSQLTable table;
        private final PostgreSQLColumn column;

        private ColumnLocation(PostgreSQLTable table, PostgreSQLColumn column) {
            this.table = table;
            this.column = column;
        }
    }
}
