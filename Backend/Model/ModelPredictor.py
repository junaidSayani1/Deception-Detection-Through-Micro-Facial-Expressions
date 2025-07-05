import numpy as np
import pandas as pd
import tensorflow as tf
import pickle
import os
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model

class EnsemblePredictor:
    def __init__(self, model_dir='Model/Models/'):
        # Load ensemble metadata
        with open(os.path.join(model_dir, 'ensemble_metadata.pkl'), 'rb') as f:
            self.metadata = pickle.load(f)
        
        # Load models
        self.models = []
        for path in self.metadata['model_paths']:
            model_path = os.path.join(model_dir, path)
            model = load_model(model_path)
            self.models.append(model)
        
        self.s_size = self.metadata['s_size']  # chunk size from training
        print(f"Loaded {len(self.models)} models with chunk size {self.s_size}")
    
    def preprocess_data(self, csv_file):
        """Process input CSV file to match model input format"""
        # Read the action units data
        data = pd.read_csv(csv_file, skipinitialspace=True)
        
        # Print initial data info
        print(f"\n=== Input Data Info ===")
        print(f"Total rows: {len(data)}")
        print(f"Columns: {data.columns.tolist()}")
        
        # Validate data format
        if 'frame' in data.columns:
            data = data.sort_values('frame')  # Ensure frames are in order
            print(f"Frames range: {data['frame'].min()} to {data['frame'].max()}")
        
        # Convert to numpy array (excluding header if necessary)
        first_row_check = pd.to_numeric(data.iloc[0], errors='coerce')
        if not first_row_check.notnull().all():
            data = data[1:]
        
        # Extract only AU columns if they exist
        au_columns = [col for col in data.columns if col.startswith('AU')]
        if not au_columns:
            raise ValueError("No Action Unit columns found in the CSV file")
        
        print(f"Number of AU features: {len(au_columns)}")
        print(f"AU columns: {au_columns}")
        
        data = data[au_columns].values
        
        # Verify chunk size
        if self.s_size != 30:
            print(f"Warning: Expected chunk size of 30 frames, but got {self.s_size}")
        
        # Reshape data into chunks of size s_size
        total_frames = len(data)
        num_chunks = total_frames // self.s_size
        remainder = total_frames % self.s_size
        
        print(f"\n=== Chunking Info ===")
        print(f"Total frames: {total_frames}")
        print(f"Chunk size: {self.s_size}")
        print(f"Number of complete chunks: {num_chunks}")
        print(f"Remaining frames: {remainder}")
        
        chunks = []
        timestamps = []
        
        # Create overlapping chunks for better temporal analysis
        for i in range(num_chunks):
            start_idx = i * self.s_size
            end_idx = (i + 1) * self.s_size
            chunk = data[start_idx:end_idx]
            
            # Validate chunk shape
            if chunk.shape[0] != self.s_size:
                print(f"Warning: Chunk {i} has incorrect shape: {chunk.shape}")
                continue
                
            chunks.append(chunk)
            timestamps.append(start_idx + self.s_size // 2)
        
        # Handle remaining frames
        if remainder > 0:
            last_chunk = data[-remainder:]
            # Pad with zeros to reach s_size
            padding = np.zeros((self.s_size - remainder, data.shape[1]))
            padded_chunk = np.vstack((last_chunk, padding))
            chunks.append(padded_chunk)
            timestamps.append(total_frames - remainder // 2)
        
        # Convert list of chunks to a 3D numpy array
        X = np.array(chunks)
        
        print(f"\n=== Final Output Shape ===")
        print(f"Input shape: {X.shape}")
        print(f"Number of chunks: {len(chunks)}")
        print(f"Timestamps: {timestamps}")
        
        return X, timestamps, total_frames
    
    def predict(self, X, deception_threshold=0.5):
        """Make predictions using ensemble models"""
        # Store raw probabilities from each model
        raw_probabilities = np.zeros((len(X), len(self.models)))
        
        # Get predictions from each model
        for i, model in enumerate(self.models):
            # Get raw probability scores
            pred_prob = model.predict(X, verbose=0).flatten()
            raw_probabilities[:, i] = pred_prob
        print("The raw probabilities are:")
        print(raw_probabilities)
        # Calculate deception score: average of all model probabilities
        deception_score = np.mean(raw_probabilities, axis=1)
        
        # Calculate binary predictions based on average probability
        binary_predictions = (deception_score > deception_threshold).astype(int)
        
        # Calculate confidence based on distance from 0.5 (most uncertain)
        confidence = 2 * np.abs(deception_score - 0.5)
        
        return deception_score, binary_predictions, confidence
    
    def predict_from_csv(self, csv_file, output_file=None, plot=True, fps=30, deception_threshold=0.5):
        """Run the full prediction pipeline on a CSV file"""
        # Preprocess data
        X, timestamps, total_frames = self.preprocess_data(csv_file)
        
        # Make predictions
        deception_score, binary_predictions, confidence = self.predict(X, deception_threshold)
        
        # Convert frames to seconds
        timestamp_seconds = [t / fps for t in timestamps]
        total_seconds = total_frames / fps
        
        # Create results DataFrame
        results = pd.DataFrame({
            'Chunk_Start_Frame': [t - self.s_size // 2 for t in timestamps],
            'Chunk_End_Frame': [min(t + self.s_size // 2, total_frames) for t in timestamps],
            'Chunk_Start_Time': [(t - self.s_size // 2) / fps for t in timestamps],
            'Chunk_End_Time': [min(t + self.s_size // 2, total_frames) / fps for t in timestamps],
            'Frame': timestamps,
            'Time_Seconds': timestamp_seconds,
            'Deception_Score': deception_score,  # [0,1] scale
            'Binary_Prediction': binary_predictions,  # 0: truth, 1: deception
            'Confidence': confidence
        })
        
        # Save results if output file is specified
        if output_file:
            results.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")
        
        # Plot results if requested
        if plot:
            self.plot_results(results, total_frames, total_seconds, fps, deception_threshold)
        
        # Store the total_frames for summary output
        self.total_frames = total_frames
        self.total_seconds = total_seconds
        
        return results
    
    def plot_results(self, results, total_frames, total_seconds, fps=30, deception_threshold=0.5):
        """Plot only the polygraph-style deception score graph"""
        plt.figure(figsize=(15, 6), facecolor='#f9f9f9')
        
        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Plot deception score (polygraph style)
        plt.plot(results['Time_Seconds'], results['Deception_Score'], color='#3366cc', linewidth=2.5)
        plt.axhline(y=deception_threshold, color='#e74c3c', linestyle='--', alpha=0.6, linewidth=1.5)  # Reference line at threshold
        
        # Fill areas with more pleasing colors
        plt.fill_between(results['Time_Seconds'], deception_threshold, results['Deception_Score'], 
                         where=(results['Deception_Score'] > deception_threshold), color='#ff9999', alpha=0.4)
        plt.fill_between(results['Time_Seconds'], deception_threshold, results['Deception_Score'], 
                         where=(results['Deception_Score'] <= deception_threshold), color='#99cc99', alpha=0.4)
        
        # Adjust y-axis to show full [0,1] range with some padding
        plt.ylim(-0.05, 1.05)  
        plt.xlim(0, total_seconds)
        
        # Improve title and labels
        plt.title('Deception Analysis', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Time (seconds)', fontsize=12, labelpad=10)
        plt.ylabel('Deception Score', fontsize=12, labelpad=10)
        
        # Customize grid
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # Add secondary x-axis for frame numbers
        ax1 = plt.gca()
        ax2 = ax1.twiny()
        ax2.set_xlim(0, total_frames)
        ax2.set_xlabel('Frame Number', fontsize=12, labelpad=10)
        
        # Add legend for threshold
        plt.legend(['Deception Score', f'Threshold ({deception_threshold})'], 
                  loc='upper right', frameon=True, framealpha=0.9)
        
        plt.tight_layout()
        plt.savefig('deception_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Analysis plot saved as 'deception_analysis.png'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run deception detection on action unit data")
    parser.add_argument("input_csv", help="Path to the CSV file with action unit data")
    parser.add_argument("--output", "-o", help="Path to save prediction results CSV")
    parser.add_argument("--no-plot", action="store_true", help="Disable plotting")
    parser.add_argument("--fps", type=float, default=30.0, help="Frames per second of the original video (default: 30)")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="Threshold for deception classification (default: 0.5)")
    
    args = parser.parse_args()
    
    predictor = EnsemblePredictor()
    results = predictor.predict_from_csv(
        args.input_csv, 
        output_file=args.output,
        plot=not args.no_plot,
        fps=args.fps,
        deception_threshold=args.threshold
    )
    
    # Calculate percentages of time spent in each category based on deception score
    truthful_percent = (results['Deception_Score'] < args.threshold).mean() * 100
    deceptive_percent = (results['Deception_Score'] >= args.threshold).mean() * 100
    
    # Also calculate statistics based on traditional binary predictions
    binary_truth_percent = (results['Binary_Prediction'] == 0).mean() * 100
    binary_deception_percent = (results['Binary_Prediction'] == 1).mean() * 100
    
    print("\n=== Analysis Summary ===")
    print(f"Total frames analyzed: {len(results['Deception_Score']) * predictor.s_size}")
    print(f"Total video duration: {predictor.total_seconds:.2f} seconds")
    print(f"\nUsing threshold: {args.threshold}")
    print(f"Based on Continuous Deception Score [0 to 1]:")
    print(f"Truthful periods (score < {args.threshold}): {truthful_percent:.1f}% of frames")
    print(f"Deceptive periods (score >= {args.threshold}): {deceptive_percent:.1f}% of frames")
    print(f"Average deception score: {results['Deception_Score'].mean():.2f}")
    print("\nBased on Binary Classification:")
    print(f"Truth classification: {binary_truth_percent:.1f}% of frames")
    print(f"Deception classification: {binary_deception_percent:.1f}% of frames")
    print(f"Average confidence: {results['Confidence'].mean():.2f}") 