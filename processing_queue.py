from queue import Queue


class ProcessingQueue(Queue):
    def _init(self, maxsize):
        self.queue = set()
        self.in_process_items = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        item = self.queue.pop()
        self.in_process_items.add(item)
        return item

    def finalize_task(self, item):
        with self.mutex:
            if item in self.in_process_items:
                self.in_process_items.remove(item)
        self.task_done()

    def check_items_in_queue(self, items):
        with self.mutex:
            unprocessed_items = self.queue.intersection(items)
            in_progress_items = self.in_process_items.intersection(items)
        return unprocessed_items.union(in_progress_items)
