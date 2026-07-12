-- object_key: table_02_simplified_types
-- aliases: normal table representative types, composite and enum table
-- object_kind: table
-- compatibility_target: postgresql-18.4
-- purpose: compact normal-table base object with representative scalar, enum, composite, array, range, and TOAST-capable columns
-- primary_object: tab_normal_representative

DROP TABLE IF EXISTS tab_normal_representative;
DROP TYPE IF EXISTS typ_normal_composite;
DROP TYPE IF EXISTS enum_normal_status;

CREATE TYPE typ_normal_composite AS
(
    id_col integer,
    varchar_col varchar(255),
    text_col text
);

CREATE TYPE enum_normal_status AS ENUM
(
    'init',
    'running',
    'success',
    'failed'
);

CREATE TABLE tab_normal_representative
(
    id_col                 integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    integer_col            integer,
    bigint_col             bigint,
    numeric_col            numeric(16, 4),
    double_col             double precision,
    varchar_col            varchar(100),
    text_col               text,
    bytea_col              bytea,
    boolean_col            boolean,
    date_col               date,
    timestamp_col          timestamp,
    timestamptz_col        timestamptz,
    interval_col           interval,
    inet_col               inet,
    bit_col                bit(8),
    tsvector_col           tsvector,
    json_col               json,
    jsonb_col              jsonb,
    uuid_col               uuid,
    point_col              point,
    int4range_col          int4range,
    int4multirange_col     int4multirange,
    int_array_col          integer[],
    text_array_col         text[],
    composite_type_col     typ_normal_composite,
    enum_col               enum_normal_status,
    composite_search_col   tsvector GENERATED ALWAYS AS
    (
        to_tsvector(
            'pg_catalog.english'::regconfig,
            coalesce((composite_type_col).varchar_col, '')
            || ' '
            || coalesce((composite_type_col).text_col, '')
        )
    ) STORED
);
