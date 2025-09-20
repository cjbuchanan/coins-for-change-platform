-- Initialize database for Coins for Change platform

-- Create test database for running tests
CREATE DATABASE coins_for_change_test;

-- Grant permissions to the user
GRANT ALL PRIVILEGES ON DATABASE coins_for_change TO cfc_user;
GRANT ALL PRIVILEGES ON DATABASE coins_for_change_test TO cfc_user;

-- Create extensions that might be needed
\c coins_for_change;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c coins_for_change_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";