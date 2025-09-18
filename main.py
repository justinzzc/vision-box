import cv2
import supervision as sv
from ultralytics import YOLO

image = cv2.imread("true.jpg")
model = YOLO("yolov8s.pt")
result = model(image)[0]
detections = sv.Detections.from_ultralytics(result)

annotated_frame = image.copy()

box_annotator = sv.BoxAnnotator()
annotated_frame = box_annotator.annotate(
  scene=image.copy(),
  detections=detections)

# labels = [
#     # f"{class_name} {confidence:.2f}"
#     f"{class_name}"
#     for class_name, confidence
#     in zip(detections['class_name'], detections.confidence)
# ]
# label_annotator = sv.LabelAnnotator(text_position=sv.Position.BOTTOM_CENTER)
# annotated_frame = label_annotator.annotate(
#     scene=annotated_frame,
#     detections=detections,
#     labels=labels)

cv2.imshow("annotated_frame", annotated_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()