from Model.ModelPredictor import EnsemblePredictor
from Model.PreProcessing.AUsGenerator import extract_and_process_chunks
import os
import shutil
import glob
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()


class DeceptionDetector:
    def __init__(self):
        # Create necessary directories
        os.makedirs("temp_image", exist_ok=True)
        os.makedirs("AU_output", exist_ok=True)
        os.makedirs("combined_data", exist_ok=True)
        
        # OpenFace path for Windows
        self.openface_executable = os.getenv("OPENFACE_PATH")
        
    def process_video(self, video_path, cleanup=True):
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return None
        
        try:
            # Clear previous AU_output contents to prevent duplication
            self._clear_directory("AU_output")
            
            # Step 1: Extract Action Units from video using OpenFace
            print(f"Step 1: Extracting Action Units from {video_path}")
            extract_and_process_chunks(
                video_path=video_path,
                chunk_size=30,
                temp_img_folder="temp_image",
                openface_executable=self.openface_executable,
                output_folder="AU_output"  # This will be used as the base directory, no nesting
            )
            print("Action Units extraction complete")
            
            # Step 2: Combine AU files
            print("Step 2: Combining extracted Action Units")
            self._combine_and_clean_aus()
            
            # Step 3: Run prediction using the ensemble model
            print("Step 3: Running deception detection")
            data_file = "combined_data/cleaned_sample_data.csv"
            
            # Initialize the predictor
            print("Initializing deception predictor...")
            predictor = EnsemblePredictor()
            
            # Run prediction on the cleaned data
            print(f"Running prediction on {data_file}...")
            results = predictor.predict_from_csv(
                data_file, 
                output_file="prediction_results.csv",
                plot=True,
                fps=30
            )
            
            print("Analysis complete!")
            print("- Visualization saved as 'deception_analysis.png'")
            print("- Detailed results saved as 'prediction_results.csv'")
            
            # Delete the folders after processing if cleanup is True
            if cleanup:
                self._cleanup_temp_folders()
            
            return results
            
        except Exception as e:
            print(f"Error during processing: {e}")
            raise e
    
    def _clear_directory(self, directory):
        """Clear contents of directory without removing the directory itself"""
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            print(f"Cleared contents of {directory}")
    
    def _combine_and_clean_aus(self):
        au_path = 'AU_output'  # No 'r' prefix to avoid raw string problems
        
        # Get all CSV files from the output directory
        csv_files = glob.glob(os.path.join(au_path, "*.csv"))
        print(f"Found {len(csv_files)} AU files")
        
        # Sort files by chunk number
        def get_chunk_number(filename):
            # Extract chunk number from filename (assuming format like "chunk_0.csv", "chunk_1.csv", etc.)
            try:
                return int(filename.split('chunk_')[1].split('.')[0])
            except:
                return float('inf')  # Put files without chunk numbers at the end
        
        csv_files.sort(key=get_chunk_number)
        print("Files will be processed in order:", [os.path.basename(f) for f in csv_files])
        
        # Create a list to store dataframes
        au_data = []
        file_count = 0
        
        # Process each CSV file
        for filename in csv_files:
            # Read the CSV file
            df = pd.read_csv(filename, index_col=None, header=0)
            
            # Add metadata
            df['id'] = file_count
            file_count += 1
            df['label'] = "sample"
            
            # Add to the list
            au_data.append(df)
            print(f"Processed {filename}")
        
        # Combine all dataframes
        if not au_data:
            raise Exception("No data was processed. Check if CSV files exist in the output directory.")
            
        # Concatenate all dataframes
        combined_frame = pd.concat(au_data, axis=0, ignore_index=True)
        
        # Clean up column names by stripping whitespace
        combined_frame.columns = combined_frame.columns.str.strip()
        
        # Save the combined data
        if not os.path.exists("combined_data"):
            os.makedirs("combined_data")
        combined_frame.to_csv("combined_data/combined_sample_data.csv", index=False, encoding='utf-8-sig')
        print(f"Combined data saved to combined_data/combined_sample_data.csv")
        
        # Define the exact 32 AUs needed
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
        
        # For missing columns, create them with zeros
        missing_columns = set(required_au_columns) - set(available_au_columns)
        for col in missing_columns:
            combined_frame[col] = 0.0
            print(f"Added missing column {col} with zeros")
        
        # Create a cleaned dataframe with ONLY the 32 AU columns
        cleaned_df = combined_frame[required_au_columns]
        
        # Ensure all data is numeric
        for col in cleaned_df.columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Fill any NaN values with 0
        cleaned_df = cleaned_df.fillna(0)
        
        # Ensure all data is float32 (standard for ML models)
        cleaned_df = cleaned_df.astype(np.float32)
        
        # Save the cleaned data
        cleaned_df.to_csv("combined_data/cleaned_sample_data.csv", index=False, encoding='utf-8-sig')
        print(f"Cleaned data saved to combined_data/cleaned_sample_data.csv with exactly {len(cleaned_df.columns)} columns")
    
    def _cleanup_temp_folders(self):
        """
        Delete temporary folders created during processing
        """
        print("Cleaning up temporary folders...")
        if os.path.exists("AU_output"):
            shutil.rmtree("AU_output")
            print("- AU_output folder deleted")
        
        if os.path.exists("combined_data"):
            shutil.rmtree("combined_data")
            print("- combined_data folder deleted")
