# CASE_LINREG_4PARTY_3 - 4-Party Linear Regression Data

Generated with seed: 456
Total samples: 500

## Data Structure

### OrgA.csv (Demographics & Target)
- `user_id`: Unique identifier
- `age`: Customer age (25-75 years)
- `income`: Annual income ($25k-$200k)
- `purchase_amount`: Target variable ($100-$60k)

### OrgB.csv (Purchase Behavior)
- `user_id`: Unique identifier
- `purchase_history`: Number of previous purchases (0-50)

### OrgC.csv (Digital Engagement)
- `user_id`: Unique identifier
- `web_visits`: Website visits in last month (5-100)

### OrgD.csv (Financial Data)
- `user_id`: Unique identifier
- `credit_score`: Credit score (300-850)
- `location_category`: Location type (1=Rural, 5=Urban)

## Linear Relationship Formula

```
purchase_amount = 400 + 
                  0.06 � income + 
                  120 � age + 
                  35 � purchase_history + 
                  10 � web_visits + 
                  8 � credit_score + 
                  400 � location_category + 
                  noise
```

## Feature Correlations

- age: 0.438
- income: 0.775
- purchase_history: 0.794
- web_visits: 0.529
- credit_score: 0.732
- location_category: 0.242
