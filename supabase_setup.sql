CREATE TABLE IF NOT EXISTS bookings (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  service TEXT NOT NULL,
  stylist TEXT NOT NULL,
  date TEXT NOT NULL,
  time TEXT,
  booked_by TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);