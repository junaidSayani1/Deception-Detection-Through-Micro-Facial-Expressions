import cv2
import torch
import os
import subprocess
import shutil

# Check if GPU is available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Function to extract frame chunks, feed to AU generator, and clear memory
def extract_and_process_chunks(video_path, chunk_size, temp_img_folder, openface_executable, output_folder):
    cap = cv2.VideoCapture(video_path)
    frames = []
    chunk_index = 0  # Initialize chunk index for naming CSV files
    
    if not cap.isOpened():
        print(f"Error opening video file {video_path}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to a torch tensor and move to GPU
        frame_tensor = torch.tensor(frame).to(device)
        frames.append(frame_tensor)

        # If we have collected a full chunk of frames, process it
        if len(frames) == chunk_size:
            # Process the chunk for AU extraction and save each result in a single CSV with a unique name
            csv_filename = f"{os.path.basename(video_path)}_chunk_{chunk_index}.csv"
            process_chunk_for_AUs(frames, temp_img_folder, openface_executable, output_folder, csv_filename)
            frames = []  # Clear frames list for the next chunk
            chunk_index += 1

    cap.release()

# Function to convert frames to images and run AU extraction
def process_chunk_for_AUs(frames, temp_img_folder, openface_executable, output_folder, csv_filename):
    # Ensure the temporary image folder exists
    os.makedirs(temp_img_folder, exist_ok=True)
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Convert frames to images and save temporarily
    for i, frame in enumerate(frames):
        frame_cpu = frame.cpu().numpy()
        image_path = os.path.join(temp_img_folder, f"frame_{i}.jpg")
        cv2.imwrite(image_path, frame_cpu)

    # Run OpenFace on the images in temp_img_folder and directly save to the output folder
    csv_output_path = os.path.join(output_folder, csv_filename)
    
    # Windows command needs quotes around paths with spaces
    # Using a different approach to avoid nested directory creation
    # We provide the full output_dir but specify only the filename for -of parameter
    openface_command = f"\"{os.path.abspath(openface_executable)}\" -fdir \"{os.path.abspath(temp_img_folder)}\" -out_dir \"{os.path.abspath(output_folder)}\" -of \"{csv_filename}\""
    
    print(f"Running command: {openface_command}")
    subprocess.call(openface_command, shell=True)
    
    # After OpenFace runs, check if the file was created with the expected path
    # If not, it might have been created in a subdirectory, so try to find and move it
    expected_csv = os.path.join(output_folder, csv_filename)
    if not os.path.exists(expected_csv):
        # Check if file was created in a nested directory
        possible_nested_path = os.path.join(output_folder, output_folder, csv_filename)
        if os.path.exists(possible_nested_path):
            # Move the file to the correct location
            shutil.move(possible_nested_path, expected_csv)
            print(f"Moved file from nested directory to {expected_csv}")
            
            # Remove the empty nested directory if it exists
            nested_dir = os.path.join(output_folder, output_folder)
            if os.path.exists(nested_dir) and os.path.isdir(nested_dir):
                if not os.listdir(nested_dir):  # Check if directory is empty
                    os.rmdir(nested_dir)
                    print(f"Removed empty nested directory {nested_dir}")

    # Clean up the temporary images
    for img_file in os.listdir(temp_img_folder):
        os.remove(os.path.join(temp_img_folder, img_file))
    
    # Free up GPU memory if using CUDA
    if torch.cuda.is_available():
        torch.cuda.empty_cache()