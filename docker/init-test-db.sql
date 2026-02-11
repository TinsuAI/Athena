-- Create test database for pytest (prevents test fixtures from destroying dev data)
CREATE DATABASE athena_test OWNER athena;
\c athena_test
CREATE EXTENSION IF NOT EXISTS vector;
