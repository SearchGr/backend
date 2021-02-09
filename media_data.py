class MediaData:
    def __init__(self, classification, detection):
        self.classification = classification
        self.detection = detection
        if not classification and not detection:
            self.classification = [-1]
