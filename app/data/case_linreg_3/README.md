# CASE_LINREG_3 - Linear Regression Data

Generated with seed: 456
Total samples: 500

## Data Structure

### OrgA.csv (Demographics & Target)
- `user_id`: Unique identifier
- `age`: Customer age (25-75 years)
- `income`: Annual income ($25k-$200k)
- `purchase_amount`: Target variable ($100-$50k)

### OrgB.csv (Purchase Behavior)
- `user_id`: Unique identifier
- `purchase_history`: Number of previous purchases (0-50)

### OrgC.csv (Digital Engagement)
- `user_id`: Unique identifier
- `web_visits`: Website visits in last month (5-100)

## Linear Relationship Formula

```
purchase_amount = 500 + 
                  0.08 � income + 
                  150 � age + 
                  45 � purchase_history + 
                  12 � web_visits + 
                  noise
```

## Feature Correlations

- age: 0.643
- income: 0.838
- purchase_history: 0.921
- web_visits: 0.591
