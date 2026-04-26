# cURL Tests for Multi-DB SQL Agent

This document contains a series of cURL commands you can run to test the endpoints of the FastAPI application.
Run the application locally (`uvicorn app2:app --reload`) or via Docker before running these tests.

## 1. Test Root Endpoint (Frontend HTML)
```bash
curl -X GET "http://localhost:8000/"
```

## 2. Get All Schemas
Fetches all tables from the connected database. Replace the `db_url` with your actual database URL if different.
```bash
curl -X POST "http://localhost:8000/schemas" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
         }'
```

## 3. Get Table Details
Replace `YOUR_TABLE_NAME` with an actual table name from your schema.
```bash
curl -X POST "http://localhost:8000/schemas/YOUR_TABLE_NAME" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
         }'
```

## 4. Get Table Data with Pagination
```bash
curl -X POST "http://localhost:8000/schemas/YOUR_TABLE_NAME/data" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
           "page": 1,
           "limit": 50
         }'
```

## 5. Generate SQL Insight / Analysis
Asks the AI to generate a SQL query based on the database schema to answer your natural language query.
```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
           "query": "Show me the top 5 records from the database",
           "safe_mode": true
         }'
```

## 6. Generate Insights Dashboard
Generates a full dashboard plan with multiple charts powered by AI.
```bash
curl -X POST "http://localhost:8000/gen-dashboard" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
         }'
```

## 7. Optimize SQL
Explains and optimizes an existing SQL query.
```bash
curl -X POST "http://localhost:8000/optimize" \
     -H "Content-Type: application/json" \
     -d '{
           "db_url": "postgresql://neondb_owner:npg_UCdk9eMi2vGn@ep-mute-firefly-amtmu27v-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
           "query": "SELECT * FROM my_table WHERE id > 0"
         }'
```
