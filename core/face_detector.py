import cv2
import mediapipe as mp


class FaceDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mesh = self.mp_face_mesh.FaceMesh(
            refine_landmarks=True,
            max_num_faces=4
        )

        # detection thresholds
        self.eye_threshold = 8
        self.head_threshold = 20

        self._frame_count = 0

        # returns: (face_present, face_count, looking_center, head_turn)
        self._last_result = (False, 0, False, False)

    def calibrate(self, frame):
        """
        Calibrates eye center offset for more accurate gaze detection
        """
        small = cv2.resize(frame, (320, 240))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self.mesh.process(rgb)

        if not results.multi_face_landmarks:
            return False

        face_landmarks = results.multi_face_landmarks[0]

        h, w = 240, 320

        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        nose = face_landmarks.landmark[1]

        left_eye_x = int(left_eye.x * w)
        right_eye_x = int(right_eye.x * w)
        nose_x = int(nose.x * w)

        eye_center = (left_eye_x + right_eye_x) // 2

        offset = abs(eye_center - nose_x)

        # smaller adaptive thresholds
        self.eye_threshold = offset + 4
        self.head_threshold = offset + 12

        return True

    def detect(self, frame):
        """
        Returns:
        (face_present: bool,
         face_count: int,
         looking_center: bool,
         head_turn: bool)
        """

        # run detection every frame (better reliability)
        small = cv2.resize(frame, (320, 240))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        results = self.mesh.process(rgb)

        if not results.multi_face_landmarks:
            self._last_result = (False, 0, False, False)
            return self._last_result

        face_count = len(results.multi_face_landmarks)

        face_landmarks = results.multi_face_landmarks[0]

        h, w = 240, 320

        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        nose = face_landmarks.landmark[1]

        left_eye_x = int(left_eye.x * w)
        right_eye_x = int(right_eye.x * w)
        nose_x = int(nose.x * w)

        eye_center = (left_eye_x + right_eye_x) // 2

        offset = abs(eye_center - nose_x)

        looking_center = offset < self.eye_threshold
        head_turn = offset > self.head_threshold

        self._last_result = (True, face_count, looking_center, head_turn)

        return self._last_result