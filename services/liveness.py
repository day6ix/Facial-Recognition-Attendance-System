import time

class LivenessDetector:
    def __init__(self):
        self.blinked = False
        self.head_moved = False
        self.start = time.time()

    def blink_detected(self, ear):
        if ear < 0.2:
            self.blinked = True

    def head_turn_detected(self, yaw):
        if abs(yaw) > 15:
            self.head_moved = True

    def is_live(self):
        return self.blinked and self.head_moved
