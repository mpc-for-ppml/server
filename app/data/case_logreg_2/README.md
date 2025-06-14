# CASE_LOGREG_2 - Logistic Regression Data

Generated with seed: 123
Total samples: 250

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

- Positive (will_purchase = 1): 20 (64.5%)
- Negative (will_purchase = 0): 11 (35.5%)
- Ratio: 1.82:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 40.8 | 53.0 | -12.2 |
| income | 40421.7 | 55644.7 | -15223.1 |
| purchase_history | 29.4 | 25.5 | 4.0 |
| web_visits | 51.6 | 40.5 | 11.1 |
