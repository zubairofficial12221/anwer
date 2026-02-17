-- Create DB + tables for NEO-SHOW

CREATE DATABASE IF NOT EXISTS neo_show
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE neo_show;

-- Minimal movie catalog (matches your frontend titles)
CREATE TABLE IF NOT EXISTS movies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One showtime per movie for now (simple). Extend later if needed.
CREATE TABLE IF NOT EXISTS showtimes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  movie_id INT NOT NULL,
  starts_at DATETIME NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_movie_time (movie_id, starts_at),
  CONSTRAINT fk_showtimes_movie FOREIGN KEY (movie_id) REFERENCES movies(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Booking header
CREATE TABLE IF NOT EXISTS bookings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  showtime_id INT NOT NULL,
  customer_email VARCHAR(255) NULL,
  total_price_cents INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_bookings_showtime FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

-- Seats for a booking. Unique per showtime so no double booking.
CREATE TABLE IF NOT EXISTS booking_seats (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  booking_id BIGINT NOT NULL,
  showtime_id INT NOT NULL,
  seat_code VARCHAR(8) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_showtime_seat (showtime_id, seat_code),
  CONSTRAINT fk_booking_seats_booking FOREIGN KEY (booking_id) REFERENCES bookings(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_booking_seats_showtime FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Seed movies + a default showtime (today 19:00) for each movie if missing.
INSERT IGNORE INTO movies (title) VALUES
  ('The Dark Knight'),
  ('Inception'),
  ('Interstellar'),
  ('Dune: Part Two');

-- Create a default showtime per movie at 19:00 today (server date).
INSERT IGNORE INTO showtimes (movie_id, starts_at)
SELECT m.id, STR_TO_DATE(CONCAT(CURDATE(), ' 19:00:00'), '%Y-%m-%d %H:%i:%s')
FROM movies m;

