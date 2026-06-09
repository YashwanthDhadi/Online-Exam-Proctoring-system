import cv2


class Camera:
    def __init__(self):
        self.cap = None
        self.available = False
        self._try_open()

    def _try_open(self):
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.cap = cap
                self.available = True
            else:
                cap.release()
        except Exception:
            self.available = False

    def get_frame(self):
        if not self.available or self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.available = False

    def enable(self):
        if not self.available:
            self._try_open()
        return self.available

    def disable(self):
        self.release()
