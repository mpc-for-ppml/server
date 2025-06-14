# CASE_LOGREG_3 - Logistic Regression Data

Generated with seed: 456
Total samples: 500

## Data Structure

### OrgA.csv (Demographics & Target)
- `user_id`: Unique identifier
- `age`: Customer age (18-80 years)
- `income`: Annual income ($15k-$250k)
- `will_purchase`: Target variable (0 or 1)

### OrgB.csv (Purchase Behavior)
- `user_id`: Unique identifier
- `purchase_history`: Number of previous purchases (0-100)

### OrgC.csv (Digital Engagement)
- `user_id`: Unique identifier
- `web_visits`: Website visits in last month (0-150)

## Logistic Relationship Formula

```
logit(p) = -2.5 + 
           3.0 � income_normalized + 
           2.0 � age_factor + 
           2.5 � purchase_history_normalized + 
           1.5 � web_visits_normalized + 
           noise

probability = sigmoid(logit(p))
will_purchase = 1 if random() < probability else 0
```

## Class Distribution

- Positive (will_purchase = 1): 45 (72.6%)
- Negative (will_purchase = 0): 17 (27.4%)
- Ratio: 2.65:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 40.6 | 42.9 | -2.3 |
| income | 51609.6 | 46255.4 | 5354.2 |
| purchase_history | 27.1 | 25.2 | 1.9 |
| web_visits | 55.6 | 48.9 | 6.7 |
