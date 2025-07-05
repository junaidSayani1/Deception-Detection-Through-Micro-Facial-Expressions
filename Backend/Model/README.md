# LSTM Ensemble Deception Detector

This module provides an ensemble approach to deception detection using multiple LSTM models trained on facial action units.

## Files

- `ModelPredictor.py`: Script to run predictions on new action unit data, with chunk-wise output.
- `Models/`: Directory containing trained models and metadata.

## Using the Model Predictor

The `ModelPredictor.py` script allows you to analyze a CSV file containing frame-wise action units from a video to detect deceptive behavior over time.

### Command Line Usage

Basic usage:
```bash
python Model/ModelPredictor.py path/to/your_action_units.csv
```

Save the results to a CSV file:
```bash
python Model/ModelPredictor.py path/to/your_action_units.csv --output results.csv
```

Run without generating a plot:
```bash
python Model/ModelPredictor.py path/to/your_action_units.csv --no-plot
```

### Input Format

The input CSV file should contain action units in the same format as the training data, with each row representing a frame and each column representing different action unit values.

### Output

The script provides:
1. A CSV file with chunk-wise predictions (if `--output` is specified)
2. A visualization showing deception detection over time (unless `--no-plot` is used)
3. A summary of the analysis in the console output

### Understanding the Results

- Prediction values: 0 = truth, 1 = deception
- Confidence: Higher values indicate stronger consensus among ensemble models
- The visualization shows both predictions and confidence levels mapped against frame numbers

## Example

```python
from Model.ModelPredictor import EnsemblePredictor

# Initialize the predictor
predictor = EnsemblePredictor()

# Analyze a video
results = predictor.predict_from_csv('action_units.csv', output_file='results.csv')

# Or use it programmatically
X, timestamps, total_frames = predictor.preprocess_data('action_units.csv')
predictions, confidence = predictor.predict(X)
``` 