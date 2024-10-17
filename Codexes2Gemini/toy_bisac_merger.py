import pandas as pd

# Load the CSV files into pandas DataFrames
output2_df = pd.read_csv('output/output2.csv')
bisacs_df = pd.read_csv('output/bisacs.csv')

# Merge the DataFrames on 'Publisher Reference ID'
merged_df = pd.merge(output2_df, bisacs_df, on='Publisher Reference ID', how='left')

# Update the values in output2_df
output2_df['BISAC Category'] = merged_df['Description 1']
output2_df['BISAC Category 2'] = merged_df['Description 2']
output2_df['BISAC Category 3'] = merged_df['Description 3']

# Save the updated output2.csv
output2_df.to_csv('output2_updated.csv', index=False)

print("output2.csv updated successfully!")
