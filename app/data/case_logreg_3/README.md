# CASE_LOGREG_4PARTY_3 - 4-Party Logistic Regression Data

Generated with seed: 456
Total samples: 500

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
  - Positive: 27 (54.0%)
  - Negative: 23 (46.0%)
  - Ratio: 1.17:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 45.3 | 42.7 | 2.6 |
| income | 70212.9 | 50074.6 | 20138.3 |
| purchase_history | 34.7 | 14.6 | 20.1 |
| web_visits | 57.0 | 28.4 | 28.6 |
| credit_score | 707.8 | 664.4 | 43.3 |
| location_category | 3.9 | 2.3 | 1.5 |
