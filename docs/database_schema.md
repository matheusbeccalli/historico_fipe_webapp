# FIPE Database Schema Documentation

## Overview

This database stores historical car price data scraped from the FIPE (Fundação Instituto de Pesquisas Econômicas) website. The schema is fully normalized across 5 tables with foreign key relationships.

## Database: `fipe_data.db` (SQLite)

## Tables

### 1. reference_months

Stores time periods for which price data is available.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `month_code` (VARCHAR(50), UNIQUE, NOT NULL) - FIPE's internal code (e.g., "21")
- `month_date` (DATE, NOT NULL) - Date representation (e.g., 2024-01-01 for Janeiro/2024)
- `created_at` (DATE) - Timestamp when record was created

**Example Data:**
```
id | month_code | month_date  | created_at
1  | 21         | 2024-01-01  | 2025-10-13
2  | 22         | 2024-02-01  | 2025-10-13
```

**Relationships:**
- One-to-Many with `car_prices`

---

### 2. brands

Stores car manufacturers/brands.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `brand_code` (VARCHAR(50), UNIQUE, NOT NULL) - FIPE's internal code
- `brand_name` (VARCHAR(100), NOT NULL) - Brand name (e.g., "Volkswagen")
- `created_at` (DATE) - Timestamp when record was created

**Example Data:**
```
id | brand_code | brand_name     | created_at
1  | 1          | Acura          | 2025-10-13
2  | 2          | Agrale         | 2025-10-13
3  | 59         | Volkswagen     | 2025-10-13
```

**Relationships:**
- One-to-Many with `car_models`

---

### 3. car_models

Stores specific car models within each brand.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `brand_id` (INTEGER, FOREIGN KEY → brands.id, NOT NULL) - Reference to brand
- `model_code` (VARCHAR(50), NOT NULL) - FIPE's internal code
- `model_name` (VARCHAR(200), NOT NULL) - Model name (e.g., "Gol 1.0")
- `created_at` (DATE) - Timestamp when record was created

**Constraints:**
- UNIQUE(`brand_id`, `model_code`) - Prevents duplicate models per brand

**Example Data:**
```
id | brand_id | model_code | model_name           | created_at
1  | 1        | 1          | Integra GS 1.8       | 2025-10-13
2  | 1        | 2          | Legend 3.2/3.5       | 2025-10-13
3  | 3        | 5890       | Gol 1.0 Flex         | 2025-10-13
```

**Relationships:**
- Many-to-One with `brands`
- One-to-Many with `model_years`

---

### 4. model_years

Stores year and fuel type combinations for each car model.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `car_model_id` (INTEGER, FOREIGN KEY → car_models.id, NOT NULL) - Reference to model
- `year_code` (VARCHAR(50), NOT NULL) - FIPE's internal code
- `year_description` (VARCHAR(100), NOT NULL) - Year + fuel type (e.g., "2024 Gasolina")
- `created_at` (DATE) - Timestamp when record was created

**Constraints:**
- UNIQUE(`car_model_id`, `year_code`) - Prevents duplicate years per model

**Example Data:**
```
id | car_model_id | year_code | year_description  | created_at
1  | 1            | 1         | 1992 Gasolina     | 2025-10-13
2  | 1            | 2         | 1991 Gasolina     | 2025-10-13
3  | 3            | 1         | 2024 Flex         | 2025-10-13
```

**Relationships:**
- Many-to-One with `car_models`
- One-to-Many with `car_prices`

---

### 5. car_prices

**⭐ Main table** - Stores actual price data linking months with vehicle configurations.

**Columns:**
- `id` (INTEGER, PRIMARY KEY) - Auto-increment ID
- `reference_month_id` (INTEGER, FOREIGN KEY → reference_months.id, NOT NULL)
- `model_year_id` (INTEGER, FOREIGN KEY → model_years.id, NOT NULL)
- `price` (FLOAT, NOT NULL) - Price in BRL (Brazilian Real)
- `fipe_code` (VARCHAR(50)) - FIPE code for this vehicle (e.g., "038003-2")
- `vehicle_type` (VARCHAR(50)) - Vehicle category (currently NULL, reserved)
- `fuel_type` (VARCHAR(50)) - Fuel type (currently NULL, in year_description)
- `scraped_at` (DATE) - When this data was scraped

**Constraints:**
- UNIQUE(`reference_month_id`, `model_year_id`) - One price per month/year combo

**Example Data:**
```
id | reference_month_id | model_year_id | price    | fipe_code  | scraped_at
1  | 1                  | 1             | 11520.00 | 038003-2   | 2025-10-13
2  | 1                  | 2             | 10761.00 | 038003-2   | 2025-10-13
```

**Relationships:**
- Many-to-One with `reference_months`
- Many-to-One with `model_years`

---

## Entity Relationship Diagram

```
┌─────────────────┐
│ reference_months│
│ ─────────────── │
│ id (PK)         │
│ month_code      │
│ month_date      │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│   car_prices    │ N:1   │  model_years    │
│ ─────────────── │◄──────│ ─────────────── │
│ id (PK)         │       │ id (PK)         │
│ ref_month_id(FK)│       │ car_model_id(FK)│
│ model_year_id(FK)       │ year_code       │
│ price           │       │ year_description│
│ fipe_code       │       └────────┬────────┘
└─────────────────┘                │
                                   │ N:1
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   car_models    │
                          │ ─────────────── │
                          │ id (PK)         │
                          │ brand_id (FK)   │
                          │ model_code      │
                          │ model_name      │
                          └────────┬────────┘
                                   │
                                   │ N:1
                                   │
                                   ▼
                          ┌─────────────────┐
                          │     brands      │
                          │ ─────────────── │
                          │ id (PK)         │
                          │ brand_code      │
                          │ brand_name      │
                          └─────────────────┘
```

## Complete Query Path

To get full vehicle information with price:

```
CarPrice → ModelYear → CarModel → Brand
    ↓
ReferenceMonth
```

## Sample Full Query Result

```sql
SELECT
    b.brand_name,
    cm.model_name,
    my.year_description,
    rm.month_date,
    cp.price,
    cp.fipe_code
FROM car_prices cp
JOIN reference_months rm ON cp.reference_month_id = rm.id
JOIN model_years my ON cp.model_year_id = my.id
JOIN car_models cm ON my.car_model_id = cm.id
JOIN brands b ON cm.brand_id = b.id
LIMIT 5;
```

**Expected Output:**
```
brand_name | model_name      | year_description | month_date  | price    | fipe_code
Acura      | Integra GS 1.8  | 1992 Gasolina   | 2024-01-01  | 11520.00 | 038003-2
Acura      | Integra GS 1.8  | 1991 Gasolina   | 2024-01-01  | 10761.00 | 038003-2
Volkswagen | Gol 1.0         | 2024 Flex       | 2024-01-01  | 45890.00 | 005339-1
...
```

## Data Volume Estimates

For full historical data (2001-2025, ~300 months):
- **reference_months**: ~300 rows
- **brands**: ~100 rows
- **car_models**: ~50,000 rows
- **model_years**: ~500,000 rows (each model × ~10 years average)
- **car_prices**: ~150,000,000 rows (500k years × 300 months)

## Indexing Recommendations for Webapp

For optimal query performance in your webapp:

```sql
-- Already have primary keys and unique constraints
-- Add these indexes for common queries:

CREATE INDEX idx_prices_month ON car_prices(reference_month_id);
CREATE INDEX idx_prices_model_year ON car_prices(model_year_id);
CREATE INDEX idx_model_years_model ON model_years(car_model_id);
CREATE INDEX idx_models_brand ON car_models(brand_id);
CREATE INDEX idx_months_date ON reference_months(month_date);
```

## Notes for Webapp Development

1. **Read-Only Access**: Webapp should only SELECT, never INSERT/UPDATE/DELETE
2. **Connection String**: Use same `DATABASE_URL` from config.py
3. **Date Format**: Dates stored as YYYY-MM-DD, display as "Janeiro/2024" for UX
4. **Price Format**: Stored as float, display as "R$ 11.520,00" (Brazilian format)
5. **Fuel Types**: Currently in `year_description`, may want to parse separately
6. **Missing Data**: Some month/year combos may not exist (FIPE data gaps)
