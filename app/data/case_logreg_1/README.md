# CASE_LOGREG_4PARTY_1 - 4-Party Logistic Regression Data

Generated with seed: 42
Total samples: 50

## Data Structure

### OrgA.csv (Demographics & Target)
- `user_id`: Unique identifier
- `age`: Customer age (18-80 years)
- `income`: Annual income ($15k-$200k)
- `will_purchase`: Target variable (0 or 1)

### OrgB.csv (Purchase Behavior)
- `user_id`: Unique identifier
- `purchase_history`: Number of previous purchases (0-100)

### OrgC.csv (Digital Engagement)
- `user_id`: Unique identifier
- `web_visits`: Website visits in last month (0-150)

### OrgD.csv (Financial & Location Data)
- `user_id`: Unique identifier
- `credit_score`: Credit score (300-850)
- `location_category`: Location type (1=Rural, 5=Urban)

## Logistic Relationship

Features are generated to create realistic separation between classes:
- Positive class: higher income, peak age (35-55), more purchases, more visits, higher credit, urban location
- Negative class: lower income, varied age, fewer purchases, fewer visits, lower credit, rural location

The logistic function uses 6 features with realistic coefficients:
- Income: 1.3x weight
- Credit Score: 1.1x weight
- Purchase History: 1.0x weight
- Age (peak factor): 0.8x weight
- Web Visits: 0.7x weight
- Location: 0.6x weight

## Class Distribution

- Target ratio: ~55% positive, ~45% negative
- Actual intersection:
  - Positive: 4 (50.0%)
  - Negative: 4 (50.0%)
  - Ratio: 1.00:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 39.2 | 49.0 | -9.8 |
| income | 79019.0 | 55673.8 | 23345.2 |
| purchase_history | 25.8 | 7.2 | 18.5 |
| web_visits | 48.0 | 27.2 | 20.8 |
| credit_score | 655.0 | 714.2 | -59.2 |
| location_category | 3.5 | 3.2 | 0.2 |
