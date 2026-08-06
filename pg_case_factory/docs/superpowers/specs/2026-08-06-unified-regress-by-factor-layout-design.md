# 统一 Regress 因子目录映射设计

**日期：** 2026-08-06

**状态：** 已批准，待实施

**目标目录：** `artifacts/regress/by-factor`

## 1. 目标

把已经生成并验证的 DML、Cursor、DCL regress SQL 发布为一个面向人工浏览和分语句执行的派生目录。目标目录严格镜像 `skills/pg-sql-generation/references/combinations/` 下的因子分类路径，使测试 SQL 的物理位置可以直接反查其因子矩阵：

```text
artifacts/regress/by-factor/
├── dml/
│   ├── query/select/
│   ├── query/values/
│   ├── routine/call/
│   └── table/{delete,insert,merge,update}/
├── cursor/cursor/{close,declare,fetch,move}/
└── dcl/privilege/{grant,revoke}/
```

本目录是派生执行视图。原始批次继续作为覆盖、shard、mapping 和审计证据，不被移动、删除或改写。

## 2. 来源与固定规模

唯一允许的来源包为：

- DML：`artifacts/regress/dml-statement-factor-loop-v2`
- Cursor：`artifacts/regress/cursor-factor-full-v1`
- DCL：`artifacts/regress/dcl-factor-full-v1`

派生前必须先验证三个来源包。预期 SQL 文件数为：

| 因子路径 | SQL 数 |
|---|---:|
| `dml/query/select` | 119 |
| `dml/query/values` | 43 |
| `dml/routine/call` | 39 |
| `dml/table/delete` | 80 |
| `dml/table/insert` | 88 |
| `dml/table/merge` | 90 |
| `dml/table/update` | 83 |
| `cursor/cursor/close` | 213 |
| `cursor/cursor/declare` | 213 |
| `cursor/cursor/fetch` | 213 |
| `cursor/cursor/move` | 213 |
| `dcl/privilege/grant` | 6,933 |
| `dcl/privilege/revoke` | 6,933 |
| **合计** | **15,260** |

实际生成时必须从来源 mapping 重新计算这些数量，并与固定预期比较；不允许靠复制、补位或抽样达到数量。

## 3. 目录和文件合同

每个语句叶子目录直接包含 SQL 和独立串行 schedule：

```text
artifacts/regress/by-factor/dcl/privilege/grant/
├── GRANT00001.sql
├── GRANT00002.sql
├── ...
└── serial_schedule
```

编号在每个叶子目录内从 `00001` 独立连续增长，顺序由来源 SQL 文件名的全局编号升序决定。文件名和对象前缀保持强绑定：

| 文件示例 | 对象前缀 |
|---|---|
| `SELECT00001.sql` | `select_00001_` |
| `FETCH00001.sql` | `fetch_00001_` |
| `GRANT00001.sql` | `grant_00001_` |

所有叶子目录统一采用五位编号，避免同一目录规模变化时改变编号宽度。

## 4. 分类规则

分类只读取结构化证据，不通过 SQL 文本猜测：

- DML：从 v2 `mapping.json` 和 bundle/subcase 绑定取得唯一 `statement_key`。
- Cursor：从 regress mapping 的 `test_point_id` 取得 `close`、`declare`、`fetch` 或 `move`。
- DCL：普通笛卡尔积和逐因子值义务从 `test_point_id` 取得语句；列类型和 MAINTAIN 义务从 assignment 的 `dcl_statement` 取得 `grant` 或 `revoke`。

每个来源 SQL 必须且只能归入一个叶子目录。分类结果再与对应组合矩阵路径核对，最终路径必须等于矩阵的 `category/domain/statement` 路径。

## 5. SQL 身份转换

转换只改变派生文件身份，不改变测试语义：

1. 将源文件对象前缀整体替换为目标语句前缀。
2. DML 同步替换文件内 subcase 标识前缀；atom id、outcome、subcase 顺序保持不变。
3. Cursor/DCL 保留因子注释、目标 SQL、验证 SQL、清理顺序和预期结果分类。
4. 不重新展开因子、不重新装箱、不改变 success、expected failure、justified N/A 统计。
5. 替换后不得残留源对象前缀，所有 PostgreSQL 标识符不得超过 63 字节。

转换前后分别计算 SHA-256，并在 manifest 中保存一一映射。

## 6. Manifest 与追溯

根目录生成 `README.md` 和 `manifest.json`。Manifest 至少记录：

- schema version、artifact kind、生成器版本和静态运行状态；
- 三个来源包路径、来源 mapping/package 哈希及验证结果；
- 因子根路径、13 个叶子目录及逐目录数量；
- 每个源文件和目标文件的相对路径、statement、来源义务或 bundle；
- source/target object prefix 和 source/target SQL SHA-256；
- DML subcase id 映射；
- 每个 schedule 的相对路径和 SHA-256；
- `runtime_verification_status=not_run_static_sql_only`。

任一目标 SQL 都必须能从 manifest 反查到原始批次文件和正式覆盖证据。

## 7. 生成与失败保护

派生生成使用 Python 脚本，并遵循以下顺序：

1. 验证三个来源包完整且哈希匹配。
2. 读取结构化 mapping，计算 15,260 个唯一分类结果。
3. 在同级临时目录生成完整树、SQL、schedule、README 和 manifest。
4. 验证数量守恒、编号连续、映射双射、对象前缀、SQL 规范和 schedule。
5. 用相同输入再生成一份临时树，递归比较字节完全一致。
6. 所有检查通过后原子发布为 `artifacts/regress/by-factor`。

出现以下任一情况必须失败且不发布半成品：来源验证失败、来源哈希不匹配、语句分类不唯一、文件遗漏或重复、目标碰撞、旧前缀残留、subcase 守恒失败、目录已存在或静态规范检查失败。

## 8. 验收条件

只有同时满足以下条件才算完成：

1. 13 个叶子目录与 13 个因子矩阵路径逐一对应。
2. 15,260 个来源 SQL 与 15,260 个目标 SQL 一一对应，无 missing、duplicate、unexpected。
3. 每个叶子目录编号从 `00001` 连续，文件名和对象前缀一致。
4. 每个 `serial_schedule` 精确列出本目录全部 SQL stem。
5. DML bundle/subcase/atom 守恒；Cursor/DCL obligation、outcome 和因子赋值守恒。
6. 13 个目录分别通过 regress SQL 风格检查。
7. 专用 manifest validator、相关单元测试和项目完整测试通过。
8. 两次独立派生目录递归字节一致。

本轮仍是 SQL-only 静态派生，不连接 PostgreSQL、不生成 expected 文件，也不声明数据库运行态通过。
