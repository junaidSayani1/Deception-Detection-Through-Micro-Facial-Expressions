import glob
import os
import pandas as pd
import csv
import numpy as np

# Set the path to the output directory
au_path = r'AU_output/AU_output'

# Get all CSV files from the output directory
csv_files = glob.glob(au_path + "/*.csv")
print(csv_files)
# Create a list to store dataframes
au_data = []
file_count = 0

# Process each CSV file
for filename in csv_files:
    try:
        # Read the CSV file
        df = pd.read_csv(filename, index_col=None, header=0)
        
        # Add metadata
        df['id'] = file_count
        file_count += 1
        df['label'] = "sample"  # You can change this to "truth" or "lie" as needed
        
        # Add to the list
        au_data.append(df)
        print(f"Processed {filename}")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

# Create directory to store combined data if it doesn't exist
os.makedirs("combined_data", exist_ok=True)

# Combine all dataframes
if au_data:
    # Concatenate all dataframes
    combined_frame = pd.concat(au_data, axis=0, ignore_index=True)
    
    # Clean up column names by stripping whitespace
    combined_frame.columns = combined_frame.columns.str.strip()
    
    # Save the combined data
    combined_frame.to_csv("combined_data/combined_sample_data.csv", index=False, encoding='utf-8-sig')
    print(f"Combined data saved to combined_data/combined_sample_data.csv")
    
    # Print column names to debug after stripping whitespace
    print("Available columns (after stripping spaces):", combined_frame.columns.tolist())
    
    # Define the exact 32 AUs needed based on Data_cleaner.py
    required_au_columns = [
        'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r',
        'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r', 'AU17_r', 'AU20_r', 'AU25_r', 'AU26_r', 
        'AU45_r', 'AU01_c', 'AU02_c', 'AU04_c', 'AU05_c', 'AU06_c', 'AU07_c', 'AU09_c', 
        'AU10_c', 'AU12_c', 'AU14_c', 'AU15_c', 'AU20_c', 'AU23_c', 'AU25_c', 'AU26_c', 
        'AU28_c', 'AU45_c'
    ]
    
    # Check which of the required AUs are available in the data
    available_au_columns = [col for col in required_au_columns if col in combined_frame.columns]
    print(f"Found {len(available_au_columns)} of the required {len(required_au_columns)} AU columns")
    print("Missing AU columns:", set(required_au_columns) - set(available_au_columns))
    
    # For missing columns, create them with zeros to ensure we have all 32 required columns
    missing_columns = set(required_au_columns) - set(available_au_columns)
    for col in missing_columns:
        combined_frame[col] = 0.0
        print(f"Added missing column {col} with zeros")
    
    # Now all 32 required columns should be available
    all_au_columns = required_au_columns
    
    # Create a cleaned dataframe with ONLY the 32 AU columns (no frame or other columns)
    cleaned_df = combined_frame[all_au_columns]
    
    # Ensure all data is numeric
    for col in cleaned_df.columns:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
    
    # Fill any NaN values with 0
    cleaned_df = cleaned_df.fillna(0)
    
    # Ensure all data is float32 (standard for ML models)
    cleaned_df = cleaned_df.astype(np.float32)
    
    # Save the cleaned data with exactly 32 columns
    cleaned_df.to_csv("combined_data/cleaned_sample_data.csv", index=False, encoding='utf-8-sig')
    print(f"Cleaned data saved to combined_data/cleaned_sample_data.csv with exactly {len(cleaned_df.columns)} columns")
else:
    print("No data was processed. Check if CSV files exist in the specified directory.")

print("Processing complete!") 