import cv2

filePath = "Videos/me.mp4"
cap = cv2.VideoCapture(filePath)
fps = cap.get(cv2.CAP_PROP_FPS)
cap.release()
print(f"Video frame rate: {fps} FPS")