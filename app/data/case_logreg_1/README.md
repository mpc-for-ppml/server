# CASE_LOGREG_1 - Logistic Regression Data

Generated with seed: 42
Total samples: 50

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

- Positive (will_purchase = 1): 7 (70.0%)
- Negative (will_purchase = 0): 3 (30.0%)
- Ratio: 2.33:1

## Feature Statistics by Class

| Feature | Positive Mean | Negative Mean | Difference |
|---------|---------------|---------------|------------|
| age | 41.6 | 29.7 | 11.9 |
| income | 61368.1 | 44720.0 | 16648.1 |
| purchase_history | 30.1 | 22.0 | 8.1 |
| web_visits | 60.0 | 65.7 | -5.7 |
