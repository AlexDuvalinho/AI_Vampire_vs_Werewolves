import time

class Clock():
    def __init__(self, limit):
        self.begin_time = 0
        self.limit = limit

    def startClock(self):
        self.begin_time = time.time()

    def timeSinceBeginning(self):
        if (self.begin_time > 0):
            return time.time() - self.begin_time
        return 0

    def isTimeoutClose(self):
        return self.timeSinceBeginning() > self.limit