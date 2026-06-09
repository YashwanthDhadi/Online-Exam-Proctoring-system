import os
import cv2
import time
from datetime import datetime

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), '..', 'evidence')


class ProctorEngine:

    WEIGHT_FACE_MISSING = 10
    WEIGHT_WINDOW_SWITCH = 5
    WEIGHT_LOOKING_AWAY = 3
    WEIGHT_MULTIPLE_FACES = 15
    WEIGHT_INACTIVITY = 2

    # Better demo thresholds
    FACE_MISSING_THRESHOLD = 5
    LOOKING_AWAY_THRESHOLD = 8
    INACTIVITY_THRESHOLD_SECS = 20

    def __init__(self):
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        self.reset()

    def evaluate(self, face_present, face_count,
                 looking_center, window_active,
                 activity_active, frame=None):

        self.total_frames += 1
        now = time.time()

        # FACE MISSING
        if not face_present:
            self._face_missing_streak += 1
            if self._face_missing_streak >= self.FACE_MISSING_THRESHOLD:
                self.violations['face_missing'] += 1
                self._save_evidence(frame, 'face_missing')
                self._face_missing_streak = 0
        else:
            self._face_missing_streak = 0

        # MULTIPLE FACES
        if face_count > 1:
            self.violations['multiple_faces'] += 1
            self._save_evidence(frame, 'multiple_faces')

        # LOOKING AWAY
        if face_present and not looking_center:
            self._looking_away_streak += 1
            if self._looking_away_streak >= self.LOOKING_AWAY_THRESHOLD:
                self.violations['looking_away'] += 1
                self._save_evidence(frame, 'looking_away')
                self._looking_away_streak = 0
        else:
            self._looking_away_streak = 0

        # WINDOW SWITCH
        if not window_active:
            if not self._window_was_inactive:
                self.violations['window_switch'] += 1
                self._save_evidence(frame, 'window_switch')
            self._window_was_inactive = True
        else:
            self._window_was_inactive = False

        # LONG INACTIVITY
        if not activity_active:
            if self._inactivity_start is None:
                self._inactivity_start = now
            elif now - self._inactivity_start >= self.INACTIVITY_THRESHOLD_SECS:
                if not self._inactivity_logged:
                    self.violations['inactivity'] += 1
                    self._inactivity_logged = True
        else:
            self._inactivity_start = None
            self._inactivity_logged = False

        risk = self._calc_risk()

        if risk < 20:
            status, color = "Low Risk", "#00d26a"
        elif risk < 50:
            status, color = "Medium Risk", "#f5a623"
        else:
            status, color = "High Risk", "#ff4757"

        return {
            'status': status,
            'color': color,
            'risk_score': risk,
            'violations': dict(self.violations),
        }

    def get_risk_score(self):
        return self._calc_risk()

    def get_risk_level(self):
        r = self._calc_risk()
        if r < 20:
            return "Low"
        elif r < 50:
            return "Medium"
        return "High"

    def get_evidence_files(self):
        return sorted(self._evidence_files)

    def reset(self):
        self.violations = {
            'face_missing': 0,
            'multiple_faces': 0,
            'looking_away': 0,
            'window_switch': 0,
            'inactivity': 0,
        }

        self.total_frames = 0
        self._evidence_files = []

        self._face_missing_streak = 0
        self._looking_away_streak = 0
        self._window_was_inactive = False

        self._inactivity_start = None
        self._inactivity_logged = False

    def _calc_risk(self):
        v = self.violations
        return (
            v['face_missing'] * self.WEIGHT_FACE_MISSING +
            v['window_switch'] * self.WEIGHT_WINDOW_SWITCH +
            v['looking_away'] * self.WEIGHT_LOOKING_AWAY +
            v['multiple_faces'] * self.WEIGHT_MULTIPLE_FACES +
            v['inactivity'] * self.WEIGHT_INACTIVITY
        )

    def _save_evidence(self, frame, label):
        if frame is None:
            return

        ts = datetime.now().strftime("%H_%M_%S")

        fname = f"violation_{label}_{ts}.png"
        path = os.path.join(EVIDENCE_DIR, fname)

        try:
            cv2.imwrite(path, frame)
            self._evidence_files.append(path)
        except:
            pass