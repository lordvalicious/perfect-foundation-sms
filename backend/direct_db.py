import os
import sys

# Use psycopg directly with the full connection string
# DATABASE_URL format: postgres://user:password@host:port/database?sslmode=require
# The password is npg_cJi4s5TXWZUP but it's being treated as the host

# Let's try connecting directly
import psycopg

# The full URL from .env.production
conn_str = "postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

print(f"Attempting direct psycopg connection...")
print(f"Connection string: {conn_str[:80]}...")

try:
    # Try connecting with the full URL
    conn = psycopg.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT 1 as test")
    result = cur.fetchone()
    print(f"Direct connection SUCCESS: {result}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Direct connection FAILED: {e}")
    print("\nTrying with keyword args...")
    
    # Try parsing the URL manually
    # postgres://npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
    # user=npg_cJi4s5TXWZUP, host=ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech, dbname=neondb, sslmode=require
    
    try:
        conn = psycopg.connect(
            host="ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech",
            dbname="neondb",
            user="npg_cJi4s5TXWZUP",
            sslmode="require"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1 as test")
        result = cur.fetchone()
        print(f"Connection with kwargs SUCCESS: {result}")
        cur.close()
        conn.close()
    except Exception as e2:
        print(f"Connection with kwargs also FAILED: {e2}")