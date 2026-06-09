from pynput import keyboard, mouse
import time


class ActivityTracker:
    """
    Tracks keyboard and mouse activity during the exam.
    Returns True if the student has interacted recently.
    """

    def __init__(self):

        # last time user interacted
        self.last_activity_time = time.time()

        # practical threshold for exams (thinking time allowed)
        self.idle_threshold = 90   # seconds

        # keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_activity
        )

        # mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity
        )

        # start listeners
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def _on_activity(self, *args):
        """
        Called whenever keyboard or mouse activity occurs
        """
        self.last_activity_time = time.time()

    def is_active(self):
        """
        Returns True if user has interacted within idle_threshold
        """
        return (time.time() - self.last_activity_time) <= self.idle_threshold

    def stop(self):
        """
        Stop background listeners safely
        """
        try:
            self.keyboard_listener.stop()
            self.mouse_listener.stop()
        except Exception:
            pass