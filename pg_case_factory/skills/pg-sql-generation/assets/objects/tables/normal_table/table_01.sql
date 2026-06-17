DROP TABLE IF EXISTS tbl_base_index_1;
CREATE TABLE tbl_base_index_1
(
    id_col                      INT4 GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    smallint_col            SMALLINT,
    integer_col             INTEGER,
    bigint_col              BIGINT,
    numeric_col             NUMERIC(16,4),
    real_col                REAL,
    double_col              DOUBLE PRECISION,
    money_col               MONEY,
    char_col                CHAR(20),
    character_col           CHARACTER(20),
    varchar_col             VARCHAR(100),
    character_varying_col   CHARACTER VARYING(100),
    text_col                TEXT,
    bpchar_col              BPCHAR(20),
    boolean_col             BOOLEAN,
    bytea_col               BYTEA,
    date_col                DATE,
    time_col                TIME,
    timetz_col              TIMETZ,
    timestamp_col           TIMESTAMP,
    timestamptz_col         TIMESTAMPTZ,
    interval_col            INTERVAL,
    inet_col                INET,
    cidr_col                CIDR,
    macaddr_col             MACADDR,
    macaddr8_col            MACADDR8,
    bit_col                 BIT(8),
    varbit_col              VARBIT(32),
    tsvector_col            TSVECTOR,
    tsquery_col             TSQUERY,
    json_col                JSON,
    jsonb_col               JSONB,
    uuid_col                UUID,
    xml_col                 XML,
    point_col               POINT,
    line_col                LINE,
    lseg_col                LSEG,
    box_col                 BOX,
    path_col                PATH,
    polygon_col             POLYGON,
    circle_col              CIRCLE,
    int4range_col           INT4RANGE,
    int8range_col           INT8RANGE,
    numrange_col            NUMRANGE,
    tsrange_col             TSRANGE,
    tstzrange_col           TSTZRANGE,
    daterange_col           DATERANGE,
    int_array_col           INT4[],
    text_array_col          TEXT[],
    varchar_array_col       VARCHAR[],
    pg_lsn_col              PG_LSN,
    oid_col                 OID,
    tid_col                 TID,
    xid_col                 XID,
    xid8_col                XID8,
    cid_col                 CID,
    name_col                NAME
);

DROP PROCEDURE IF EXISTS insert_10000_uniform_data(text);

CREATE OR REPLACE PROCEDURE insert_10000_uniform_data(p_table_name text)
LANGUAGE plpgsql
AS $$
DECLARE
    i INT;
    v_sql text;
BEGIN
    v_sql := format(
        'INSERT INTO %I (
            smallint_col, integer_col, bigint_col, numeric_col, real_col, double_col, money_col,
            char_col, character_col, varchar_col, character_varying_col, text_col, bpchar_col,
            boolean_col, bytea_col,
            date_col, time_col, timetz_col, timestamp_col, timestamptz_col, interval_col,
            inet_col, cidr_col, macaddr_col, macaddr8_col,
            bit_col, varbit_col,
            tsvector_col, tsquery_col,
            json_col, jsonb_col,
            uuid_col, xml_col,
            point_col, line_col, lseg_col, box_col, path_col, polygon_col, circle_col,
            int4range_col, int8range_col, numrange_col, tsrange_col, tstzrange_col, daterange_col,
            int_array_col, text_array_col, varchar_array_col,
            pg_lsn_col, oid_col, tid_col, xid_col, xid8_col, cid_col, name_col
        )
        VALUES (
            ($1 %% 32767)::smallint, $1, $1::bigint,
            ($1*1.2345)::numeric(16,4), ($1*0.01234)::real, ($1*0.056789)::double precision, ($1*0.5)::money,

            ''CHAR_''||lpad($1::text,6,''0''),
            ''CHARACTER_''||lpad(($1 %% 1000)::text,6,''0''),
            ''VARCHAR_DATA_''||$1,
            ''CHAR_VARYING_''||$1,
            ''FULL_TEXT_''||$1,
            ''BPCHAR_''||lpad(($1 %% 1000)::text,6,''0''),

            $1 %% 2 = 0,
            (''bin_''||$1)::bytea,

            current_date - ($1 %% 3650),
            ''09:00:00''::time + ($1 %% 86400)*interval ''1 second'',
            ''09:00:00+08''::timetz + ($1 %% 86400)*interval ''1 second'',
            localtimestamp - $1*interval ''1 day'',
            now() - $1*interval ''1 day'',
            ($1 %% 100) * interval ''1 minute'',

            (''192.168.0.''||($1 %% 250))::inet,
            (''10.0.''||($1 %% 16)||''.0/24'')::cidr,
            (''00:11:22:33:44:''||lpad(to_hex($1 %% 255),2,''0''))::macaddr,
            (''00:11:22:33:44:55:66:''||lpad(to_hex($1 %% 255),2,''0''))::macaddr8,

            ($1 %% 256)::bit(8),
            ($1 %% 65535)::bit(32)::varbit(32),

            to_tsvector(''english'', ''row ''||$1),
            plainto_tsquery(''english'', ''demo''),

            json_build_object(''id'', $1),
            jsonb_build_object(''id'', $1, ''active'', $1 %% 2 = 0),

            uuid_in(md5($1::text)::cstring),
            NULL,

            point($1 %% 100, $1 %% 100),
            line(''(0,0),(100,100)''),
            lseg(''(0,0),(''||($1 %% 100)||'',''||($1 %% 100)||'')''),
            box(''(0,0),(''||($1 %% 50)||'',''||($1 %% 50)||'')''),
            path(''(0,0),(''||($1 %% 40)||'',0),(''||($1 %% 40)||'',''||($1 %% 40)||'')''),
            polygon(''(0,0),(''||($1 %% 40)||'',0),(''||($1 %% 40)||'',''||($1 %% 40)||''), (0,''||($1 %% 40)||'')''),
            circle(''(''||($1 %% 100)||'',''||($1 %% 100)||''),''||($1 %% 30)),

            int4range($1, $1+100),
            int8range($1, $1+100),
            numrange($1, $1+100),
            tsrange(localtimestamp - $1*interval ''1 day'', localtimestamp - $1*interval ''1 day'' + interval ''1 hour''),
            tstzrange(now() - $1*interval ''1 day'', now() - $1*interval ''1 day'' + interval ''1 hour''),
            daterange(current_date - $1, current_date - $1 + 30),

            array[$1 %% 5, $1 %% 10, $1 %% 15],
            array[''A''||($1 %% 4), ''B''||($1 %% 6)],
            array[''X'',''Y'',''Z'']::varchar[],

            (''0/''||lpad(to_hex($1),8,''0''))::pg_lsn,
            ($1 + 10000)::oid,
            (''(0,''||$1||'')'')::tid,
            (''1000'')::xid,
            (''1000000'')::xid8,
            (''100'')::cid,
            (''name_''||$1)::name
        )',
        p_table_name
    );

    FOR i IN 1..20000 LOOP
        EXECUTE v_sql USING i;
    END LOOP;
END;
$$;

CALL insert_10000_uniform_data('tbl_base_index_1');




CREATE INDEX idx_integer_col ON tbl_base_index_1 USING btree (integer_col);
CREATE INDEX idx_timestamp_col ON tbl_base_index_1 USING btree (timestamp_col);
CREATE INDEX idx_varchar_col ON tbl_base_index_1 USING hash (varchar_col);
CREATE INDEX idx_point_col ON tbl_base_index_1 USING gist (point_col);
CREATE INDEX idx_box_col ON tbl_base_index_1 USING gist (box_col);
CREATE INDEX idx_tsvector_col ON tbl_base_index_1 USING gin (tsvector_col);
CREATE INDEX idx_jsonb_col ON tbl_base_index_1 USING gin (jsonb_col);
CREATE INDEX idx_int_array_col ON tbl_base_index_1 USING gin (int_array_col);
CREATE INDEX idx_id_brin ON tbl_base_index_1 USING brin (id_col);
CREATE INDEX idx_varchar_upper ON tbl_base_index_1 USING btree (upper(varchar_col));
CREATE INDEX idx_int_bool_mx ON tbl_base_index_1 USING btree (integer_col, boolean_col);
CREATE INDEX idx_order_by_index ON tbl_base_index_1 USING btree (uuid_col);
CREATE INDEX idx_money_btree ON tbl_base_index_1 USING btree (money_col);
CREATE INDEX idx_money_bool ON tbl_base_index_1 USING btree (money_col, boolean_col);
CREATE INDEX idx_comb_lsn_bool ON tbl_base_index_1 USING btree (pg_lsn_col, boolean_col);
CREATE INDEX idx_comb_text_bit_enum ON tbl_base_index_1 USING btree (tsvector_col, varbit_col, name_col);
CREATE INDEX idx_fulltext ON tbl_base_index_1 USING GIN (tsvector_col);
-- 1. 普通 B-tree 索引
CREATE INDEX idx_btree_integer ON tbl_base_index_1 USING btree (integer_col);
CREATE UNIQUE INDEX idx_btree_unique_uuid ON tbl_base_index_1 USING btree (uuid_col);
CREATE INDEX idx_btree_money_bool ON tbl_base_index_1 USING btree (money_col, boolean_col);
CREATE INDEX idx_hash_varchar ON tbl_base_index_1 USING hash (varchar_col);
CREATE INDEX idx_hash_text ON tbl_base_index_1 USING hash (text_col);
CREATE INDEX idx_gist_point ON tbl_base_index_1 USING gist (point_col);
CREATE INDEX idx_gist_box ON tbl_base_index_1 USING gist (box_col);
CREATE INDEX idx_spgist_inet ON tbl_base_index_1 USING spgist (inet_col);
CREATE INDEX idx_spgist_polygon ON tbl_base_index_1 USING spgist (polygon_col);
CREATE INDEX idx_gin_jsonb ON tbl_base_index_1 USING gin (jsonb_col);
CREATE INDEX idx_gin_int_array ON tbl_base_index_1 USING gin (int_array_col);
CREATE INDEX idx_gin_text_array ON tbl_base_index_1 USING gin (text_array_col);
CREATE INDEX idx_brin_id ON tbl_base_index_1 USING brin (id_col);
CREATE INDEX idx_brin_timestamp ON tbl_base_index_1 USING brin (timestamp_col);
CREATE INDEX idx_brin_date ON tbl_base_index_1 USING brin (date_col);
CREATE INDEX idx_geo_box ON tbl_base_index_1 USING gist (box_col);
CREATE INDEX idx_lsn_bool ON tbl_base_index_1 USING btree (pg_lsn_col, boolean_col);
CREATE INDEX idx_ts_bit_enum ON tbl_base_index_1 USING btree (tsvector_col, varbit_col);