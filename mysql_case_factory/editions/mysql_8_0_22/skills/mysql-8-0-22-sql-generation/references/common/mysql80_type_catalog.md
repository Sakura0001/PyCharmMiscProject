# MySQL 8.0.22 Type Catalog

Initial type catalog for object templates and statement factor choices.

```yaml
structured_config:
  kind: type_catalog
  skill_name: mysql80_type_catalog
  version: "8.0.22"
  families:
    numeric:
      values:
        - tinyint
        - smallint
        - mediumint
        - int
        - bigint
        - decimal
        - float
        - double
        - bit
    string:
      values:
        - char
        - varchar
        - binary
        - varbinary
        - tinytext
        - text
        - mediumtext
        - longtext
        - enum
        - set
    temporal:
      values:
        - date
        - time
        - datetime
        - timestamp
        - year
    json:
      values:
        - json
    spatial:
      values:
        - geometry
        - point
        - linestring
        - polygon
    blob:
      values:
        - tinyblob
        - blob
        - mediumblob
        - longblob
```
