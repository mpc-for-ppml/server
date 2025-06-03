import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Generate base customer data
n_total_customers = 400  # Total pool of customers
n_per_party = 250  # Each party gets 250 customers

# Create customer pool
customer_ids = list(range(1001, 1001 + n_total_customers))
emails = [f"customer{i}@example.com" for i in range(1, n_total_customers + 1)]

# Create overlapping sets for each party
# Ensure significant overlap
overlap_all = random.sample(range(n_total_customers), 100)  # 100 customers in all 3 parties
overlap_ab = random.sample([i for i in range(n_total_customers) if i not in overlap_all], 50)
overlap_bc = random.sample([i for i in range(n_total_customers) if i not in overlap_all + overlap_ab], 50)
overlap_ac = random.sample([i for i in range(n_total_customers) if i not in overlap_all + overlap_ab + overlap_bc], 50)

# Remaining unique customers
remaining = [i for i in range(n_total_customers) if i not in overlap_all + overlap_ab + overlap_bc + overlap_ac]
unique_a = random.sample(remaining, 50)
remaining = [i for i in remaining if i not in unique_a]
unique_b = random.sample(remaining, 50)
remaining = [i for i in remaining if i not in unique_b]
unique_c = random.sample(remaining, 50)

# Create party indices
party_a_indices = overlap_all + overlap_ab + overlap_ac + unique_a
party_b_indices = overlap_all + overlap_ab + overlap_bc + unique_b
party_c_indices = overlap_all + overlap_ac + overlap_bc + unique_c

# Shuffle to randomize order
random.shuffle(party_a_indices)
random.shuffle(party_b_indices)
random.shuffle(party_c_indices)

# Generate data for Party A (e-commerce data)
data_a = []
for idx in party_a_indices[:n_per_party]:
    age = np.random.randint(18, 70)
    income = np.random.normal(50000, 20000)
    purchase_frequency = np.random.poisson(5)
    avg_order_value = np.random.normal(100, 30)
    
    # Target: will_purchase (based on features)
    purchase_prob = 0.2 + (income / 200000) + (purchase_frequency / 20) + (avg_order_value / 500)
    purchase_prob = min(max(purchase_prob, 0), 1)
    will_purchase = 1 if np.random.random() < purchase_prob else 0
    
    data_a.append({
        'customer_id': customer_ids[idx],
        'email': emails[idx],
        'age': age,
        'income': round(income, 2),
        'purchase_frequency': purchase_frequency,
        'avg_order_value': round(avg_order_value, 2),
        'will_purchase': will_purchase
    })

# Generate data for Party B (marketing data)
data_b = []
for idx in party_b_indices[:n_per_party]:
    email_opens = np.random.poisson(10)
    click_rate = np.random.beta(2, 5)
    social_engagement = np.random.randint(0, 100)
    ad_spend = np.random.exponential(50)
    
    # Different features but same identifiers
    data_b.append({
        'customer_id': customer_ids[idx],
        'email': emails[idx],
        'email_opens': email_opens,
        'click_rate': round(click_rate, 3),
        'social_engagement': social_engagement,
        'ad_spend': round(ad_spend, 2)
    })

# Generate data for Party C (customer service data)
data_c = []
for idx in party_c_indices[:n_per_party]:
    support_tickets = np.random.poisson(2)
    satisfaction_score = np.random.randint(1, 6)
    retention_months = np.random.randint(1, 60)
    lifetime_value = np.random.exponential(1000)
    
    data_c.append({
        'customer_id': customer_ids[idx],
        'email': emails[idx],
        'support_tickets': support_tickets,
        'satisfaction_score': satisfaction_score,
        'retention_months': retention_months,
        'lifetime_value': round(lifetime_value, 2)
    })

# Create DataFrames
df_a = pd.DataFrame(data_a)
df_b = pd.DataFrame(data_b)
df_c = pd.DataFrame(data_c)

# Save to CSV files
df_a.to_csv('OrgA.csv', index=False)
df_b.to_csv('OrgB.csv', index=False)
df_c.to_csv('OrgC.csv', index=False)

# Print statistics
print("Dataset Generated Successfully!")
print(f"\nParty A: {len(df_a)} records")
print(f"Columns: {list(df_a.columns)}")
print(f"\nParty B: {len(df_b)} records")
print(f"Columns: {list(df_b.columns)}")
print(f"\nParty C: {len(df_c)} records")
print(f"Columns: {list(df_c.columns)}")

# Check overlaps
ids_a = set(df_a['customer_id'])
ids_b = set(df_b['customer_id'])
ids_c = set(df_c['customer_id'])

print(f"\nOverlap Statistics:")
print(f"Common to all 3 parties: {len(ids_a & ids_b & ids_c)} customers")
print(f"Common to A & B only: {len((ids_a & ids_b) - ids_c)} customers")
print(f"Common to B & C only: {len((ids_b & ids_c) - ids_a)} customers")
print(f"Common to A & C only: {len((ids_a & ids_c) - ids_b)} customers")
print(f"Unique to A: {len(ids_a - ids_b - ids_c)} customers")
print(f"Unique to B: {len(ids_b - ids_a - ids_c)} customers")
print(f"Unique to C: {len(ids_c - ids_a - ids_b)} customers")