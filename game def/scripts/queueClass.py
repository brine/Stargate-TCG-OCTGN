class queueItem(object):
    def __init__(self):
        self.target = None
        self.trigger = None
        self.type = None
        self.count = 0
        self.priority = False
        self.skippable = False
        self.source = None

class moveCard(queueItem):
    def __init__(self):
        super.__init__(self)
    def serialize(self):
        return ""
    def deserialize(self):
        return ""