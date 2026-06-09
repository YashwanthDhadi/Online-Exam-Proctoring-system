"""
ScreenshotCapture — saves violation evidence frames.
"""
import cv2
import os
from datetime import datetime


EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), '..', 'evidence')


def save_evidence_frame(frame, violation_type: str) -> str:
    """
    Save a CV2 frame as evidence image.
    Returns the saved file path, or '' on failure.
    """
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%H_%M_%S")
    safe_type = violation_type.replace(' ', '_').lower()
    filename = f"violation_{safe_type}_{ts}.png"
    filepath = os.path.join(EVIDENCE_DIR, filename)
    try:
        # Annotate frame
        annotated = frame.copy()
        label = f"VIOLATION: {violation_type.upper()}  {datetime.now().strftime('%H:%M:%S')}"
        cv2.putText(annotated, label, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1]-1, annotated.shape[0]-1),
                      (0, 0, 255), 3)
        cv2.imwrite(filepath, annotated)
        return filepath
    except Exception as e:
        print(f"[ScreenshotCapture] Error saving evidence: {e}")
        return ''
