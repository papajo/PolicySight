-- TimescaleDB Initialization for PolicySight
-- Runs after schema.sql. Enables extension and creates hypertables.
-- The timescale/timescaledb-ha image pre-loads timescaledb, so CREATE EXTENSION is a no-op.

-- Enable TimescaleDB extension (already loaded in HA image, safe to re-run)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Convert time-series tables to hypertables
-- TimescaleDB requires the partitioning column to be part of any unique index.

-- Policy snapshots: track SLIP parsing history over time
SELECT create_hypertable('policy_snapshots', 'created_at',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- Claims: time-series of filed claims
SELECT create_hypertable('claims', 'filed_date',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- Rate snapshots: historical rate tracking per carrier
SELECT create_hypertable('rate_snapshots', 'date',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- Enable compression on hypertables (columnstore)
-- This achieves 90%+ storage reduction on historical data

ALTER TABLE policy_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'policy_id',
    timescaledb.compress_orderby = 'created_at DESC'
);

ALTER TABLE claims SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id',
    timescaledb.compress_orderby = 'filed_date DESC'
);

ALTER TABLE rate_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'carrier_id',
    timescaledb.compress_orderby = 'date DESC'
);

-- Add compression policy: auto-compress chunks older than 7 days
SELECT add_compression_policy('policy_snapshots', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('claims', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('rate_snapshots', INTERVAL '7 days', if_not_exists => TRUE);

-- Continuous Aggregates: pre-computed dashboards for management

-- Daily claims summary (for Claims Advocate dashboard)
CREATE MATERIALIZED VIEW claims_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', filed_date) AS day,
    carrier_id,
    COUNT(*) AS total_claims,
    COUNT(*) FILTER (WHERE status = 'approved') AS approved,
    COUNT(*) FILTER (WHERE status = 'denied') AS denied,
    COUNT(*) FILTER (WHERE status = 'filed') AS pending
FROM claims
GROUP BY day, carrier_id
WITH NO DATA;

-- Refresh policy for claims_daily_summary
SELECT add_continuous_aggregate_policy('claims_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Daily rate trajectory (for Rate Trajectory Bot)
CREATE MATERIALIZED VIEW rate_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', date) AS day,
    carrier_id,
    AVG(rate) AS avg_rate,
    MIN(rate) AS min_rate,
    MAX(rate) AS max_rate,
    COUNT(*) AS snapshot_count
FROM rate_snapshots
GROUP BY day, carrier_id
WITH NO DATA;

-- Refresh policy for rate_daily_summary
SELECT add_continuous_aggregate_policy('rate_daily_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Retention policy: auto-drop raw policy_snapshots older than 2 years
SELECT add_retention_policy('policy_snapshots', INTERVAL '2 years', if_not_exists => TRUE);

-- Retention policy: auto-drop raw claims older than 5 years (regulatory hold)
SELECT add_retention_policy('claims', INTERVAL '5 years', if_not_exists => TRUE);

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialized successfully for PolicySight';
    RAISE NOTICE 'Hypertables: policy_snapshots, claims, rate_snapshots';
    RAISE NOTICE 'Continuous Aggregates: claims_daily_summary, rate_daily_summary';
    RAISE NOTICE 'Compression: enabled on all hypertables (7-day threshold)';
    RAISE NOTICE 'Retention: policy_snapshots=2yr, claims=5yr';
END $$;
