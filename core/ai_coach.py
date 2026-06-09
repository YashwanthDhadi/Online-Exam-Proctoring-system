"""
ai_coach.py
Generates rule-based exam integrity summaries without any external API.
"""


class AICoach:
    def __init__(self, api_key=""):
        # API key not used — kept for compatibility
        self.available = False

    def set_api_key(self, key):
        pass  # No API used

    def generate_exam_summary(self, student_id, exam_id, duration_mins,
                               violations: dict, risk_level: str) -> str:
        """
        Generates a professional rule-based summary of the exam integrity session.
        """
        return self._fallback_exam_summary(violations, risk_level, duration_mins)

    def _fallback_exam_summary(self, violations, risk_level, duration_mins):
        fm  = violations.get('face_missing', 0)
        mf  = violations.get('multiple_faces', 0)
        la  = violations.get('looking_away', 0)
        ws  = violations.get('window_switch', 0)
        ina = violations.get('inactivity', 0)
        total = fm + mf + la + ws + ina

        if total == 0:
            return (f"The student completed the {duration_mins}-minute exam with no detected violations. "
                    f"Camera presence was maintained throughout and no suspicious activity was observed. "
                    f"The session has been assessed as {risk_level} Risk.")

        parts = []
        if fm:  parts.append(f"face was missing {fm} time(s)")
        if mf:  parts.append(f"multiple faces were detected {mf} time(s)")
        if la:  parts.append(f"the student looked away {la} time(s)")
        if ws:  parts.append(f"window switching occurred {ws} time(s)")
        if ina: parts.append(f"extended inactivity was noted {ina} time(s)")

        summary = ", ".join(parts)
        return (f"During the {duration_mins}-minute exam session, the monitoring system detected "
                f"the following: {summary}. "
                f"The overall integrity assessment is {risk_level} Risk. "
                f"Evidence screenshots have been saved for review.")
