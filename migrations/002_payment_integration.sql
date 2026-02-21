-- Migration: Payment integration tables
-- Date: 2026-02-21
-- Description: Creates membership_tiers, member_memberships, guest_registrations,
--              app_settings, payments, and payment_methods tables for payment processing.

-- membership_tiers table
CREATE TABLE saga.membership_tiers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    amount          NUMERIC NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    description     TEXT NULL,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed membership tiers
INSERT INTO saga.membership_tiers (name, amount, sort_order) VALUES
    ('Individual', 150.00, 1),
    ('Young Adult', 100.00, 2),
    ('Student', 75.00, 3),
    ('Brunswick Team', 200.00, 4);

-- member_memberships table
CREATE TABLE saga.member_memberships (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES saga.user(id),
    tier_id              INTEGER NOT NULL REFERENCES saga.membership_tiers(id),
    payment_id           INTEGER NULL,
    season_year          INTEGER NOT NULL,
    status               VARCHAR(30) NOT NULL DEFAULT 'pending',
    marked_paid_by_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, season_year)
);

CREATE INDEX idx_memberships_user ON saga.member_memberships(user_id);
CREATE INDEX idx_memberships_status ON saga.member_memberships(status);

-- guest_registrations table
CREATE TABLE saga.guest_registrations (
    id                  SERIAL PRIMARY KEY,
    first_name          VARCHAR(255) NOT NULL,
    last_name           VARCHAR(255) NOT NULL,
    email               VARCHAR(255) NOT NULL,
    phone               VARCHAR(50) NOT NULL,
    handicap            VARCHAR(50) NULL,
    referral_source     TEXT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

-- app_settings table
CREATE TABLE saga.app_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by  INTEGER NULL REFERENCES saga.user(id)
);

INSERT INTO saga.app_settings (key, value) VALUES ('guest_event_rate', '0');

-- payments table
CREATE TABLE saga.payments (
    id                SERIAL PRIMARY KEY,
    registration_id   INTEGER NULL REFERENCES saga.event_registration(id),
    membership_id     INTEGER NULL,
    payment_method_id INTEGER NULL,
    payment_type      VARCHAR(50) NOT NULL DEFAULT 'event_registration',
    amount            NUMERIC NOT NULL,
    status            VARCHAR(30) NOT NULL DEFAULT 'pending',
    north_token       VARCHAR(255) NULL,
    north_response    JSONB NULL,
    refunded_at       TIMESTAMP NULL,
    idempotency_key   VARCHAR(255) NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_payments_idempotency ON saga.payments(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Add FK after member_memberships exists
ALTER TABLE saga.payments ADD CONSTRAINT fk_payments_membership
    FOREIGN KEY (membership_id) REFERENCES saga.member_memberships(id);

-- payment_methods table
CREATE TABLE saga.payment_methods (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO saga.payment_methods (name) VALUES ('credit_card'), ('cash'), ('check');

ALTER TABLE saga.payments ADD CONSTRAINT fk_payments_method
    FOREIGN KEY (payment_method_id) REFERENCES saga.payment_methods(id);
