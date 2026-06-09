import time

try:
    import pygetwindow as gw
    GW_AVAILABLE = True
except Exception:
    GW_AVAILABLE = False


class WindowTracker:
    def __init__(self):
        self.study_keywords = [
            "visual studio", "code", "pdf", "chrome", "firefox",
            "notepad", "word", "excel", "jupyter", "pycharm",
            "intellij", "sublime", "atom", "notion", "obsidian",
            "smart study", "youtube", "khan academy", "coursera"
        ]
        self._cache = False
        self._last_check = 0
        self._cache_interval = 2.0  # only check every 2 seconds

    def is_study_window_active(self):
        now = time.time()
        if now - self._last_check < self._cache_interval:
            return self._cache
        self._last_check = now

        if not GW_AVAILABLE:
            self._cache = True  # assume active if can't check
            return True
        try:
            win = gw.getActiveWindow()
            if win is None:
                self._cache = False
                return False
            title = win.title.lower()
            self._cache = any(k in title for k in self.study_keywords)
        except Exception:
            self._cache = True
        return self._cache

    def add_keyword(self, keyword):
        if keyword.lower() not in self.study_keywords:
            self.study_keywords.append(keyword.lower())

    def remove_keyword(self, keyword):
        kw = keyword.lower()
        if kw in self.study_keywords:
            self.study_keywords.remove(kw)
