package dbradar.postgresql;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

import dbradar.IgnoreMeException;
import dbradar.Randomly;
import dbradar.SQLGlobalState;
import grammar.Token;
import dbradar.common.query.generator.ASTNode;
import dbradar.common.query.generator.KeyFunc;
import dbradar.common.query.generator.KeyFuncManager;
import dbradar.common.query.generator.QueryGenerationException;
import dbradar.common.query.generator.data.Generator;
import dbradar.common.query.generator.data.GeneratorRegister;
import dbradar.common.query.generator.data.IntGenerator;
import dbradar.common.query.generator.data.TextGenerator;
import dbradar.common.schema.AbstractTable;
import dbradar.common.schema.AbstractTableColumn;
import dbradar.common.schema.TableIndex;
import dbradar.postgresql.PostgreSQLSchema.PostgreSQLTable;

public class PostgreSQLKeyFunctionManager extends KeyFuncManager {
    private static final String SELECTED_PARTITION_PARENT = "selected_partition_parent";
    private static final String SELECTED_FUNCTION_NAME = "selected_function_name";
    private static final String SELECTED_PROCEDURE_NAME = "selected_procedure_name";
    private static final String SELECTED_RULE_NAME = "selected_rule_name";
    private static final String SELECTED_TRIGGER_NAME = "selected_trigger_name";
    private static final String SELECTED_TYPE_NAME = "selected_type_name";
    private static final String SELECTED_STATISTICS_NAME = "selected_statistics_name";
    private static final String SELECTED_TABLESPACE_NAME = "selected_tablespace_name";
    private static final int TYPE_MODIFIER_MIN = 500;
    private static final int TYPE_MODIFIER_MAX = 1000;
    private final Map<String, List<String>> insertValueCache = new HashMap<>();

    public PostgreSQLKeyFunctionManager(SQLGlobalState globalState) {
        super(globalState);

        keyFuncMap.put(DatabaseKeyFunc.KEY, new DatabaseKeyFunc());
        keyFuncMap.put(AccessMethodKeyFunc.KEY, new AccessMethodKeyFunc());
        keyFuncMap.put(DistinctTableKeyFunc.KEY, new DistinctTableKeyFunc());
        keyFuncMap.put(TableWithPrimaryKeyKeyFunc.KEY, new TableWithPrimaryKeyKeyFunc());
        keyFuncMap.put(IndexKeyFunc.KEY, new IndexKeyFunc());
        keyFuncMap.put(BrinIndexTableKeyFunc.KEY, new BrinIndexTableKeyFunc());
        keyFuncMap.put(BrinIndexColumnKeyFunc.KEY, new BrinIndexColumnKeyFunc());
        keyFuncMap.put(SpgistIndexTableKeyFunc.KEY, new SpgistIndexTableKeyFunc());
        keyFuncMap.put(SpgistIndexColumnKeyFunc.KEY, new SpgistIndexColumnKeyFunc());
        keyFuncMap.put(TextIndexTableKeyFunc.KEY, new TextIndexTableKeyFunc());
        keyFuncMap.put(TextIndexColumnKeyFunc.KEY, new TextIndexColumnKeyFunc());
        keyFuncMap.put(PrimaryKeyColumnKeyFunc.KEY, new PrimaryKeyColumnKeyFunc());
        keyFuncMap.put(MaterializedViewKeyFunc.KEY, new MaterializedViewKeyFunc());
        keyFuncMap.put(SelectedTableIndexKeyFunc.KEY, new SelectedTableIndexKeyFunc());
        keyFuncMap.put(SelectedTableUniqueIndexKeyFunc.KEY, new SelectedTableUniqueIndexKeyFunc(false));
        keyFuncMap.put(SelectedTableUniqueNotNullIndexKeyFunc.KEY, new SelectedTableUniqueNotNullIndexKeyFunc());
        keyFuncMap.put(SelectedTablePrimaryKeyConstraintKeyFunc.KEY, new SelectedTablePrimaryKeyConstraintKeyFunc());
        keyFuncMap.put(NewConstraintNameKeyFunc.KEY, new NewConstraintNameKeyFunc());
        keyFuncMap.put(SequenceKeyFunc.KEY, new SequenceKeyFunc());
        keyFuncMap.put(NewSequenceNameKeyFunc.KEY, new NewSequenceNameKeyFunc());
        keyFuncMap.put(NewFunctionNameKeyFunc.KEY, new NewFunctionNameKeyFunc());
        keyFuncMap.put(SelectedFunctionNameKeyFunc.KEY, new SelectedFunctionNameKeyFunc());
        keyFuncMap.put(NewProcedureNameKeyFunc.KEY, new NewProcedureNameKeyFunc());
        keyFuncMap.put(SelectedProcedureNameKeyFunc.KEY, new SelectedProcedureNameKeyFunc());
        keyFuncMap.put(FunctionSignatureKeyFunc.KEY, new FunctionSignatureKeyFunc());
        keyFuncMap.put(ProcedureSignatureKeyFunc.KEY, new ProcedureSignatureKeyFunc());
        keyFuncMap.put(NewRuleNameKeyFunc.KEY, new NewRuleNameKeyFunc());
        keyFuncMap.put(SelectedRuleNameKeyFunc.KEY, new SelectedRuleNameKeyFunc());
        keyFuncMap.put(NewStressTriggerNameKeyFunc.KEY, new NewStressTriggerNameKeyFunc());
        keyFuncMap.put(SelectedTriggerNameKeyFunc.KEY, new SelectedTriggerNameKeyFunc());
        keyFuncMap.put(NewTypeNameKeyFunc.KEY, new NewTypeNameKeyFunc());
        keyFuncMap.put(SelectedTypeNameKeyFunc.KEY, new SelectedTypeNameKeyFunc());
        keyFuncMap.put(NewStatisticsNameKeyFunc.KEY, new NewStatisticsNameKeyFunc());
        keyFuncMap.put(SelectedStatisticsNameKeyFunc.KEY, new SelectedStatisticsNameKeyFunc());
        keyFuncMap.put(StatisticsNameKeyFunc.KEY, new StatisticsNameKeyFunc());
        keyFuncMap.put(StatisticsColumnsKeyFunc.KEY, new StatisticsColumnsKeyFunc());
        keyFuncMap.put(StatisticsTableKeyFunc.KEY, new StatisticsTableKeyFunc());
        keyFuncMap.put(NewDomainNameKeyFunc.KEY, new NewDomainNameKeyFunc());
        keyFuncMap.put(DomainNameKeyFunc.KEY, new DomainNameKeyFunc());
        keyFuncMap.put(NewTablespaceNameKeyFunc.KEY, new NewTablespaceNameKeyFunc());
        keyFuncMap.put(TablespaceNameKeyFunc.KEY, new TablespaceNameKeyFunc());
        keyFuncMap.put(TablespaceLocationKeyFunc.KEY, new TablespaceLocationKeyFunc());
        keyFuncMap.put(TableWithConstraintKeyFunc.KEY, new TableWithConstraintKeyFunc(false));
        keyFuncMap.put(TableWithValidatableConstraintKeyFunc.KEY, new TableWithValidatableConstraintKeyFunc());
        keyFuncMap.put(SelectedTableConstraintKeyFunc.KEY, new SelectedTableConstraintKeyFunc(false));
        keyFuncMap.put(SelectedTableValidatableConstraintKeyFunc.KEY, new SelectedTableValidatableConstraintKeyFunc());
        keyFuncMap.put(IdentityColumnTableKeyFunc.KEY, new IdentityColumnTableKeyFunc());
        keyFuncMap.put(IdentityColumnKeyFunc.KEY, new IdentityColumnKeyFunc());
        keyFuncMap.put(StorageColumnKeyFunc.KEY, new StorageColumnKeyFunc());
        keyFuncMap.put(SelectedTableNameKeyFunc.KEY, new SelectedTableNameKeyFunc());
        keyFuncMap.put(NotPKColumnKeyFunc.KEY, new NotPKColumnKeyFunc());
        keyFuncMap.put(PartitionedTableWithoutDefaultKeyFunc.KEY, new PartitionedTableWithoutDefaultKeyFunc());
        keyFuncMap.put(PartitionedTableForNewPartitionKeyFunc.KEY, new PartitionedTableForNewPartitionKeyFunc());
        keyFuncMap.put(PartitionedTableWithPartitionsKeyFunc.KEY, new PartitionedTableWithPartitionsKeyFunc());
        keyFuncMap.put(PartitionOfSelectedTableKeyFunc.KEY, new PartitionOfSelectedTableKeyFunc());
        keyFuncMap.put(DetachedPartitionCandidateKeyFunc.KEY, new DetachedPartitionCandidateKeyFunc());
        keyFuncMap.put(NewPartitionBoundKeyFunc.KEY, new NewPartitionBoundKeyFunc());
        keyFuncMap.put(InsertTargetTableKeyFunc.KEY, new InsertTargetTableKeyFunc());
        keyFuncMap.put(InsertTargetTableWithoutRulesKeyFunc.KEY, new InsertTargetTableWithoutRulesKeyFunc());
        keyFuncMap.put(UpdatableTableKeyFunc.KEY, new UpdatableTableKeyFunc());
        keyFuncMap.put(UpdatableTableWithoutRulesKeyFunc.KEY, new UpdatableTableWithoutRulesKeyFunc());
        keyFuncMap.put(PartitionAwareInsertValueKeyFunc.KEY, new PartitionAwareInsertValueKeyFunc());
        keyFuncMap.put(PartitionAwareInsertRowsKeyFunc.KEY, new PartitionAwareInsertRowsKeyFunc());
        keyFuncMap.put(VarcharTypeKeyFunc.KEY, new VarcharTypeKeyFunc());
        keyFuncMap.put(CharTypeKeyFunc.KEY, new CharTypeKeyFunc());
        keyFuncMap.put(BitTypeKeyFunc.KEY, new BitTypeKeyFunc());
        keyFuncMap.put(VarbitTypeKeyFunc.KEY, new VarbitTypeKeyFunc());
        keyFuncMap.put(NumericTypeKeyFunc.KEY, new NumericTypeKeyFunc());
        keyFuncMap.put(DecimalTypeKeyFunc.KEY, new DecimalTypeKeyFunc());
        keyFuncMap.put(ArrayTypeKeyFunc.KEY, new ArrayTypeKeyFunc());
    }


    /**
     * This key function is used to return the database name. For example,
     * REINDEX DATABASE _database
     */
    private class DatabaseKeyFunc implements KeyFunc {

        public static final String KEY = "_database";

        @Override
        public void generateAST(ASTNode parent) {
            String databaseName = globalState.getDatabaseName();
            ASTNode node = new ASTNode(new Token(Token.TokenType.TERMINAL, databaseName));
            parent.addChild(node);
        }
    }

    /**
     * This key function is used to return an access method. For example,
     * CREATE TABLE t1 (c1 INT) USING _access_method
     */
    private class AccessMethodKeyFunc implements KeyFunc {

        public static final String KEY = "_access_method";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLGlobalState state = (PostgreSQLGlobalState) globalState;
            String accessMethod = state.getRandomTableAccessMethod();
            ASTNode node = new ASTNode(new Token(Token.TokenType.TERMINAL, accessMethod));
            parent.addChild(node);
        }
    }

    /**
     * This key function is used to fetch a distinct table.
     * For example, TRUNCATE TABLE _distinct_table , _distinct_table
     */
    private class DistinctTableKeyFunc implements KeyFunc {

        public static final String KEY = "_distinct_table";

        @Override
        public void generateAST(ASTNode parent) {
            try {
                List<AbstractTable<?, ?, ?>> tables = (List<AbstractTable<?, ?, ?>>) globalState.getSchema().getDatabaseTablesWithoutViews();
                List<AbstractTable<?, ?, ?>> distinctTables = tables.stream()
                        .filter(element -> !currentContext.getSelectedTables().contains(element))
                        .collect(Collectors.toList());
                if (!distinctTables.isEmpty()) {
                    AbstractTable<?, ?, ?> table = Randomly.fromList(distinctTables);
                    currentContext.addSelectedTable(table);
                    currentContext.getCurrentColumns().addAll(table.getColumns());
                    ASTNode tableNode = new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName()));
                    parent.addChild(tableNode);
                } else {
                    throw new QueryGenerationException("There are not available tables for _distinct_table.");
                }
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There are not available tables for _distinct_table.");
            }
        }
    }

    /**
     * This key function is used to return an existing index. For example, DROP
     * INDEX _index
     */
    private class IndexKeyFunc implements KeyFunc {
        public static final String KEY = "_index";

        @Override
        public void generateAST(ASTNode parent) {
            String indexName;
            try {
                TableIndex index = ((PostgreSQLSchema) globalState.getSchema()).getRandomIndex();
                indexName = index.getName();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There are no available indexes for _index.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, indexName)));
        }
    }

    private class BrinIndexTableKeyFunc implements KeyFunc {
        public static final String KEY = "_brin_index_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getRandomTableWithCompatibleIndexColumn(this::isBrinCompatibleColumn,
                    "There is no table with a BRIN-compatible column.");
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }

        private boolean isBrinCompatibleColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            switch (column.getType()) {
                case INT:
                case DATE:
                case TIME:
                case TIMESTAMP:
                    return true;
                default:
                    return false;
            }
        }
    }

    private class BrinIndexColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_brin_index_column";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    getCompatibleSelectedColumnName(this::isBrinCompatibleColumn,
                            "No selected BRIN-compatible column."))));
        }

        private boolean isBrinCompatibleColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            switch (column.getType()) {
                case INT:
                case DATE:
                case TIME:
                case TIMESTAMP:
                    return true;
                default:
                    return false;
            }
        }
    }

    private class SpgistIndexTableKeyFunc implements KeyFunc {
        public static final String KEY = "_spgist_index_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getRandomTableWithCompatibleIndexColumn(this::isSpgistCompatibleColumn,
                    "There is no table with an SP-GiST-compatible column.");
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }

        private boolean isSpgistCompatibleColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.POINT;
        }
    }

    private class SpgistIndexColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_spgist_index_column";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    getCompatibleSelectedColumnName(this::isSpgistCompatibleColumn,
                            "No selected SP-GiST-compatible column."))));
        }

        private boolean isSpgistCompatibleColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.POINT;
        }
    }

    private class TextIndexTableKeyFunc implements KeyFunc {
        public static final String KEY = "_text_index_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getRandomTableWithCompatibleIndexColumn(this::isTextIndexColumn,
                    "There is no table with a text-compatible index column.");
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }

        private boolean isTextIndexColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.TEXT
                    || column.getType() == PostgreSQLSchema.PostgreSQLDataType.ENUM;
        }
    }

    private class TextIndexColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_text_index_column";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    getCompatibleSelectedColumnName(this::isTextIndexColumn,
                            "No selected text-compatible index column."))));
        }

        private boolean isTextIndexColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.TEXT
                    || column.getType() == PostgreSQLSchema.PostgreSQLDataType.ENUM;
        }
    }

    private class PrimaryKeyColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_primary_key_column";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for primary-key column lookup.");
            }
            TableIndex primaryKeyIndex = getPrimaryKeyIndex(table);
            if (primaryKeyIndex == null || primaryKeyIndex.getColumnNames().isEmpty()) {
                throw new QueryGenerationException("No primary-key column on selected table.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    Randomly.fromList(primaryKeyIndex.getColumnNames()))));
        }
    }

    private class MaterializedViewKeyFunc implements KeyFunc {
        public static final String KEY = "_materialized_view";

        @Override
        public void generateAST(ASTNode parent) {
            List<String> materializedViews = new ArrayList<>();
            String query = "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    + "WHERE n.nspname = 'public' AND c.relkind = 'm' ORDER BY c.relname";
            try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                    ResultSet resultSet = statement.executeQuery(query)) {
                while (resultSet.next()) {
                    materializedViews.add(resultSet.getString(1));
                }
            } catch (SQLException e) {
                throw new QueryGenerationException("Unable to query materialized views: " + e.getMessage());
            }
            if (materializedViews.isEmpty()) {
                throw new QueryGenerationException("There are no available materialized views.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(materializedViews))));
        }
    }

    private class TableWithPrimaryKeyKeyFunc implements KeyFunc {
        public static final String KEY = "_table_with_primary_key";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomTable(t -> !t.isView() && getPrimaryKeyIndex(t) != null);
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There are no tables with primary keys.");
            }
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class SelectedTableIndexKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_table_index";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for selected-table index lookup.");
            }
            List<TableIndex> indexes = table.getIndexes().stream()
                    .filter(index -> !isPrimaryKeyIndex(index))
                    .collect(Collectors.toList());
            if (indexes.isEmpty()) {
                throw new QueryGenerationException("No suitable selected-table index.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(indexes).getName())));
        }
    }

    private class SelectedTableUniqueIndexKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_table_unique_index";
        private final boolean requireNotNullColumns;

        SelectedTableUniqueIndexKeyFunc(boolean requireNotNullColumns) {
            this.requireNotNullColumns = requireNotNullColumns;
        }

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for selected-table index lookup.");
            }
            List<TableIndex> indexes = table.getIndexes().stream()
                    .filter(TableIndex::isUnique)
                    .filter(index -> !isPrimaryKeyIndex(index))
                    .filter(index -> !requireNotNullColumns || allIndexedColumnsAreNotNull(table, index))
                    .collect(Collectors.toList());
            if (indexes.isEmpty()) {
                throw new QueryGenerationException("No suitable selected-table unique index.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(indexes).getName())));
        }
    }

    private class SelectedTableUniqueNotNullIndexKeyFunc extends SelectedTableUniqueIndexKeyFunc {
        public static final String KEY = "_selected_table_unique_not_null_index";

        SelectedTableUniqueNotNullIndexKeyFunc() {
            super(true);
        }
    }

    private class SelectedTablePrimaryKeyConstraintKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_table_primary_key_constraint";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for primary-key constraint lookup.");
            }
            TableIndex primaryKeyIndex = getPrimaryKeyIndex(table);
            if (primaryKeyIndex == null) {
                throw new QueryGenerationException("No primary-key constraint on selected table.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, primaryKeyIndex.getName())));
        }
    }

    private static boolean isPrimaryKeyIndex(TableIndex index) {
        if (index instanceof PostgreSQLSchema.PostgreSQLIndex pgIndex) {
            return pgIndex.isPrimaryKey();
        }
        return index.getName() != null && index.getName().contains("pkey");
    }

    private static TableIndex getPrimaryKeyIndex(PostgreSQLTable table) {
        for (TableIndex index : table.getIndexes()) {
            if (isPrimaryKeyIndex(index)) {
                return index;
            }
        }
        return null;
    }

    private static boolean allIndexedColumnsAreNotNull(PostgreSQLTable table, TableIndex index) {
        if (index.getColumnNames() == null || index.getColumnNames().isEmpty()) {
            return false;
        }
        for (String indexColumn : index.getColumnNames()) {
            boolean foundNotNull = table.getColumns().stream()
                    .filter(column -> Objects.equals(column.getName(), indexColumn))
                    .anyMatch(AbstractTableColumn::isNotNull);
            if (!foundNotNull) {
                return false;
            }
        }
        return true;
    }

    /**
     * This key function is used to fetch a new constraint name. For example, ALTER
     * TABLE _TABLE ADD CONSTRAINT _new_constraint_name UNIQUE _index
     */
    private class NewConstraintNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_constraint_name";

        @Override
        public void generateAST(ASTNode parent) {
            int length = Integer.parseInt(new IntGenerator(1, 10, "").generate(globalState));
            String constraintName = new TextGenerator(length).generate(globalState);
            constraintName = constraintName.substring(1, constraintName.length() - 1);
            String prefix = globalState.getGeneratedObjectNamePrefix();
            if (!prefix.isEmpty()) {
                constraintName = prefix + constraintName;
            }
            ASTNode tableNode = new ASTNode(new Token(Token.TokenType.TERMINAL, constraintName));
            parent.addChild(tableNode);
        }
    }

    private class SequenceKeyFunc implements KeyFunc {
        public static final String KEY = "_sequence";

        @Override
        public void generateAST(ASTNode parent) {
            List<String> sequences = new ArrayList<>();
            String query = "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    + "WHERE n.nspname = 'public' AND c.relkind = 'S' ORDER BY c.relname";
            try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                    ResultSet resultSet = statement.executeQuery(query)) {
                while (resultSet.next()) {
                    sequences.add(resultSet.getString(1));
                }
            } catch (SQLException e) {
                throw new QueryGenerationException("Unable to query sequences: " + e.getMessage());
            }
            if (sequences.isEmpty()) {
                throw new QueryGenerationException("There are no available sequences for _sequence.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(sequences))));
        }
    }

    private class NewSequenceNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_sequence_name";

        @Override
        public void generateAST(ASTNode parent) {
            String prefix = globalState.getGeneratedObjectNamePrefix();
            int suffix = Randomly.getNotCachedInteger(0, Integer.MAX_VALUE);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, prefix + "seq" + suffix)));
        }
    }

    private class NewFunctionNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_function_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = "public." + generatedName("fn");
            currentContext.setProperty(SELECTED_FUNCTION_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedFunctionNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_function_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_FUNCTION_NAME, "No selected function name."))));
        }
    }

    private class NewProcedureNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_procedure_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = "public." + generatedName("proc");
            currentContext.setProperty(SELECTED_PROCEDURE_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedProcedureNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_procedure_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_PROCEDURE_NAME, "No selected procedure name."))));
        }
    }

    private class FunctionSignatureKeyFunc extends RoutineSignatureKeyFunc {
        public static final String KEY = "_function_signature";

        FunctionSignatureKeyFunc() {
            super("f", "There are no available functions for _function_signature.");
        }
    }

    private class ProcedureSignatureKeyFunc extends RoutineSignatureKeyFunc {
        public static final String KEY = "_procedure_signature";

        ProcedureSignatureKeyFunc() {
            super("p", "There are no available procedures for _procedure_signature.");
        }
    }

    private class RoutineSignatureKeyFunc implements KeyFunc {
        private final String proKind;
        private final String emptyMessage;

        RoutineSignatureKeyFunc(String proKind, String emptyMessage) {
            this.proKind = proKind;
            this.emptyMessage = emptyMessage;
        }

        @Override
        public void generateAST(ASTNode parent) {
            List<String> routines = new ArrayList<>();
            String query = "SELECT quote_ident(n.nspname) || '.' || quote_ident(p.proname) || '(' "
                    + "|| pg_get_function_identity_arguments(p.oid) || ')' "
                    + "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                    + "WHERE n.nspname = 'public' AND p.prokind = '" + proKind + "' "
                    + "ORDER BY p.proname, pg_get_function_identity_arguments(p.oid)";
            try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                    ResultSet resultSet = statement.executeQuery(query)) {
                while (resultSet.next()) {
                    routines.add(resultSet.getString(1));
                }
            } catch (SQLException e) {
                throw new QueryGenerationException("Unable to query routine signatures: " + e.getMessage());
            }
            if (routines.isEmpty()) {
                throw new QueryGenerationException(emptyMessage);
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(routines))));
        }
    }

    private class NewRuleNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_rule_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = generatedName("rule");
            currentContext.setProperty(SELECTED_RULE_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedRuleNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_rule_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_RULE_NAME, "No selected rule name."))));
        }
    }

    private class NewStressTriggerNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_stress_trigger_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = generatedName("trg");
            currentContext.setProperty(SELECTED_TRIGGER_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedTriggerNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_trigger_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_TRIGGER_NAME, "No selected trigger name."))));
        }
    }

    private class NewTypeNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_type_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = generatedName("typ");
            currentContext.setProperty(SELECTED_TYPE_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedTypeNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_type_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_TYPE_NAME, "No selected type name."))));
        }
    }

    private class NewStatisticsNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_statistics_name";

        @Override
        public void generateAST(ASTNode parent) {
            String name = generatedName("stat");
            currentContext.setProperty(SELECTED_STATISTICS_NAME, name);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, name)));
        }
    }

    private class SelectedStatisticsNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_statistics_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    requireStringProperty(SELECTED_STATISTICS_NAME, "No selected statistics name."))));
        }
    }

    private class StatisticsNameKeyFunc implements KeyFunc {
        public static final String KEY = "_statistics";

        @Override
        public void generateAST(ASTNode parent) {
            List<String> statistics = new ArrayList<>();
            String query = "SELECT stxname FROM pg_statistic_ext ORDER BY stxname";
            try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                    ResultSet resultSet = statement.executeQuery(query)) {
                while (resultSet.next()) {
                    statistics.add(resultSet.getString(1));
                }
            } catch (SQLException e) {
                throw new QueryGenerationException("Unable to query statistics objects: " + e.getMessage());
            }
            if (statistics.isEmpty()) {
                throw new QueryGenerationException("There are no available statistics objects.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(statistics))));
        }
    }

    private class StatisticsColumnsKeyFunc implements KeyFunc {
        public static final String KEY = "_statistics_columns";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomTable(t -> !t.isView()
                        && !t.isPartition()
                        && t.getColumns().stream().filter(this::isStatisticsColumn).count() >= 2);
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no table with enough columns for CREATE STATISTICS.");
            }
            rememberSelectedTable(table);
            List<PostgreSQLSchema.PostgreSQLColumn> columns = table.getColumns().stream()
                    .filter(this::isStatisticsColumn)
                    .collect(Collectors.toList());
            List<PostgreSQLSchema.PostgreSQLColumn> selectedColumns = Randomly.nonEmptySubset(columns, 2);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    selectedColumns.get(0).getName() + ", " + selectedColumns.get(1).getName())));
        }

        private boolean isStatisticsColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            switch (column.getType()) {
                case INT:
                case BOOLEAN:
                case TEXT:
                case DECIMAL:
                case FLOAT:
                case REAL:
                case MONEY:
                case DATE:
                case TIME:
                case TIMETZ:
                case TIMESTAMP:
                case TIMESTAMPTZ:
                case UUID:
                case INET:
                case CIDR:
                case MACADDR:
                    return true;
                default:
                    return false;
            }
        }
    }

    private class StatisticsTableKeyFunc implements KeyFunc {
        public static final String KEY = "_statistics_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for statistics generation.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class NewDomainNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_domain_name";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, generatedName("dom"))));
        }
    }

    private class DomainNameKeyFunc implements KeyFunc {
        public static final String KEY = "_domain";

        @Override
        public void generateAST(ASTNode parent) {
            List<String> domains = querySingleColumn(
                    "SELECT quote_ident(t.typname) FROM pg_type t "
                            + "JOIN pg_namespace n ON n.oid = t.typnamespace "
                            + "WHERE n.nspname = 'public' AND t.typtype = 'd' ORDER BY t.typname",
                    "Unable to query domains.");
            if (domains.isEmpty()) {
                throw new QueryGenerationException("There are no available domains.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(domains))));
        }
    }

    private class NewTablespaceNameKeyFunc implements KeyFunc {
        public static final String KEY = "_new_tablespace_name";

        @Override
        public void generateAST(ASTNode parent) {
            requireTablespaceGenerationEnabled();
            String tablespaceName = generatedName("tsp");
            currentContext.setProperty(SELECTED_TABLESPACE_NAME, tablespaceName);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, tablespaceName)));
        }
    }

    private class TablespaceNameKeyFunc implements KeyFunc {
        public static final String KEY = "_tablespace";

        @Override
        public void generateAST(ASTNode parent) {
            requireTablespaceGenerationEnabled();
            String prefix = globalState.getGeneratedObjectNamePrefix() + "tsp";
            List<String> tablespaces = querySingleColumn(
                    "SELECT quote_ident(spcname) FROM pg_tablespace "
                            + "WHERE spcname LIKE '" + sqlLiteral(prefix) + "%' ORDER BY spcname",
                    "Unable to query tablespaces.");
            if (tablespaces.isEmpty()) {
                throw new QueryGenerationException("There are no generated tablespaces to drop.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(tablespaces))));
        }
    }

    private class TablespaceLocationKeyFunc implements KeyFunc {
        public static final String KEY = "_tablespace_location";

        @Override
        public void generateAST(ASTNode parent) {
            requireTablespaceGenerationEnabled();
            String tablespaceName = requireStringProperty(SELECTED_TABLESPACE_NAME,
                    "No selected tablespace name.");
            Path location = Paths.get("target", "dbradar-tablespaces", globalState.getDatabaseName(),
                    tablespaceName).toAbsolutePath();
            try {
                Files.createDirectories(location);
            } catch (IOException e) {
                throw new QueryGenerationException("Unable to create tablespace directory: " + e.getMessage());
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "'" + location.toString().replace("'", "''") + "'")));
        }
    }

    private class TableWithConstraintKeyFunc implements KeyFunc {
        public static final String KEY = "_table_with_constraint";
        private final boolean validatableOnly;

        TableWithConstraintKeyFunc(boolean validatableOnly) {
            this.validatableOnly = validatableOnly;
        }

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getRandomTableWithConstraint(validatableOnly);
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class TableWithValidatableConstraintKeyFunc extends TableWithConstraintKeyFunc {
        public static final String KEY = "_table_with_validatable_constraint";

        TableWithValidatableConstraintKeyFunc() {
            super(true);
        }
    }

    private class SelectedTableConstraintKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_table_constraint";
        private final boolean validatableOnly;

        SelectedTableConstraintKeyFunc(boolean validatableOnly) {
            this.validatableOnly = validatableOnly;
        }

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table for constraint lookup.");
            }
            List<String> constraints = getTableConstraints(table.getName(), validatableOnly);
            if (constraints.isEmpty()) {
                throw new QueryGenerationException("No selected-table constraints.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, Randomly.fromList(constraints))));
        }
    }

    private class SelectedTableValidatableConstraintKeyFunc extends SelectedTableConstraintKeyFunc {
        public static final String KEY = "_selected_table_validatable_constraint";

        SelectedTableValidatableConstraintKeyFunc() {
            super(true);
        }
    }

    private class IdentityColumnTableKeyFunc implements KeyFunc {
        public static final String KEY = "_identity_column_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getRandomTableWithCompatibleIndexColumn(this::isIdentityCandidate,
                    "There is no table with an identity-compatible column.");
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }

        private boolean isIdentityCandidate(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.INT
                    && column.getColumnDefault() == null
                    && !column.isGenerated();
        }
    }

    private class IdentityColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_identity_column";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    getCompatibleSelectedColumnName(this::isIdentityCandidate,
                            "No selected identity-compatible column."))));
        }

        private boolean isIdentityCandidate(PostgreSQLSchema.PostgreSQLColumn column) {
            return column.getType() == PostgreSQLSchema.PostgreSQLDataType.INT
                    && column.getColumnDefault() == null
                    && !column.isGenerated();
        }
    }

    private class StorageColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_storage_column";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    getCompatibleSelectedColumnName(this::isStorageColumn,
                            "No selected storage-configurable column."))));
        }

        private boolean isStorageColumn(PostgreSQLSchema.PostgreSQLColumn column) {
            switch (column.getType()) {
                case TEXT:
                case BYTEA:
                case XML:
                case JSON:
                case JSONB:
                case ARRAY:
                    return true;
                default:
                    return false;
            }
        }
    }

    private class SelectedTableNameKeyFunc implements KeyFunc {
        public static final String KEY = "_selected_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLTable table = getSelectedTableOrNull();
            if (table == null) {
                throw new QueryGenerationException("No selected table.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    /**
     * This key function is used to return an existing column which is not primary key. For example,
     * ALTER TABLE _table ALTER _not_pk_column DROP NOT NULL
     */
    private class NotPKColumnKeyFunc implements KeyFunc {
        public static final String KEY = "_not_pk_column";

        @Override
        public void generateAST(ASTNode parent) {
            List<AbstractTableColumn<?, ?>> columns = new ArrayList<>();
            for (AbstractTableColumn<?, ?> col : currentContext.getCurrentColumns()) {
                if (!col.isPrimaryKey()) {
                    columns.add(col);
                }
            }
            if (columns.isEmpty()) {
                throw new QueryGenerationException("No such column");
            }
            AbstractTableColumn<?, ?> col = Randomly.fromList(columns);
            currentContext.addSelectedColumn(col);
            ASTNode columnNode = new ASTNode(new Token(Token.TokenType.TERMINAL, getColumnName(col)));
            parent.addChild(columnNode);
        }
    }

    private class PartitionedTableWithoutDefaultKeyFunc implements KeyFunc {
        public static final String KEY = "_partitioned_table_without_default";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomPartitionedTableWithoutDefaultPartition();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no available partitioned table without default partition.");
            }
            rememberSelectedPartitionedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class PartitionedTableWithPartitionsKeyFunc implements KeyFunc {
        public static final String KEY = "_partitioned_table_with_partitions";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomPartitionedTableWithPartitions();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no partitioned table with partitions.");
            }
            rememberSelectedPartitionedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class PartitionedTableForNewPartitionKeyFunc implements KeyFunc {
        public static final String KEY = "_partitioned_table_for_new_partition";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomPartitionedTableForPartitionCreation();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no partitioned table that can accept an additional partition.");
            }
            rememberSelectedPartitionedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class PartitionOfSelectedTableKeyFunc implements KeyFunc {
        public static final String KEY = "_partition_of_selected_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable selectedParent = getSelectedPartitionedTable();
            PostgreSQLTable partition;
            try {
                partition = schema.getRandomPartitionOf(selectedParent);
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no partition for the selected partitioned table.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, partition.getName())));
        }
    }

    private class DetachedPartitionCandidateKeyFunc implements KeyFunc {
        public static final String KEY = "_detached_partition_candidate";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable selectedParent = getSelectedPartitionedTable();
            PostgreSQLTable candidate;
            try {
                candidate = schema.getRandomDetachedPartitionCandidate(selectedParent);
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no detached partition candidate for the selected partitioned table.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, candidate.getName())));
        }
    }

    private class NewPartitionBoundKeyFunc implements KeyFunc {
        public static final String KEY = "_new_partition_bound";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable selectedParent = getSelectedPartitionedTable();
            String partitionBound;
            try {
                partitionBound = schema.generateNewPartitionBound(selectedParent);
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("Unable to generate a valid partition bound.");
            }
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, partitionBound)));
        }
    }

    private class InsertTargetTableKeyFunc implements KeyFunc {
        public static final String KEY = "_insert_target_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomInsertTargetTable();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no available insert target table.");
            }
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class InsertTargetTableWithoutRulesKeyFunc implements KeyFunc {
        public static final String KEY = "_insert_target_table_without_rules";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            Set<String> tablesWithRules = getTablesWithInsertOrUpdateRules();
            PostgreSQLTable table;
            try {
                table = schema.getRandomTable(t -> !t.isView()
                        && !t.isPartition()
                        && !tablesWithRules.contains(t.getName())
                        && (!t.isPartitionedTable() || PostgreSQLPartitionSupport.hasUsableInsertRoute(schema, t)));
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no insert target table without INSERT/UPDATE rules.");
            }
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class UpdatableTableKeyFunc implements KeyFunc {
        public static final String KEY = "_updatable_table";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            PostgreSQLTable table;
            try {
                table = schema.getRandomUpdatableTable();
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no available updatable table.");
            }
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class UpdatableTableWithoutRulesKeyFunc implements KeyFunc {
        public static final String KEY = "_updatable_table_without_rules";

        @Override
        public void generateAST(ASTNode parent) {
            PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
            Set<String> tablesWithRules = getTablesWithInsertOrUpdateRules();
            PostgreSQLTable table;
            try {
                table = schema.getRandomTable(t -> !t.isView()
                        && !t.isPartition()
                        && !t.isPartitionedTable()
                        && !tablesWithRules.contains(t.getName()));
            } catch (IgnoreMeException ignored) {
                throw new QueryGenerationException("There is no updatable table without INSERT/UPDATE rules.");
            }
            rememberSelectedTable(table);
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, table.getName())));
        }
    }

    private class PartitionAwareInsertValueKeyFunc implements KeyFunc {
        public static final String KEY = "_insert_values";

        @Override
        public void generateAST(ASTNode parent) {
            Map<String, String> partitionValues = Map.of();
            PostgreSQLTable selectedTable = getSelectedTableOrNull();
            if (selectedTable != null && selectedTable.isPartitionedTable()) {
                try {
                    partitionValues = ((PostgreSQLSchema) globalState.getSchema()).generatePartitionInsertValues(selectedTable);
                } catch (IgnoreMeException ignored) {
                    throw new QueryGenerationException("Unable to generate insert values for a partitioned table.");
                }
            }

            int colSize = currentContext.getReturnedColumns().size();
            for (int i = 0; i < colSize; i++) {
                AbstractTableColumn<?, ?> col = currentContext.getReturnedColumns().poll();
                String value = partitionValues.get(col.getName());
                if (value == null) {
                    value = generateInsertValue(col, 0);
                }
                ASTNode valueNode = new ASTNode(new Token(Token.TokenType.TERMINAL, value));
                parent.addChild(valueNode);
                if (i != colSize - 1) {
                    parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, ",")));
                }
            }
        }
    }

    private class PartitionAwareInsertRowsKeyFunc implements KeyFunc {
        public static final String KEY = "_insert_rows";

        @Override
        public void generateAST(ASTNode parent) {
            List<AbstractTableColumn<?, ?>> columns = new ArrayList<>(currentContext.getReturnedColumns());
            if (columns.isEmpty()) {
                throw new QueryGenerationException("There are no insert columns for _insert_rows.");
            }
            int rowCount = shouldGenerateBulkInsertRows()
                    ? Randomly.getNotCachedInteger(100, 1001)
                    : Randomly.getNotCachedInteger(1, 5);
            for (int rowIndex = 0; rowIndex < rowCount; rowIndex++) {
                parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, "(")));
                Map<String, String> partitionValues = generatePartitionInsertValuesIfNeeded();
                for (int columnIndex = 0; columnIndex < columns.size(); columnIndex++) {
                    AbstractTableColumn<?, ?> column = columns.get(columnIndex);
                    String value = partitionValues.get(column.getName());
                    if (value == null) {
                        value = generateColumnValue(column, rowIndex);
                    }
                    parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, value)));
                    if (columnIndex != columns.size() - 1) {
                        parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, ",")));
                    }
                }
                parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, ")")));
                if (rowIndex != rowCount - 1) {
                    parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL, ",")));
                }
            }
        }

        private Map<String, String> generatePartitionInsertValuesIfNeeded() {
            PostgreSQLTable selectedTable = getSelectedTableOrNull();
            if (selectedTable != null && selectedTable.isPartitionedTable()) {
                try {
                    return ((PostgreSQLSchema) globalState.getSchema()).generatePartitionInsertValues(selectedTable);
                } catch (IgnoreMeException ignored) {
                    throw new QueryGenerationException("Unable to generate insert values for a partitioned table.");
                }
            }
            return Map.of();
        }

        private String generateColumnValue(AbstractTableColumn<?, ?> column, int rowIndex) {
            ForeignKeyValue foreignKeyValue = findForeignKeyValue(column);
            if (foreignKeyValue.applies()) {
                if (foreignKeyValue.value() != null) {
                    return foreignKeyValue.value();
                }
                if (column.isNotNull()) {
                    throw new QueryGenerationException("No referenced value available for non-null foreign key.");
                }
                return "null";
            }

            String cacheKey = getInsertValueCacheKey(column);
            List<String> cachedValues = insertValueCache.get(cacheKey);
            if (rowIndex > 0 && rowIndex % 2 == 1 && cachedValues != null && !cachedValues.isEmpty()) {
                return Randomly.fromList(cachedValues);
            }

            Generator generator = GeneratorRegister.getGenerator(column, globalState);
            String value = generator.generate(globalState);
            while (column.isNotNull() && value.equals("null")) {
                value = generator.generate(globalState);
            }
            if (!"null".equals(value)) {
                insertValueCache.computeIfAbsent(cacheKey, ignored -> new ArrayList<>()).add(value);
            }
            return value;
        }

        private String getInsertValueCacheKey(AbstractTableColumn<?, ?> column) {
            return column.getName() + ":" + column.getType();
        }

        private boolean shouldGenerateBulkInsertRows() {
            if (!(globalState.getDbmsSpecificOptions() instanceof PostgreSQLOptions)) {
                return false;
            }
            return ((PostgreSQLOptions) globalState.getDbmsSpecificOptions()).allowBulkInsert;
        }
    }

    private class VarcharTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_varchar_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "VARCHAR(" + randomUpperHalfTypeModifier() + ")")));
        }
    }

    private class CharTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_char_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "CHAR(" + randomUpperHalfTypeModifier() + ")")));
        }
    }

    private class BitTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_bit_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "BIT(" + randomUpperHalfTypeModifier() + ")")));
        }
    }

    private class VarbitTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_varbit_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "VARBIT(" + randomUpperHalfTypeModifier() + ")")));
        }
    }

    private class NumericTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_numeric_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "NUMERIC" + randomPrecisionAndScale())));
        }
    }

    private class DecimalTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_decimal_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    "DECIMAL" + randomPrecisionAndScale())));
        }
    }

    private class ArrayTypeKeyFunc implements KeyFunc {
        public static final String KEY = "_array_type";

        @Override
        public void generateAST(ASTNode parent) {
            parent.addChild(new ASTNode(new Token(Token.TokenType.TERMINAL,
                    Randomly.fromOptions("INTEGER[]", "INTEGER[][]", "TEXT[]", "BOOLEAN[]", "UUID[]",
                            "BIGINT[]", "SMALLINT[]", "REAL[]", "DOUBLE PRECISION[]", "NUMERIC[]"))));
        }
    }

    private static int randomUpperHalfTypeModifier() {
        return Randomly.getNotCachedInteger(TYPE_MODIFIER_MIN, TYPE_MODIFIER_MAX + 1);
    }

    private static String randomPrecisionAndScale() {
        int precision = randomUpperHalfTypeModifier();
        int scale = Randomly.getNotCachedInteger(precision / 2, precision);
        return String.format("(%d,%d)", precision, scale);
    }

    private String generatedName(String stem) {
        String prefix = globalState.getGeneratedObjectNamePrefix();
        int suffix = Randomly.getNotCachedInteger(0, Integer.MAX_VALUE);
        return prefix + stem + suffix;
    }

    private PostgreSQLTable getRandomTableWithCompatibleIndexColumn(
            Predicate<PostgreSQLSchema.PostgreSQLColumn> predicate, String emptyMessage) {
        PostgreSQLSchema schema = (PostgreSQLSchema) globalState.getSchema();
        try {
            return schema.getRandomTable(t -> !t.isView()
                    && !t.isPartition()
                    && t.getColumns().stream().anyMatch(predicate));
        } catch (IgnoreMeException ignored) {
            throw new QueryGenerationException(emptyMessage);
        }
    }

    private String getCompatibleSelectedColumnName(Predicate<PostgreSQLSchema.PostgreSQLColumn> predicate,
                                                  String emptyMessage) {
        List<String> columns = new ArrayList<>();
        for (AbstractTableColumn<?, ?> column : currentContext.getCurrentColumns()) {
            if (column instanceof PostgreSQLSchema.PostgreSQLColumn
                    && predicate.test((PostgreSQLSchema.PostgreSQLColumn) column)) {
                columns.add(getColumnName(column));
            }
        }
        if (columns.isEmpty()) {
            throw new QueryGenerationException(emptyMessage);
        }
        return Randomly.fromList(columns);
    }

    private String requireStringProperty(String key, String errorMessage) {
        Object value = currentContext.getProperty(key);
        if (!(value instanceof String)) {
            throw new QueryGenerationException(errorMessage);
        }
        return (String) value;
    }

    private Set<String> getTablesWithInsertOrUpdateRules() {
        Set<String> tableNames = new HashSet<>();
        String query = "SELECT DISTINCT tablename FROM pg_rules "
                + "WHERE rulename <> '_RETURN' "
                + "AND (definition ILIKE '%ON INSERT TO%' OR definition ILIKE '%ON UPDATE TO%')";
        try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                ResultSet resultSet = statement.executeQuery(query)) {
            while (resultSet.next()) {
                tableNames.add(resultSet.getString(1));
            }
        } catch (SQLException e) {
            throw new QueryGenerationException("Unable to query INSERT/UPDATE rules: " + e.getMessage());
        }
        return tableNames;
    }

    private PostgreSQLTable getSelectedPartitionedTable() {
        Object selectedParent = currentContext.getProperty(SELECTED_PARTITION_PARENT);
        if (!(selectedParent instanceof PostgreSQLTable)) {
            throw new QueryGenerationException("No selected partitioned table.");
        }
        return (PostgreSQLTable) selectedParent;
    }

    private void rememberSelectedPartitionedTable(PostgreSQLTable table) {
        rememberSelectedTable(table);
        currentContext.setProperty(SELECTED_PARTITION_PARENT, table);
    }

    private void rememberSelectedTable(PostgreSQLTable table) {
        currentContext.addSelectedTable(table);
        currentContext.getCurrentColumns().clear();
        currentContext.getCurrentColumns().addAll(table.getColumns());
    }

    private PostgreSQLTable getSelectedTableOrNull() {
        if (currentContext.getSelectedTables().isEmpty()) {
            return null;
        }
        AbstractTable<?, ?, ?> table = currentContext.getSelectedTables().get(0);
        if (table instanceof PostgreSQLTable) {
            return (PostgreSQLTable) table;
        }
        return null;
    }

    private String generateInsertValue(AbstractTableColumn<?, ?> column, int rowIndex) {
        ForeignKeyValue foreignKeyValue = findForeignKeyValue(column);
        if (foreignKeyValue.applies()) {
            if (foreignKeyValue.value() != null) {
                return foreignKeyValue.value();
            }
            if (column.isNotNull()) {
                throw new QueryGenerationException("No referenced value available for non-null foreign key.");
            }
            return "null";
        }

        String cacheKey = column.getName() + ":" + column.getType();
        List<String> cachedValues = insertValueCache.get(cacheKey);
        if (rowIndex > 0 && rowIndex % 2 == 1 && cachedValues != null && !cachedValues.isEmpty()) {
            return Randomly.fromList(cachedValues);
        }
        Generator generator = GeneratorRegister.getGenerator(column, globalState);
        String value = generator.generate(globalState);
        while (column.isNotNull() && value.equals("null")) {
            value = generator.generate(globalState);
        }
        if (!"null".equals(value)) {
            insertValueCache.computeIfAbsent(cacheKey, ignored -> new ArrayList<>()).add(value);
        }
        return value;
    }

    private ForeignKeyValue findForeignKeyValue(AbstractTableColumn<?, ?> column) {
        PostgreSQLTable selectedTable = getSelectedTableOrNull();
        if (selectedTable == null || !(column instanceof PostgreSQLSchema.PostgreSQLColumn)) {
            return ForeignKeyValue.notForeignKey();
        }
        String cacheKey = "fk:" + selectedTable.getName() + ":" + column.getName();
        if (insertValueCache.containsKey(cacheKey)) {
            List<String> cachedValues = insertValueCache.get(cacheKey);
            return cachedValues.isEmpty() ? ForeignKeyValue.noAvailableValue()
                    : ForeignKeyValue.of(Randomly.fromList(cachedValues));
        }

        List<ForeignKeyTarget> targets = getForeignKeyTargets(selectedTable.getName(), column.getName());
        if (targets.isEmpty()) {
            return ForeignKeyValue.notForeignKey();
        }

        List<String> referencedValues = new ArrayList<>();
        for (ForeignKeyTarget target : targets) {
            referencedValues.addAll(querySingleColumn(
                    "SELECT quote_nullable(" + quoteIdentifier(target.columnName()) + "::text) "
                            + "FROM " + quoteIdentifier(target.tableName()) + " "
                            + "WHERE " + quoteIdentifier(target.columnName()) + " IS NOT NULL LIMIT 20",
                    "Unable to query referenced foreign-key values."));
        }
        insertValueCache.put(cacheKey, referencedValues);
        return referencedValues.isEmpty() ? ForeignKeyValue.noAvailableValue()
                : ForeignKeyValue.of(Randomly.fromList(referencedValues));
    }

    private List<ForeignKeyTarget> getForeignKeyTargets(String tableName, String columnName) {
        List<ForeignKeyTarget> targets = new ArrayList<>();
        String query = "SELECT target_table.relname AS target_table, target_att.attname AS target_column "
                + "FROM pg_constraint con "
                + "JOIN pg_class source_table ON source_table.oid = con.conrelid "
                + "JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace "
                + "JOIN pg_class target_table ON target_table.oid = con.confrelid "
                + "JOIN unnest(con.conkey) WITH ORDINALITY AS source_cols(attnum, ord) ON true "
                + "JOIN unnest(con.confkey) WITH ORDINALITY AS target_cols(attnum, ord) "
                + "ON target_cols.ord = source_cols.ord "
                + "JOIN pg_attribute source_att ON source_att.attrelid = source_table.oid "
                + "AND source_att.attnum = source_cols.attnum "
                + "JOIN pg_attribute target_att ON target_att.attrelid = target_table.oid "
                + "AND target_att.attnum = target_cols.attnum "
                + "WHERE source_ns.nspname = 'public' AND con.contype = 'f' "
                + "AND source_table.relname = '" + sqlLiteral(tableName) + "' "
                + "AND source_att.attname = '" + sqlLiteral(columnName) + "' "
                + "ORDER BY target_table.relname, target_att.attname";
        try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                ResultSet resultSet = statement.executeQuery(query)) {
            while (resultSet.next()) {
                targets.add(new ForeignKeyTarget(resultSet.getString("target_table"),
                        resultSet.getString("target_column")));
            }
        } catch (SQLException e) {
            throw new QueryGenerationException("Unable to query foreign-key targets: " + e.getMessage());
        }
        return targets;
    }

    private PostgreSQLTable getRandomTableWithConstraint(boolean validatableOnly) {
        List<String> tableNames = querySingleColumn(
                "SELECT DISTINCT c.relname FROM pg_class c "
                        + "JOIN pg_namespace n ON n.oid = c.relnamespace "
                        + "JOIN pg_constraint con ON con.conrelid = c.oid "
                        + "WHERE n.nspname = 'public' "
                        + "AND c.relkind IN ('r', 'p') "
                        + (validatableOnly ? "AND con.contype IN ('c', 'f') " : "")
                        + "ORDER BY c.relname",
                "Unable to query constrained tables.");
        List<PostgreSQLTable> candidates = ((PostgreSQLSchema) globalState.getSchema()).getDatabaseTablesWithoutViews()
                .stream()
                .filter(table -> tableNames.contains(table.getName()))
                .collect(Collectors.toList());
        if (candidates.isEmpty()) {
            throw new QueryGenerationException("There are no tables with compatible constraints.");
        }
        return Randomly.fromList(candidates);
    }

    private List<String> getTableConstraints(String tableName, boolean validatableOnly) {
        return querySingleColumn(
                "SELECT quote_ident(con.conname) FROM pg_constraint con "
                        + "JOIN pg_class c ON c.oid = con.conrelid "
                        + "JOIN pg_namespace n ON n.oid = c.relnamespace "
                        + "WHERE n.nspname = 'public' "
                        + "AND c.relname = '" + sqlLiteral(tableName) + "' "
                        + (validatableOnly ? "AND con.contype IN ('c', 'f') " : "")
                        + "ORDER BY con.conname",
                "Unable to query table constraints.");
    }

    private List<String> querySingleColumn(String query, String errorMessage) {
        List<String> values = new ArrayList<>();
        try (Statement statement = ((SQLGlobalState) globalState).getConnection().createStatement();
                ResultSet resultSet = statement.executeQuery(query)) {
            while (resultSet.next()) {
                values.add(resultSet.getString(1));
            }
        } catch (SQLException e) {
            throw new QueryGenerationException(errorMessage + " " + e.getMessage());
        }
        return values;
    }

    private void requireTablespaceGenerationEnabled() {
        if (!(globalState.getDbmsSpecificOptions() instanceof PostgreSQLOptions)
                || !((PostgreSQLOptions) globalState.getDbmsSpecificOptions()).allowTablespaces) {
            throw new QueryGenerationException("Tablespace generation is disabled.");
        }
    }

    private static String quoteIdentifier(String identifier) {
        return "\"" + identifier.replace("\"", "\"\"") + "\"";
    }

    private static String sqlLiteral(String value) {
        return value.replace("'", "''");
    }

    private record ForeignKeyTarget(String tableName, String columnName) {
    }

    private record ForeignKeyValue(boolean applies, String value) {
        static ForeignKeyValue notForeignKey() {
            return new ForeignKeyValue(false, null);
        }

        static ForeignKeyValue noAvailableValue() {
            return new ForeignKeyValue(true, null);
        }

        static ForeignKeyValue of(String value) {
            return new ForeignKeyValue(true, value);
        }
    }

}
