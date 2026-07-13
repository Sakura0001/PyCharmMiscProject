# Write SQL Program

Generated Python programs belong in `artifacts/generated_programs/` and should
call the generic `mysql_case_factory` API:

```python
from mysql_case_factory import (
    build_bindings,
    build_name_context,
    compose_sql_script,
    discover_request_candidates,
    load_statement_skill,
    render_object_template,
    render_statement,
)
```

The generated program may choose a statement reference and object template, then
expand bindings according to `coverage_policy`. It must not invent factors that
are absent from the statement reference.
