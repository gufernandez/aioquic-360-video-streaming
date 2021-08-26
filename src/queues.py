import collections
from asyncio import Queue
import heapq

class StrictPriorityQueue(Queue):
    def _init(self, maxsize):
        self._queue = []

    def _put(self, item, heappush=heapq.heappush):
        heappush(self._queue, item)

    def _get(self, heappop=heapq.heappop):
        return heappop(self._queue)[1]


class WeightedFairQueue(Queue):

    def _init(self, maxsize):
        self.n = 7
        self.weight = [0.25, 0.2, 0.17, 0.15, 0.10, 0.08, 0.05] # Share of the bandwidth
        self._queue = [collections.deque() for i in range(self.n)]
        # Finish Time
        self.F = list(0 for i in range(self.n))
        # Queue start time
        self.S = list(0 for i in range(self.n))
        self.active = list(False for i in range(self.n))
        self.time = 0
        self.virtual_time = 0
        self.L = 10
        self.t = 0

    def _put(self, item):
        i = item[0]
        packet = item[1]
        weight = self.weight[i]

        if not self.active[i]:
            self.activate(i)

        if len(self._queue[i]) == 0:
            self.S[i] = max(self.F[i], self.virtual_time)

        self.F[i] = self.S[i] + self.L / weight

        self._queue[i].append(packet)

        self.time += 1

    def _get(self):
        self.time += 1
        min_f = self.get_active_min_F()

        # Update current virtual time
        self.update_virtual_time()
        if len(self._queue[min_f]) == 0:
            return
        return self._queue[min_f].popleft()

    def update_virtual_time(self):
        tk = 0
        vk = 0
        total_weight = self.get_active_sum()
        updated = False

        while not updated and total_weight > 0:
            min_f = self.get_active_min_F()
            if min_f == -1:
                exit()
            sig = self.time - tk
            tmp = vk + sig*self.L/total_weight

            if self.F[min_f] <= tmp:
                self.deactivate(min_f)
                tk = tk + (self.F[min_f] - vk) * total_weight / self.L
                vk = self.F[min_f]
                total_weight = self.get_active_sum()
            else:
                self.virtual_time = tmp
                vk = self.virtual_time
                tk = self.time
                updated = True


    def deactivate(self, index):
        self.active[index] = False

    def activate(self, index):
        self.active[index] = True

    def get_active_sum(self):
        total_weight = 0
        for i in range(self.n):
            if self.active[i]:
                total_weight += self.weight[i]

        return total_weight

    def get_active_min_F(self):
        try:
            first_active = self.active.index(True)
        except ValueError:
            return -1
        minimum = self.F[first_active]
        index = first_active
        for i in range(first_active+1, self.n):
            if self.active[i] and self.F[i] < minimum:
                minimum = self.F[i]
                index = first_active

        return index