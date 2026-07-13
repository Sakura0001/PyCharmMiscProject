# Output Script Style

Generated SQL scripts should be executable by the MySQL client and readable in
review.

```yaml
structured_config:
  skill_name: output_script_style
  statement: common
  script_sections:
    - header
    - pre_cleanup
    - setup
    - target_statement
    - verification
    - cleanup
  delimiter_required_for_routines: true
  use_database_required: false
  comments: sql_dash_dash
```
