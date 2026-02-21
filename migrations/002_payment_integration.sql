-- Migration: Payment integration
-- Date: 2026-02-27
-- Run: psql $DATABASE_URL -f migrations/002_payment_integration.sql
-- Idempotent: safe to run multiple times.

BEGIN;

-- 1. ALTER saga.payment — add North gateway + membership columns
ALTER TABLE saga.payment
    ADD COLUMN IF NOT EXISTS membership_id     INTEGER NULL,
    ADD COLUMN IF NOT EXISTS payment_type      VARCHAR(50) NOT NULL DEFAULT 'event_registration',
    ADD COLUMN IF NOT EXISTS north_token       VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS north_response    JSONB NULL,
    ADD COLUMN IF NOT EXISTS refunded_at       TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS idempotency_key   VARCHAR(255) NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_idempotency
    ON saga.payment(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- 2. Seed saga.payment_method (existing table, currently empty)
INSERT INTO saga.payment_method (name)
SELECT name FROM (VALUES ('credit_card'), ('cash'), ('check'), ('zelle')) AS v(name)
WHERE NOT EXISTS (SELECT 1 FROM saga.payment_method WHERE payment_method.name = v.name);

-- 3. CREATE saga.membership_tiers
CREATE TABLE IF NOT EXISTS saga.membership_tiers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    amount          NUMERIC(10,2) NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    description     TEXT NULL,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed from existing membership_options (if tiers table is empty)
INSERT INTO saga.membership_tiers (name, amount, description, sort_order, is_active)
SELECT name, price, description, display_order, is_active
FROM saga.membership_options
WHERE NOT EXISTS (SELECT 1 FROM saga.membership_tiers LIMIT 1)
ORDER BY display_order;

-- 4. CREATE saga.member_memberships
CREATE TABLE IF NOT EXISTS saga.member_memberships (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES saga."user"(id),
    tier_id              INTEGER NOT NULL REFERENCES saga.membership_tiers(id),
    payment_id           INTEGER NULL,
    season_year          INTEGER NOT NULL,
    status               VARCHAR(30) NOT NULL DEFAULT 'pending',
    marked_paid_by_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, season_year)
);

CREATE INDEX IF NOT EXISTS idx_memberships_user   ON saga.member_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_status ON saga.member_memberships(status);

-- FK from payment.membership_id -> member_memberships
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_payment_membership' AND table_schema = 'saga'
    ) THEN
        ALTER TABLE saga.payment
            ADD CONSTRAINT fk_payment_membership
            FOREIGN KEY (membership_id) REFERENCES saga.member_memberships(id);
    END IF;
END $$;

-- 5. CREATE saga.guest_registrations
CREATE TABLE IF NOT EXISTS saga.guest_registrations (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(255) NOT NULL,
    last_name       VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL,
    phone           VARCHAR(50) NOT NULL,
    handicap        VARCHAR(50) NULL,
    referral_source TEXT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. CREATE saga.app_settings
CREATE TABLE IF NOT EXISTS saga.app_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by  INTEGER NULL REFERENCES saga."user"(id)
);

INSERT INTO saga.app_settings (key, value)
SELECT 'guest_event_rate', '0'
WHERE NOT EXISTS (SELECT 1 FROM saga.app_settings WHERE key = 'guest_event_rate');

COMMIT;
