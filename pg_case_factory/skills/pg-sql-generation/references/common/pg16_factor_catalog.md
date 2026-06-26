# 技能：PG16 Factor Catalog

## 作用

定义 PG16 SQL 用例生成时可复用的对象因子目录。目录使用稳定的 domain、factor group、factor 和 value key，为 statement reference 后续声明 `factor_catalog_mapping` 提供统一来源。

## 使用方式

- statement reference 通过 `factor_catalog_mapping.source_catalog` 指向本文件。
- `catalog_factor` 使用 `<domain>.<factor_group>.<factor>` 路径，例如 `database.options.owner`。
- `selected_values` 必须引用对应 factor 的 `values[].key`。
- 新增 statement 映射时，应优先复用本目录因子；确有语句特有语义时再使用 `statement_specific_override`。

## 结构化配置

```yaml
structured_config:
  kind: factor_catalog
  skill_name: pg16_factor_catalog
  version: pg16
  object_domains:
    database:
      key: database
      label: 数据库
      factor_groups:
        naming:
          key: naming
          label: 命名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 数据库名称形态
              default_tier: T3
              default_coverage_role: rotate_attach
              values:
                - key: valid_unquoted_lower
                  label: 合法未引用小写名称
                  expected_status: success
                - key: valid_unquoted_mixed_case
                  label: 合法未引用混合大小写名称
                  expected_status: success
                - key: valid_quoted_upper
                  label: 合法引用大写名称
                  expected_status: success
                - key: quoted_reserved_keyword
                  label: 引用保留关键字
                  expected_status: success
                - key: reserved_keyword_unquoted
                  label: 未引用保留关键字
                  expected_status: failure
                - key: invalid_special_char_unquoted
                  label: 未引用特殊字符
                  expected_status: failure
                - key: invalid_space_unquoted
                  label: 未引用空格
                  expected_status: failure
                - key: max_length_63_bytes
                  label: 63 字节边界名称
                  expected_status: success
                - key: over_length_64_bytes
                  label: 64 字节超长名称
                  expected_status: failure
                - key: pg_prefix_non_superuser
                  label: 非超级用户使用 pg_ 前缀
                  expected_status: failure
        options:
          key: options
          label: 选项因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            owner:
              key: owner
              label: 所有者选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted
                  label: 省略所有者
                  expected_status: success
                - key: valid_current_user
                  label: 当前用户作为所有者
                  expected_status: success
                - key: valid_other_role
                  label: 可切换的其他角色作为所有者
                  expected_status: success
                - key: nonexistent_user
                  label: 不存在的用户
                  expected_status: failure
                - key: no_set_role_privilege
                  label: 无 SET ROLE 权限
                  expected_status: failure
            template:
              key: template
              label: 模板数据库选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted_default_template1
                  label: 省略并使用 template1
                  expected_status: success
                - key: template0
                  label: 使用 template0
                  expected_status: success
                - key: custom_template
                  label: 使用自定义模板
                  expected_status: success
                - key: nonexistent_template
                  label: 不存在的模板
                  expected_status: failure
                - key: template_has_connections
                  label: 模板存在活动连接
                  expected_status: failure
            encoding:
              key: encoding
              label: 编码选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted_client_default
                  label: 省略并使用客户端默认编码
                  expected_status: success
                - key: utf8
                  label: UTF8 编码
                  expected_status: success
                - key: latin1
                  label: LATIN1 编码
                  expected_status: success
                - key: sql_ascii
                  label: SQL_ASCII 编码
                  expected_status: success
                - key: invalid_encoding
                  label: 非法编码名称
                  expected_status: failure
            locale:
              key: locale
              label: 区域设置选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted
                  label: 省略区域设置
                  expected_status: success
                - key: c_locale
                  label: C 区域设置
                  expected_status: success
                - key: posix_locale
                  label: POSIX 区域设置
                  expected_status: success
                - key: valid_system_locale
                  label: 有效系统区域设置
                  expected_status: success
                - key: nonexistent_locale
                  label: 不存在的区域设置
                  expected_status: failure
                - key: encoding_locale_mismatch
                  label: 编码与区域设置不兼容
                  expected_status: failure
            strategy:
              key: strategy
              label: 创建策略选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted_default_wal_log
                  label: 省略并使用 WAL_LOG
                  expected_status: success
                - key: wal_log
                  label: WAL_LOG 策略
                  expected_status: success
                - key: file_copy
                  label: FILE_COPY 策略
                  expected_status: success
                - key: invalid_strategy
                  label: 非法策略
                  expected_status: failure
            allow_connections:
              key: allow_connections
              label: 允许连接选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: "true"
                  label: 允许连接
                  expected_status: success
                - key: "false"
                  label: 禁止连接
                  expected_status: success
            connection_limit:
              key: connection_limit
              label: 连接数限制
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: positive
                  label: 正数限制
                  expected_status: success
                - key: unlimited_negative_one
                  label: -1 表示不限
                  expected_status: success
                - key: zero
                  label: 零连接限制
                  expected_status: success
            is_template:
              key: is_template
              label: 模板标记选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: "true"
                  label: 标记为模板
                  expected_status: success
                - key: "false"
                  label: 标记为非模板
                  expected_status: success
            tablespace:
              key: tablespace
              label: 表空间选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted_default
                  label: 省略并使用默认表空间
                  expected_status: success
                - key: pg_default
                  label: 使用 pg_default
                  expected_status: success
                - key: valid_tablespace
                  label: 使用有效表空间
                  expected_status: success
                - key: nonexistent_tablespace
                  label: 不存在的表空间
                  expected_status: failure
                - key: no_create_privilege
                  label: 无表空间 CREATE 权限
                  expected_status: failure
            config_parameter:
              key: config_parameter
              label: 数据库级配置参数
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: common_parameter
                  label: 普通配置参数
                  expected_status: success
                - key: superuser_only_parameter
                  label: 仅超级用户配置参数
                  expected_status: failure
                - key: reset_all
                  label: 重置全部配置
                  expected_status: success
        operation:
          key: operation
          label: 操作修饰因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            if_exists:
              key: if_exists
              label: IF EXISTS 选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted
                  label: 省略 IF EXISTS
                  expected_status: success
                - key: specified
                  label: 指定 IF EXISTS
                  expected_status: success
            force:
              key: force
              label: FORCE 选项
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: omitted
                  label: 省略 FORCE
                  expected_status: success
                - key: specified
                  label: 指定 FORCE
                  expected_status: success
        environment:
          key: environment
          label: 环境前置因子
          default_tier: T4
          default_coverage_role: rotate_attach
          factors:
            privilege_level:
              key: privilege_level
              label: 执行权限层级
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: superuser
                  label: 超级用户
                  expected_status: success
                - key: createdb_role
                  label: 具备 CREATEDB 的角色
                  expected_status: success
                - key: database_owner
                  label: 数据库所有者
                  expected_status: success
                - key: non_owner
                  label: 非所有者
                  expected_status: failure
            template_existence:
              key: template_existence
              label: 模板存在状态
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: exists_no_connections
                  label: 模板存在且无连接
                  expected_status: success
                - key: exists_has_connections
                  label: 模板存在且有连接
                  expected_status: failure
                - key: not_exists
                  label: 模板不存在
                  expected_status: failure
            encoding_locale_compatibility:
              key: encoding_locale_compatibility
              label: 编码与区域设置兼容性
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: compatible
                  label: 编码与区域设置兼容
                  expected_status: success
                - key: incompatible
                  label: 编码与区域设置不兼容
                  expected_status: failure
                - key: template_mismatch
                  label: 与模板编码或区域设置不匹配
                  expected_status: failure
            role_set_role_ability:
              key: role_set_role_ability
              label: SET ROLE 能力
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: can_set_role
                  label: 可以切换到目标角色
                  expected_status: success
                - key: cannot_set_role
                  label: 不能切换到目标角色
                  expected_status: failure
            tablespace_existence:
              key: tablespace_existence
              label: 表空间存在状态
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: exists
                  label: 表空间存在
                  expected_status: success
                - key: not_exists
                  label: 表空间不存在
                  expected_status: failure
            connection_state:
              key: connection_state
              label: 目标数据库连接状态
              default_tier: T4
              default_coverage_role: rotate_attach
              values:
                - key: no_other_connections
                  label: 无其他连接
                  expected_status: success
                - key: has_other_connections
                  label: 存在其他连接
                  expected_status: failure
                - key: connected_to_target_database
                  label: 当前连接到目标数据库
                  expected_status: failure
        boundary:
          key: boundary
          label: 异常与边界因子
          default_tier: T5
          default_coverage_role: rotate_attach
          factors:
            duplicate_name:
              key: duplicate_name
              label: 重名冲突
              default_tier: T5
              default_coverage_role: rotate_attach
              values:
                - key: no_conflict
                  label: 无重名冲突
                  expected_status: success
                - key: name_already_exists
                  label: 名称已存在
                  expected_status: failure
            privilege_denied:
              key: privilege_denied
              label: 权限不足场景
              default_tier: T5
              default_coverage_role: rotate_attach
              values:
                - key: has_privilege
                  label: 具备所需权限
                  expected_status: success
                - key: missing_createdb
                  label: 缺少 CREATEDB 权限
                  expected_status: failure
                - key: non_owner_operation
                  label: 非所有者执行所有者操作
                  expected_status: failure
            inside_transaction:
              key: inside_transaction
              label: 事务块位置
              default_tier: T5
              default_coverage_role: rotate_attach
              values:
                - key: outside_transaction
                  label: 位于事务块外
                  expected_status: success
                - key: inside_transaction
                  label: 位于事务块内
                  expected_status: failure
            active_connections:
              key: active_connections
              label: 活动连接状态
              default_tier: T5
              default_coverage_role: rotate_attach
              values:
                - key: no_active_connections
                  label: 无活动连接
                  expected_status: success
                - key: has_terminable_connections
                  label: 存在可终止连接
                  expected_status: success
                - key: has_unterminable_connections
                  label: 存在不可终止连接
                  expected_status: failure
        validation:
          key: validation
          label: 验证与清理因子
          default_tier: T6
          default_coverage_role: audit_only
          factors:
            catalog_check:
              key: catalog_check
              label: 系统目录验证
              default_tier: T6
              default_coverage_role: audit_only
              values:
                - key: pg_database_presence
                  label: 验证 pg_database 中存在
                  expected_status: success
                - key: pg_database_absence
                  label: 验证 pg_database 中不存在
                  expected_status: success
                - key: error_assertion
                  label: 验证错误信息
                  expected_status: failure
            cleanup:
              key: cleanup
              label: 清理动作
              default_tier: T6
              default_coverage_role: audit_only
              values:
                - key: drop_database
                  label: 常规删除数据库
                  expected_status: success
                - key: force_drop_database
                  label: 强制删除数据库
                  expected_status: success
                - key: reset_config_parameter
                  label: 重置配置参数
                  expected_status: success
    domain:
      key: domain
      label: 域类型
      factor_groups:
        naming:
          key: naming
          label: 命名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 域名称形态
              default_tier: T3
              default_coverage_role: rotate_attach
              values:
                - key: valid_domain_name
                  label: 合法域名称
                  expected_status: success
        definition:
          key: definition
          label: 定义因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            base_type:
              key: base_type
              label: 基础类型
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: builtin_type
                  label: 内置基础类型
                  expected_status: success
    schema:
      key: schema
      label: 模式
      factor_groups:
        naming:
          key: naming
          label: 命名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 模式名称形态
              default_tier: T3
              default_coverage_role: rotate_attach
              values:
                - key: valid_schema_name
                  label: 合法模式名称
                  expected_status: success
        ownership:
          key: ownership
          label: 所有权因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            owner:
              key: owner
              label: 模式所有者
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: current_user
                  label: 当前用户所有
                  expected_status: success
    role_user_group:
      key: role_user_group
      label: 角色、用户与组
      factor_groups:
        identity:
          key: identity
          label: 身份因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            role_kind:
              key: role_kind
              label: 角色类型
              default_tier: T3
              default_coverage_role: rotate_attach
              values:
                - key: login_role
                  label: 可登录角色
                  expected_status: success
        privileges:
          key: privileges
          label: 权限因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            privilege_set:
              key: privilege_set
              label: 角色权限集合
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: no_special_privileges
                  label: 无特殊权限
                  expected_status: success
    tablespace:
      key: tablespace
      label: 表空间
      factor_groups:
        naming:
          key: naming
          label: 命名因子
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: 表空间名称形态
              default_tier: T3
              default_coverage_role: rotate_attach
              values:
                - key: valid_tablespace_name
                  label: 合法表空间名称
                  expected_status: success
        storage:
          key: storage
          label: 存储因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            location:
              key: location
              label: 表空间目录位置
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: empty_existing_directory
                  label: 已存在空目录
                  expected_status: success
    extension:
      key: extension
      label: 扩展
      factor_groups:
        installation:
          key: installation
          label: 安装因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            extension_name:
              key: extension_name
              label: 扩展名称
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: available_extension
                  label: 可用扩展
                  expected_status: success
    sequence:
      key: sequence
      label: 序列
      factor_groups:
        definition:
          key: definition
          label: 定义因子
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            data_type:
              key: data_type
              label: 序列数据类型
              default_tier: T2
              default_coverage_role: representative_or_main
              values:
                - key: bigint_default
                  label: 默认 bigint 序列
                  expected_status: success
```
