# Database Architecture – Non-Profit Golf Organization

This document describes the intent, structure, and relationships of the PostgreSQL database.
It exists to help reason about API design, data integrity, and future changes.

The database represents a golf event management system for a non-profit organization.
Correctness, traceability, and clarity matter more than extreme performance.

---

## Core Concepts (Business View)

The system revolves around:

- **Events** (golf outings, tournaments)
- **Participants** (users and guests)
- **Registrations** (signing up for events)
- **Payments** (how registrations are paid)
- **Roles & access** (admins vs regular users)
- **Scoring & leaderboards**

Think of the database as answering:
> “Who participated in which event, how did they pay, and what happened during the event?”

---

## Event Model

### `event`
Represents a golf event.

Key ideas:
- One event can have many registrations
- One event can have multiple pricing tiers
- One event can have a leaderboard

Important fields:
- Date, location (township, state, zipcode)
- Golf course
- Optional start time

This is the anchor table for most of the system.

---

## Pricing Model

### `event_price_tier`
Represents pricing options for an event (e.g. “Early Bird”, “Member”, “Guest”).

Key ideas:
- Price tiers belong to a specific event
- Tier names are unique per event
- Tiers can be activated/deactivated without deletion

This allows:
- Flexible pricing
- Historical price integrity
- Clean separation between event details and pricing logic

---

## Participants

### `user`
Represents a golfer’s profile (non-auth).

Contains:
- Name
- Handicap
- Team information
- Signup-related metadata

This table does **not** handle authentication.

---

### `guest`
Represents non-registered participants.

Used when:
- Someone plays but does not have an account
- A registered user brings a guest

Guests can appear in:
- Event registrations
- Leaderboards

---

## Authentication & Accounts

### `user_account`
Represents login credentials and identity.

Key ideas:
- One-to-one relationship with `user`
- Supports multiple auth providers
- Stores password hashes or external provider IDs
- Tracks account status and last login

This separation allows:
- Clean auth logic
- Future SSO support
- User profile changes without auth coupling

---

## Roles & Authorization

### `role`
Defines system roles (e.g. admin, staff, user).

### `user_role`
Join table allowing:
- Multiple roles per account
- Clean role-based access control

Authorization decisions should be driven from this model.

---

## Event Participation

### `event_registration`
Represents a participant signing up for an event.

Key ideas:
- Ties together event, user/guest, and pricing tier
- Tracks payment status independently of payments
- Stores contact info at time of registration (historical accuracy)

Important:
- Payment status lives here, but payment records are separate
- A registration can exist before payment is completed

This table is central to:
- Check-in
- Payments
- Event operations

---

## Payments

### `payment_method`
Defines allowed payment methods (e.g. Stripe, Zelle, Cash).

### `payment`
Represents an actual payment attempt or record.

Key ideas:
- Payments belong to registrations
- Payments have status (pending, completed, failed, admin-marked)
- External references allow reconciliation with third-party systems

Payments are **append-only records**.
Do not overwrite history.

---

## Event Results

### `leaderboard`
Represents scoring results for an event.

Key ideas:
- Supports both users and guests
- Stores gross and net scores
- Tracks positions and flights
- Updated after event play

Leaderboards are event-specific and immutable after finalization (conceptually).

---

## Relationships Summary (Mental Model)

- Event → many price tiers
- Event → many registrations
- Registration → one price tier
- Registration → many payments
- User ↔ user_account (1:1)
- User ↔ roles (many-to-many)
- Event ↔ users (many-to-many via registrations / user_event)
- Event → leaderboard entries

---

## Design Principles

- PostgreSQL is the source of truth
- Foreign keys enforce integrity
- Business state is explicit (e.g. payment_status)
- History is preserved (no destructive updates)

Avoid:
- Storing business logic in the database
- Overuse of triggers
- JSON blobs for relational data

---

## Guidance for Future Changes

When adding new features:
- Identify the core business entity first
- Decide if it is stateful or transactional
- Prefer new tables over overloading existing ones
- Explain changes in business terms before schema changes

Always consider:
- How this affects reporting
- How this affects historical data
- How this affects API contracts