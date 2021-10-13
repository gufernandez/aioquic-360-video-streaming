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

    # Source: http://www.csun.edu/ansr/resources/simul15_paper.pdf
    #
    # In GPS (Generalized Processor Sharing), for any t seconds on a link capable of sending b bits per second, each
    # nonempty queue sends b ∗ t ∗ w bits, with 'w' being the share of the bandwidth that the link has.
    # To simulate GPS, the WFQ method calculates the order in which the last bit of each packet would be sent by a GPS
    # scheduler and dequeues the packets in that order

    def _init(self, maxsize):
        self.n = 2  # Number of different priorities (for now we have in FOV, and out of FOV)
        self._queue = []
        self.active = [False, False]
        self.weight = [0.75, 0.25]  # Share of the bandwidth for each queue
        self.ST = [[],[]] # Start time queues
        self.FT = [[], []] # Finish time queues
        self.VT = 0 # Virtual time
        self.time = 0
        self.last_time = 0
        self.last_VT = 0

    def _put (self, item, heappush=heapq.heappush):
        priority = item[0]-1
        length = item[1]
        content = item[2]

        self.update_virtual_time(length)

        self.activate(priority)

        if len(self.FT[priority]) == 0:
            ST = 0
        else:
            ST = max(self.FT[priority][-1], self.VT)

        finish_time = ST + length/self.weight[priority]
        self.FT[priority].append(finish_time)
        new_item = (finish_time, content)

        heappush(self._queue, new_item)

    def _get(self, heappop=heapq.heappop):
        return heappop(self._queue)[1]

    def get_active_min_F(self):
        try:
            first_active = self.active.index(True)
        except ValueError:
            return -1

        minimum = self.FT[first_active][-1]
        index = first_active
        for i in range(first_active + 1, self.n):
            if self.active[i] and self.FT[i][-1] < minimum:
                minimum = self.FT[i][-1]
                index = i

        return index

    def get_active_sum(self):
        total_weight = 0
        for i in range(self.n):
            if self.active[i]:
                total_weight += self.weight[i]

        return total_weight

    def update_virtual_time(self, packet_len):
        total_weight = self.get_active_sum()
        updated = False

        while not updated and total_weight > 0:
            min_f = self.get_active_min_F()
            if min_f == -1:
                exit()
            idle_time = self.time - self.last_time
            tmp = self.last_VT + idle_time*packet_len/total_weight

            if self.FT[min_f][-1] <= tmp:
                self.deactivate(min_f)
                self.last_time = self.last_time + (self.FT[min_f][-1] - self.last_VT) * total_weight / packet_len
                self.last_VT = self.FT[min_f][-1]
                total_weight = self.get_active_sum()
            else:
                self.VT = tmp
                self.last_time = self.VT
                self.last_VT = self.time
                updated = True

    def deactivate(self, index):
        self.active[index] = False

    def activate(self, index):
        self.active[index] = True
