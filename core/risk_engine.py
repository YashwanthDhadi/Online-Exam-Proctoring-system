"""
RiskEngine — replaces FocusEngine.
Tracks violations and computes a cheating risk score.
"""
import time


class RiskEngine:
    def __init__(self):
        self.reset()

    # ── Violation tracking ─────────────────────────────────
    def record_violation(self, vtype):
        """
        vtypes: 'face_missing', 'multiple_faces', 'looking_away',
                'window_switch', 'inactivity'
        """
        self.violation_log.append({'type': vtype, 'time': time.time()})
        self.counts[vtype] = self.counts.get(vtype, 0) + 1

    # ── Called every monitoring tick ─────────────────────────
    def evaluate(self, face_present, face_count, looking_center,
                 window_active, activity_active):
        """
        Returns (status_label, color_hex)
        Records violations internally.
        """
        now = time.time()
        self.total_ticks += 1

        # Face missing
        if not face_present:
            if not self._face_missing_since:
                self._face_missing_since = now
            elif now - self._face_missing_since > 3:
                if now - self._last_violation_time.get('face_missing', 0) > 5:
                    self.record_violation('face_missing')
                    self._last_violation_time['face_missing'] = now
        else:
            self._face_missing_since = None

        # Multiple faces
        if face_count > 1:
            if now - self._last_violation_time.get('multiple_faces', 0) > 10:
                self.record_violation('multiple_faces')
                self._last_violation_time['multiple_faces'] = now

        # Looking away
        if face_present and not looking_center:
            if not self._looking_away_since:
                self._looking_away_since = now
            elif now - self._looking_away_since > 4:
                if now - self._last_violation_time.get('looking_away', 0) > 6:
                    self.record_violation('looking_away')
                    self._last_violation_time['looking_away'] = now
        else:
            self._looking_away_since = None

        # Window switch
        if not window_active:
            if not self._window_switch_since:
                self._window_switch_since = now
            elif now - self._window_switch_since > 2:
                if now - self._last_violation_time.get('window_switch', 0) > 8:
                    self.record_violation('window_switch')
                    self._last_violation_time['window_switch'] = now
        else:
            self._window_switch_since = None

        # Inactivity
        if not activity_active:
            if not self._inactive_since:
                self._inactive_since = now
            elif now - self._inactive_since > 30:
                if now - self._last_violation_time.get('inactivity', 0) > 30:
                    self.record_violation('inactivity')
                    self._last_violation_time['inactivity'] = now
        else:
            self._inactive_since = None

        risk = self.get_risk_score()
        if risk >= 50:
            return "High Risk", "#ff4757"
        elif risk >= 20:
            return "Medium Risk", "#f5a623"
        else:
            return "Low Risk", "#00d26a"

    # ── Risk score calculation ────────────────────────────
    def get_risk_score(self):
        c = self.counts
        score = (
            c.get('face_missing', 0) * 10 +
            c.get('window_switch', 0) * 5 +
            c.get('looking_away', 0) * 3 +
            c.get('multiple_faces', 0) * 15 +
            c.get('inactivity', 0) * 2
        )
        return score

    def get_risk_level(self):
        s = self.get_risk_score()
        if s >= 50:
            return "High"
        elif s >= 20:
            return "Medium"
        return "Low"

    def get_risk_color(self):
        lvl = self.get_risk_level()
        return {"High": "#ff4757", "Medium": "#f5a623", "Low": "#00d26a"}[lvl]

    def get_violation_counts(self):
        return dict(self.counts)

    def get_total_violations(self):
        return sum(self.counts.values())

    def reset(self):
        self.counts = {}
        self.violation_log = []
        self.total_ticks = 0
        self._face_missing_since = None
        self._looking_away_since = None
        self._window_switch_since = None
        self._inactive_since = None
        self._last_violation_time = {}
