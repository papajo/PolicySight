-- PolicySight Database Schema
-- PostgreSQL initialization script

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    encrypted_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS policies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    carrier_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    current_rate FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_policies_user_id ON policies(user_id);

CREATE TABLE IF NOT EXISTS policy_snapshots (
    id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    raw_slip_content TEXT,
    parsed_limits JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_policy_snapshots_policy_id ON policy_snapshots(policy_id);

CREATE TABLE IF NOT EXISTS claims (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    carrier_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'filed',
    filed_date TIMESTAMPTZ DEFAULT NOW(),
    photo_blob TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_user_id ON claims(user_id);

CREATE TABLE IF NOT EXISTS rate_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    carrier_id VARCHAR(100) NOT NULL,
    date TIMESTAMPTZ DEFAULT NOW(),
    rate FLOAT NOT NULL
);

CREATE INDEX idx_rate_snapshots_user_id ON rate_snapshots(user_id);
CREATE INDEX idx_rate_snapshots_carrier_id ON rate_snapshots(carrier_id);