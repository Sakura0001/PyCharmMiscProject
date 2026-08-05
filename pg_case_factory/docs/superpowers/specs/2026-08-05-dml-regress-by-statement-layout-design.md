# DML Regress 按语句用途分类设计

**日期：** 2026-08-05

**状态：** 已批准，待实施

**来源包：** `artifacts/regress/dml-statement-factor-loop-v2`

**目标目录：** `artifacts/regress/dml-statement-factor-loop-v2-by-statement`

## 1. 目标

在不改写现有 v2 静态输入包的前提下，生成一个面向人工浏览和分语句执行的派生 regress
目录。542 个 SQL 文件按主语句用途分别进入 `call`、`delete`、`insert`、`merge`、
`select`、`update`、`values` 七个目录。每个目录具有独立连续编号、独立对象名前缀、
独立 schedule，并能单独通过 regress SQL 样式校验。

本设计只改变派生文件的布局和标识，不改变测试 SQL 的覆盖语义、执行顺序、fixture、目标
语句、验证语句或清理逻辑。

## 2. 范围与边界

### 2.1 纳入范围

- 使用 v2 `mapping.json`、`bundles/*.json` 和 `sql/*.sql` 作为唯一分类输入。
- 每个源 SQL 必须且只能归属于一个 `statement_key`。
- 生成实际 SQL 文件，不使用符号链接或硬链接。
- 发布新旧文件、bundle、subcase、对象前缀和 SHA-256 的完整映射。
- 为七个语句目录分别生成串行 schedule。
- 提供可重复执行的派生目录生成入口和静态验证入口。

### 2.2 不纳入范围

- 不修改或覆盖 `dml-statement-factor-loop-v1`、`dml-statement-factor-loop-v2`。
- 不重新展开 factor、syntax atom 或重新装箱。
- 不拆分一个 bundle 内的 subcase，也不把不同源 SQL 合并。
- 不生成 expected transcript，不连接 PostgreSQL，不声明运行态兼容性通过。
- 不把 success、expected failure、risk 或 external harness 继续拆成下一级目录。

## 3. 目录结构

```text
artifacts/regress/dml-statement-factor-loop-v2-by-statement/
├── README.md
├── manifest.json
├── call/
│   ├── CALL00001.sql
│   ├── ...
│   └── serial_schedule
├── delete/
│   ├── DELETE00001.sql
│   ├── ...
│   └── serial_schedule
├── insert/
│   ├── INSERT00001.sql
│   ├── ...
│   └── serial_schedule
├── merge/
│   ├── MERGE00001.sql
│   ├── ...
│   └── serial_schedule
├── select/
│   ├── SELECT00001.sql
│   ├── ...
│   └── serial_schedule
├── update/
│   ├── UPDATE00001.sql
│   ├── ...
│   └── serial_schedule
└── values/
    ├── VALUES00001.sql
    ├── ...
    └── serial_schedule
```

预期文件数固定为：

| 目录 | SQL 文件数 |
|---|---:|
| `call` | 39 |
| `delete` | 80 |
| `insert` | 88 |
| `merge` | 90 |
| `select` | 119 |
| `update` | 83 |
| `values` | 43 |
| **合计** | **542** |

## 4. 稳定编号与对象命名

每个语句目录按源 SQL 文件名的全局编号升序排列，再从 `00001` 独立连续编号。目标文件名和
对象前缀的关系如下：

| 语句 | 文件名格式 | SQL 对象前缀 |
|---|---|---|
| CALL | `CALL00001.sql` | `call_00001_` |
| DELETE | `DELETE00001.sql` | `delete_00001_` |
| INSERT | `INSERT00001.sql` | `insert_00001_` |
| MERGE | `MERGE00001.sql` | `merge_00001_` |
| SELECT | `SELECT00001.sql` | `select_00001_` |
| UPDATE | `UPDATE00001.sql` | `update_00001_` |
| VALUES | `VALUES00001.sql` | `values_00001_` |

转换时只进行两类身份替换：

1. 把源文件对象前缀，例如 `pcf_00176_`，统一替换为目标对象前缀。
2. 把源 subcase 前缀，例如 `PCF00176-SC`，替换为目标文件 stem 对应的前缀。

atom id、source bundle id、subcase 顺序、SQL 语义和注释中的 outcome 保持不变。生成器必须
检查所有目标 PostgreSQL 标识符不超过 63 字节，并拒绝任何文件名、对象名或 subcase id
冲突。

## 5. 分类与数据流

派生流程固定如下：

1. 对来源 v2 执行既有 package validation，要求 `passed=true` 且 `issue_count=0`。
2. 读取 `mapping.json`，按 `sql_filename` 聚合所有 mapping entry。
3. 要求同一源文件的所有 entry 具有同一个 `statement_key`，否则失败。
4. 按固定语句顺序和源文件名升序建立新编号。
5. 读取源 SQL，核对源 SHA-256 和 bundle 声明的文件绑定。
6. 替换文件身份、对象前缀和 subcase 前缀，计算目标 SHA-256。
7. 写入七个语句目录及其 `serial_schedule`。
8. 写入根 `manifest.json` 和使用说明。
9. 在同级临时目录完整生成并验证后，以原子发布方式创建最终目录；已有目标目录时拒绝
   覆盖。

## 6. Manifest 合同

`manifest.json` 至少包含：

- schema version、artifact kind、source package 相对路径；
- source `package.json` SHA-256 和来源 runtime 状态；
- 总 SQL 数、总 subcase 数和逐语句 SQL 数；
- 固定 statement order；
- 每个文件的 source/target filename、statement、source bundle id；
- source/target object prefix；
- source/target SQL SHA-256；
- source/target subcase id 映射；
- schedule 路径和 SHA-256；
- `runtime_verification_status=not_run_static_sql_only`。

每个源 SQL 必须在 manifest 中恰好出现一次，每个目标 SQL 也必须恰好出现一次。

## 7. 失败保护

以下任一条件必须终止生成且不发布半成品：

- 来源 v2 validation 失败或来源文件哈希不匹配；
- source mapping 引用缺失 SQL、bundle 或 subcase；
- 一个源 SQL 对应零个或多个主语句；
- statement 不在固定七语句集合内；
- 源文件遗漏、重复分类或目标文件名冲突；
- 对象前缀替换次数为零，或替换后仍残留该文件的源对象前缀；
- subcase marker 数量或顺序发生变化；
- 目标标识符超过 PostgreSQL 63 字节限制；
- 目标目录已经存在。

临时目录失败时可以保留为诊断证据，但不会替换或污染正式目标目录。

## 8. 验收与测试

### 8.1 单元测试

- 分类结果严格为 `39/80/88/90/119/83/43`。
- 每个目录编号从 `00001` 开始连续且无重复。
- 542 个源 SQL 与 542 个目标 SQL 一一对应，无 missing、duplicate、unexpected。
- 每个目标 SQL 的对象前缀与文件名一致，且源对象前缀已消除。
- subcase 数量、atom id、outcome 和顺序在转换前后相等。
- 来源篡改、混合 statement、重复映射、已有目标目录和残留旧前缀均能 fail closed。
- schedule 与对应目录 SQL stem 精确相等。

### 8.2 静态验收

- 七个目录分别运行 `validate_regress_sql_style.py`，使用各自大写 statement 前缀，全部
  PASS。
- 对派生目录运行专用 manifest validator，要求 issue count 为 0。
- 使用相同来源和参数独立生成第二份派生目录，递归字节比较无差异。
- 运行相关单元测试和项目完整测试。

### 8.3 运行态边界

本轮不执行数据库。最终 README 和 manifest 必须继续明确
`not_run_static_sql_only`。只有在授权 PostgreSQL 18.4 环境中执行 SQL、生成 expected 并
完成两次确定性比较后，才能形成运行态兼容性结论。

## 9. 交付结果

实施完成后，用户可以直接按语句用途进入对应目录浏览或执行 SQL；同时可以通过
`manifest.json` 从任一分类文件追溯到原 v2 文件、bundle、subcase 和 atom。原 v2 继续作为
不可变覆盖证据，新的 by-statement 目录只作为可读、可分组执行的派生视图。
