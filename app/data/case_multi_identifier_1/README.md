# Multi-Identifier Test Dataset

## Overview
This dataset demonstrates the multi-identifier feature with 3 organizations sharing overlapping customer data. Each organization has different features but shares 2 common identifiers: `customer_id` and `email`.

## Dataset Structure

### Party A (OrgA.csv) - E-commerce Data
- **Records**: 250
- **Identifiers**: `customer_id`, `email`
- **Features**: `age`, `income`, `purchase_frequency`, `avg_order_value`
- **Target**: `will_purchase` (binary: 0/1)

### Party B (OrgB.csv) - Marketing Data  
- **Records**: 250
- **Identifiers**: `customer_id`, `email`
- **Features**: `email_opens`, `click_rate`, `social_engagement`, `ad_spend`
- **No target variable** (Party B contributes features only)

### Party C (OrgC.csv) - Customer Service Data
- **Records**: 250
- **Identifiers**: `customer_id`, `email`
- **Features**: `support_tickets`, `satisfaction_score`, `retention_months`, `lifetime_value`
- **No target variable** (Party C contributes features only)

## Overlap Statistics
- **Common to all 3 parties**: 100 customers
- **Common to A & B only**: 50 customers  
- **Common to B & C only**: 50 customers
- **Common to A & C only**: 50 customers
- **Unique to each party**: 50 customers each

## Usage Examples

### 1. Single Identifier (customer_id)
```json
{
  "mode": "single",
  "columns": ["customer_id"]
}
```

### 2. Single Identifier (email)
```json
{
  "mode": "single", 
  "columns": ["email"]
}
```

### 3. Combined Identifiers
```json
{
  "mode": "combined",
  "columns": ["customer_id", "email"],
  "separator": "_"
}
```

## Expected Results
- **100 intersected records** when using any identifier configuration
- **Combined features**: 10 total features from all parties
- **Target**: `will_purchase` (from Party A only)
- **Regression type**: Logistic regression (binary classification)

## Testing Scenarios

1. **Test single identifier**: Use either `customer_id` or `email`
2. **Test combined identifier**: Use both `customer_id` and `email` 
3. **Test column analysis**: Should show both identifiers as potential options
4. **Test intersection**: Should find 100 common customers across all parties