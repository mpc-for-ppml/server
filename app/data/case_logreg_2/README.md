# CASE_LOGREG_4PARTY_2 - 4-Party Logistic Regression Data

Generated with seed: 123
Total samples: 250

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
  - Positive: 13 (52.0%)
  - Negative: 12 (48.0%)
  - Ratio: 1.08:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 45.1 | 41.2 | 3.8 |
| income | 69991.8 | 36932.6 | 33059.3 |
| purchase_history | 27.8 | 14.3 | 13.5 |
| web_visits | 54.3 | 20.3 | 34.0 |
| credit_score | 728.2 | 643.6 | 84.6 |
| location_category | 3.8 | 2.3 | 1.5 |
