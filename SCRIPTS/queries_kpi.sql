-- ============================================================
-- Marriott International – KPI Queries
-- ============================================================

-- ─────────────────────────────────────────
-- 1. RevPAR by hotel & month
--    RevPAR = Total Revenue / Total Available Rooms
-- ─────────────────────────────────────────
SELECT
    h.name                                          AS hotel,
    TO_CHAR(r.check_in, 'YYYY-MM')                 AS month,
    ROUND(
        SUM(r.total_revenue) /
        NULLIF(COUNT(DISTINCT ro.room_id), 0)
    , 2)                                            AS RevPAR
FROM Reservations r
JOIN Rooms  ro ON ro.room_id  = r.room_id
JOIN Hotels h  ON h.hotel_id  = ro.hotel_id
WHERE r.is_cancelled = FALSE
GROUP BY h.name, TO_CHAR(r.check_in, 'YYYY-MM')
ORDER BY month, RevPAR DESC;


-- ─────────────────────────────────────────
-- 2. ADR (Average Daily Rate) by hotel
--    ADR = Total Revenue / Number of rooms sold
-- ─────────────────────────────────────────
SELECT
    h.name                                          AS hotel,
    COUNT(r.reservation_id)                         AS rooms_sold,
    ROUND(AVG(r.total_revenue), 2)                  AS ADR
FROM Reservations r
JOIN Rooms  ro ON ro.room_id = r.room_id
JOIN Hotels h  ON h.hotel_id = ro.hotel_id
WHERE r.is_cancelled = FALSE
GROUP BY h.name
ORDER BY ADR DESC;


-- ─────────────────────────────────────────
-- 3. Revenue by booking channel
-- ─────────────────────────────────────────
SELECT
    channel,
    COUNT(*)                        AS total_bookings,
    SUM(total_revenue)              AS total_revenue,
    ROUND(AVG(total_revenue), 2)    AS avg_revenue_per_booking,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER ()
    , 1)                            AS booking_share_pct
FROM Reservations
WHERE is_cancelled = FALSE
GROUP BY channel
ORDER BY total_revenue DESC;


-- ─────────────────────────────────────────
-- 4. Occupancy rate by hotel
--    Occupancy = Rooms Sold / Available Rooms * 100
-- ─────────────────────────────────────────
SELECT
    h.name                                          AS hotel,
    COUNT(DISTINCT ro.room_id)                      AS total_rooms,
    COUNT(r.reservation_id)                         AS reservations_made,
    ROUND(
        COUNT(r.reservation_id) * 100.0 /
        NULLIF(COUNT(DISTINCT ro.room_id) * 12, 0)  -- 12 months
    , 1)                                            AS occupancy_rate_pct
FROM Hotels h
JOIN Rooms ro        ON ro.hotel_id = h.hotel_id
LEFT JOIN Reservations r ON r.room_id = ro.room_id
                        AND r.is_cancelled = FALSE
GROUP BY h.name
ORDER BY occupancy_rate_pct DESC;


-- ─────────────────────────────────────────
-- 5. Cancellation rate by loyalty tier
-- ─────────────────────────────────────────
SELECT
    c.loyalty_tier,
    COUNT(*)                                        AS total_bookings,
    SUM(CASE WHEN r.is_cancelled THEN 1 ELSE 0 END) AS cancellations,
    ROUND(
        SUM(CASE WHEN r.is_cancelled THEN 1 ELSE 0 END) * 100.0 /
        COUNT(*)
    , 1)                                            AS cancellation_rate_pct
FROM Reservations r
JOIN Customers c ON c.customer_id = r.customer_id
GROUP BY c.loyalty_tier
ORDER BY cancellation_rate_pct DESC;


-- ─────────────────────────────────────────
-- 6. Seasonal revenue trend (by month, all hotels)
-- ─────────────────────────────────────────
SELECT
    TO_CHAR(check_in, 'MM')         AS month_number,
    TO_CHAR(check_in, 'Month')      AS month_name,
    COUNT(*)                        AS bookings,
    SUM(total_revenue)              AS total_revenue,
    ROUND(AVG(total_revenue), 2)    AS avg_revenue
FROM Reservations
WHERE is_cancelled = FALSE
GROUP BY TO_CHAR(check_in, 'MM'), TO_CHAR(check_in, 'Month')
ORDER BY month_number;
