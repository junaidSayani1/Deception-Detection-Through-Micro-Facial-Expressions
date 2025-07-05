import os
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import cv2

class ReportGenerator:
    def __init__(self, reports_dir="Reports"):
        
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
        # Define colors (RGB)
        self.primary_color = (41, 128, 185)  # Blue
        self.secondary_color = (52, 152, 219)  # Light Blue
        self.accent_color = (231, 76, 60)  # Red
        self.text_color = (44, 62, 80)  # Dark Gray
        self.light_gray = (236, 240, 241)  # Light Gray
    
    def extract_face_from_video(self, video_path):
        face_dir = os.path.join(self.reports_dir, "faces")
        os.makedirs(face_dir, exist_ok=True)
        
        # Output path for the face image
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        face_image_path = os.path.join(face_dir, f"{video_name}_face.jpg")
        
        # Load face detector from OpenCV
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return None
        
        # Initialize variables to track the best face
        best_face_frame = None
        best_face_size = 0
        face_detection_interval = 30  # Process every 30th frame to save time
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process only every N frames to save time
            if frame_count % face_detection_interval == 0:
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                # Find the largest face in this frame
                for (x, y, w, h) in faces:
                    face_size = w * h
                    if face_size > best_face_size:
                        # This is now our best face
                        best_face_size = face_size
                        best_face_frame = frame.copy()
        
        cap.release()
        
        # If we found a good face, save it
        if best_face_frame is not None:
            cv2.imwrite(face_image_path, best_face_frame)
            print(f"Best face extracted and saved to {face_image_path}")
            return face_image_path
        else:
            print("No good face found in the video")
            return None
    
    def create_header(self, pdf):
        """Create a professional header with logo and title"""
        # Add logo (if you have one)
        # pdf.image('logo.png', 10, 10, 30)
        
        # Add title with custom color
        pdf.set_text_color(*self.primary_color)
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 20, "Deception Analysis Report", 0, 1, "C")
        
        # Add decorative line
        pdf.set_draw_color(*self.secondary_color)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(10)
    
    def create_footer(self, pdf):
        """Create a footer with page numbers"""
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(*self.text_color)
        pdf.cell(0, 10, f"Page {pdf.page_no()}", 0, 0, "C")
    
    def add_section_title(self, pdf, title):
        """Add a section title with custom styling"""
        pdf.ln(5)
        pdf.set_text_color(*self.primary_color)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, title, 0, 1)
        pdf.set_text_color(*self.text_color)
        pdf.set_font("Arial", "", 12)
    
    def add_info_box(self, pdf, title, content):
        """Add an information box with custom styling"""
        # Set fixed margin and width
        x = 10
        y = pdf.get_y()
        box_width = pdf.w - 20  # 10mm margin on both sides
        box_height = 20
        
        # Draw box background
        pdf.set_fill_color(*self.light_gray)
        pdf.rect(x, y, box_width, box_height, style='F')
        
        # Add title and content
        pdf.set_text_color(*self.primary_color)
        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(x + 5, y + 5)
        pdf.cell(box_width - 10, 5, title, 0, 1)
        
        pdf.set_text_color(*self.text_color)
        pdf.set_font("Arial", "", 12)
        pdf.set_xy(x + 5, y + 12)
        pdf.cell(box_width - 10, 5, content, 0, 1)
        
        pdf.ln(5)
    
    def generate_report(self, file_path, results=None, analysis_image_path="deception_analysis.png"):
        # Extract face from the video file
        face_image_path = self.extract_face_from_video(file_path)
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"deception_report_{timestamp}.pdf"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # Create PDF with FPDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set default text color
        pdf.set_text_color(*self.text_color)
        
        # Create header
        self.create_header(pdf)
        
        # Define face width and position
        face_width = 40  # Width in mm
        face_x = pdf.w - face_width - 20  # 20mm from right margin
        face_height = face_width  # Assuming square proportions for estimation
        
        # Calculate content width to avoid face overlap
        content_width = face_x - 20  # 10mm from left margin + 10mm buffer
        
        # Add face image in top right if available
        if face_image_path and os.path.exists(face_image_path):
            # Position the face image in the top right
            pdf.image(face_image_path, x=face_x, y=30, w=face_width)
            
            # Add a label for the face image
            pdf.set_xy(face_x, 30 + face_width + 2)
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(*self.secondary_color)
            pdf.cell(face_width, 5, "Subject", 0, 1, "C")
        
        # Add timestamp - adjusted width to avoid face overlap
        pdf.set_text_color(*self.text_color)
        pdf.set_font("Arial", "", 12)
        
        # Custom info box that doesn't overlap with face
        y = pdf.get_y()
        pdf.set_fill_color(*self.light_gray)
        pdf.rect(10, y, content_width, 20, style='F')
        
        pdf.set_text_color(*self.primary_color)
        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(15, y + 5)
        pdf.cell(content_width - 10, 5, "Report Information", 0, 1)
        
        pdf.set_text_color(*self.text_color)
        pdf.set_font("Arial", "", 12)
        pdf.set_xy(15, y + 12)
        pdf.cell(content_width - 10, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        
        pdf.ln(10)
        
        # Add video file information - adjusted width to avoid face overlap
        self.add_section_title(pdf, "Video Information")
        
        y = pdf.get_y()
        pdf.set_fill_color(*self.light_gray)
        pdf.rect(10, y, content_width, 20, style='F')
        
        pdf.set_text_color(*self.primary_color)
        pdf.set_font("Arial", "B", 12)
        pdf.set_xy(15, y + 5)
        pdf.cell(content_width - 10, 5, "File Details", 0, 1)
        
        pdf.set_text_color(*self.text_color)
        pdf.set_font("Arial", "", 12)
        pdf.set_xy(15, y + 12)
        pdf.cell(content_width - 10, 5, f"File: {os.path.basename(file_path)}", 0, 1)
        
        pdf.ln(10)
        
        # Add deception analysis graph
        if os.path.exists(analysis_image_path):
            self.add_section_title(pdf, "Deception Analysis Results")
            
            # Add graph with border and caption
            pdf.set_draw_color(*self.secondary_color)
            pdf.set_line_width(0.5)
            graph_y = pdf.get_y()
            pdf.image(analysis_image_path, x=10, y=graph_y, w=190)
            pdf.rect(10, graph_y, 190, 100)  # Draw border around graph
            
            # Add caption
            pdf.set_text_color(*self.secondary_color)
            pdf.set_font("Arial", "I", 10)
            pdf.set_xy(10, graph_y + 102)
            pdf.cell(0, 5, "Figure 1: Deception Analysis Timeline", 0, 1, "C")
        else:
            pdf.set_text_color(*self.accent_color)
            pdf.cell(0, 10, f"Error: Deception analysis graph not found at {analysis_image_path}.", 0, 1)
        
        # Add additional result information if available
        if results is not None:
            # Start summary on a new page (second page)
            pdf.add_page()
            self.add_section_title(pdf, "Analysis Summary")
            
            if isinstance(results, dict):
                # Create a table for dictionary results
                pdf.set_fill_color(*self.light_gray)
                pdf.set_text_color(*self.primary_color)
                pdf.set_font("Arial", "B", 12)
                
                # Table header
                pdf.cell(95, 10, "Metric", 1, 0, "C", True)
                pdf.cell(95, 10, "Value", 1, 1, "C", True)
                
                # Table content
                pdf.set_text_color(*self.text_color)
                pdf.set_font("Arial", "", 12)
                for key, value in results.items():
                    if isinstance(value, (int, float)):
                        value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
                    else:
                        value_str = str(value)
                    
                    pdf.cell(95, 10, key, 1, 0)
                    pdf.cell(95, 10, value_str, 1, 1)
            
            elif isinstance(results, pd.DataFrame):
                # Create a summary table for DataFrame results
                pdf.set_fill_color(*self.light_gray)
                pdf.set_text_color(*self.primary_color)
                pdf.set_font("Arial", "B", 12)
                
                # Calculate summary statistics
                truthful_percent = (results['Deception_Score'] < 0.5).mean() * 100
                deceptive_percent = (results['Deception_Score'] >= 0.5).mean() * 100
                avg_score = results['Deception_Score'].mean()
                
                # Create summary table
                pdf.cell(95, 10, "Metric", 1, 0, "C", True)
                pdf.cell(95, 10, "Value", 1, 1, "C", True)
                
                # Add summary statistics with custom styling
                pdf.set_text_color(*self.text_color)
                pdf.set_font("Arial", "", 12)
                
                # Add rows with alternating background colors
                metrics = [
                    ("Truthful Periods", f"{truthful_percent:.1f}%"),
                    ("Deceptive Periods", f"{deceptive_percent:.1f}%"),
                    ("Average Deception Score", f"{avg_score:.2f}")
                ]
                
                for i, (metric, value) in enumerate(metrics):
                    pdf.set_fill_color(*self.light_gray if i % 2 == 0 else (255, 255, 255))
                    pdf.cell(95, 10, metric, 1, 0, "", True)
                    pdf.cell(95, 10, value, 1, 1, "", True)
                
                if 'Confidence' in results.columns:
                    avg_confidence = results['Confidence'].mean()
                    pdf.set_fill_color(*self.light_gray)
                    pdf.cell(95, 10, "Average Confidence", 1, 0, "", True)
                    pdf.cell(95, 10, f"{avg_confidence:.2f}", 1, 1, "", True)
        
        # Add footer to all pages
        #self.create_footer(pdf)
        
        # Save the PDF
        pdf.output(report_path)
        
        print(f"Report generated: {report_path}")
        return report_path


if __name__ == "__main__":
    # Example usage
    generator = ReportGenerator()
    report_path = generator.generate_report(
        file_path="example_video.mp4",
        results={"Truthful periods": "65.2%", "Deceptive periods": "34.8%", "Average score": 0.42}
    )
    print(f"Example report saved to: {report_path}") 