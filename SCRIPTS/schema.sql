-- ============================================================
-- Marriott International – Hotel Revenue Analytics
-- PostgreSQL Schema
-- ============================================================

-- Drop tables if they exist (clean slate)
DROP TABLE IF EXISTS Revenue_Facts CASCADE;
DROP TABLE IF EXISTS Reservations CASCADE;
DROP TABLE IF EXISTS Rooms CASCADE;
DROP TABLE IF EXISTS Customers CASCADE;
DROP TABLE IF EXISTS Hotels CASCADE;

-- ─────────────────────────────────────────
-- TABLE 1 : Hotels
-- ─────────────────────────────────────────
CREATE TABLE Hotels (
    hotel_id   SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    city       VARCHAR(100),
    country    VARCHAR(100),
    category   VARCHAR(50)   -- e.g. Luxury, Upper-Upscale, Select
);

-- ─────────────────────────────────────────
-- TABLE 2 : Rooms
-- ─────────────────────────────────────────
CREATE TABLE Rooms (
    room_id     SERIAL PRIMARY KEY,
    hotel_id    INT NOT NULL REFERENCES Hotels(hotel_id) ON DELETE CASCADE,
    room_type   VARCHAR(50),   -- Standard, Suite, Deluxe, etc.
    base_price  DECIMAL(10,2),
    capacity    INT
);

-- ─────────────────────────────────────────
-- TABLE 3 : Customers
-- ─────────────────────────────────────────
CREATE TABLE Customers (
    customer_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100),
    loyalty_tier  VARCHAR(20),  -- Silver, Gold, Platinum, None
    country       VARCHAR(100)
);

-- ─────────────────────────────────────────
-- TABLE 4 : Reservations
-- ─────────────────────────────────────────
CREATE TABLE Reservations (
    reservation_id   SERIAL PRIMARY KEY,
    room_id          INT NOT NULL REFERENCES Rooms(room_id),
    customer_id      INT NOT NULL REFERENCES Customers(customer_id),
    check_in         DATE NOT NULL,
    check_out        DATE NOT NULL,
    channel          VARCHAR(50),  -- Direct, OTA, Corporate, Travel Agent
    total_revenue    DECIMAL(10,2),
    is_cancelled     BOOLEAN DEFAULT FALSE,
    lead_time_days   INT           -- days between booking and check-in
);

-- ─────────────────────────────────────────
-- TABLE 5 : Revenue_Facts  (analytical table)
-- ─────────────────────────────────────────
CREATE TABLE Revenue_Facts (
    fact_id          SERIAL PRIMARY KEY,
    reservation_id   INT REFERENCES Reservations(reservation_id),
    hotel_id         INT REFERENCES Hotels(hotel_id),
    date             DATE NOT NULL,
    RevPAR           DECIMAL(10,2),  -- Revenue Per Available Room
    ADR              DECIMAL(10,2),  -- Average Daily Rate
    occupancy_rate   DECIMAL(5,2)    -- percentage 0-100
);

-- ─────────────────────────────────────────
-- SAMPLE DATA
-- ─────────────────────────────────────────

INSERT INTO Hotels (name, city, country, category) VALUES
('Marriott Paris Opera',     'Paris',     'France',        'Upper-Upscale'),
('Ritz-Carlton New York',    'New York',  'USA',           'Luxury'),
('Courtyard London City',    'London',    'United Kingdom','Select'),
('JW Marriott Dubai',        'Dubai',     'UAE',           'Luxury'),
('Marriott Tokyo Marunouchi','Tokyo',     'Japan',         'Upper-Upscale');

INSERT INTO Rooms (hotel_id, room_type, base_price, capacity) VALUES
(1, 'Standard',  180.00, 2),
(1, 'Deluxe',    240.00, 2),
(1, 'Suite',     450.00, 4),
(2, 'Standard',  350.00, 2),
(2, 'Suite',     900.00, 4),
(3, 'Standard',  150.00, 2),
(4, 'Deluxe',    280.00, 2),
(4, 'Suite',     700.00, 4),
(5, 'Standard',  200.00, 2),
(5, 'Deluxe',    310.00, 3);

INSERT INTO Customers (name, loyalty_tier, country) VALUES
('Alex Hitchens',    'Gold',     'France'),
('Bruce Wayne',      'Platinum', 'USA'),
('Liam Cartwright',  'Silver',   'United Kingdom'),
('Keo Risen',        'None',     'UAE'),
('Haruki Sendo',     'Gold',     'Japan'),
('Thomas Renard',    'None',     'France'),
('Claire Novak',     'Platinum', 'USA');

INSERT INTO Reservations (room_id, customer_id, check_in, check_out, channel, total_revenue, is_cancelled, lead_time_days) VALUES
(1, 1, '2024-07-15', '2024-07-18', 'Direct',       540.00,  FALSE, 30),
(2, 2, '2024-08-01', '2024-08-05', 'OTA',           860.00,  FALSE, 14),
(3, 3, '2024-12-24', '2024-12-27', 'Direct',        1350.00, FALSE, 60),
(4, 4, '2024-03-10', '2024-03-12', 'Corporate',     700.00,  FALSE, 7),
(5, 5, '2024-09-05', '2024-09-08', 'OTA',           2340.00, FALSE, 21),
(6, 6, '2024-11-20', '2024-11-22', 'Travel Agent',  300.00,  TRUE,  45),
(7, 7, '2024-07-04', '2024-07-07', 'Direct',        840.00,  FALSE, 90),
(1, 3, '2024-02-14', '2024-02-16', 'OTA',           320.00,  FALSE, 10),
(9, 1, '2024-06-01', '2024-06-04', 'Direct',        600.00,  FALSE, 20),
(10,2, '2024-10-10', '2024-10-13', 'Corporate',     870.00,  FALSE, 5);
