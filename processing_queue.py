from queue import Queue


class ProcessingQueue(Queue):
    def _init(self, maxsize):
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()

    def check_tasks_in_queue(self, tasks):
        with self.mutex:
            x = self.queue.intersection(tasks)
        return x
