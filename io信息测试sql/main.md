# 技能：Generate SQL From Request

## 作用

根据输入的场景生成对应的sql用例，每个场景对应一个或多个用例，符合mysql8.0.41的语法，用例的写作规范参考common/style.md,sql的实现细节参考common/io.md.

## 主流程规则

- 读取用例的写作规范参考common/style.md,sql的实现细节参考common/io.md.
- 每个用例前提：需要先创建一张单行比较大的表，并插入至少10g数据，然后通过查询语句将表中所有的信息注入到bufferpool中，实际bufferpool大小为8g。
- 然后根据用例的场景生成对应的sql语句，保证每种数据类型大类都应该覆盖到，例如int，time，char这种大类别，不需要精确到小类。
- 然后根据用例的场景生成对应的sql语句，保证每种表类型都应该覆盖到，普通表，临时表，分区表，视图，外键表。
- 每个场景请使用gpt5.5的子agent来实现，并读取项目下的md文件，进行生成，保证上下文干净，对于多个相似场景，请使用一个python文件来进行生成。
- 场景sql生成后，每个sql需要进行验证，如果是同步读场景，需要通过查询buffer中的信息，观察数据是否和实际这个表存储的页面信息和字节数是否能对应上，是否有偏差，数值预计应该是多少，都应该在sql文件中进行体现。
- 如果是异步读场景，查询系统表观察是否执行前后是否触发了异步读，异步读字节数参数是否发生了变化，变化值是否符合预期。
- 每个用例在开始处要加上下面语句每行一条语句。
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 0.01;
SET GLOBAL log_slow_admin_statements = ON;
SET SESSION rds_log_slow_verbosity = 'io_info';
## 产物约束
- 每次运行前检查 `artifacts/`目录是否存在，并进行用例的追加生成，原有用例不用读取。
- 只允许保留一类目录：
  - `artifacts/generated_sql/`

