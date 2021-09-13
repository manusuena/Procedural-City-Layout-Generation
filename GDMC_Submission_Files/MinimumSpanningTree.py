from math import sqrt


def makePoint(string):
    out = string.split(",")
    for i in xrange(len(out)):
        out[i] = int(out[i])
    return out


# Implementation of Prim's Algorithm
class Prim:
    def __init__(self, points):
        self.Q = [str(point[0]) + "," + str(point[-1]) for point in points]

        # Remove Duplicates
        i = 0
        while i < len(self.Q):
            if self.Q.count(self.Q[i]) > 1:
                self.Q.pop(i)
            else:
                i += 1

        self.F = []
        self.C = {}
        self.E = {}
        for point in self.Q:
            self.C[point] = 1000000000
            self.E[point] = "N/A"
        Q, F, C, E = self.Q, self.F, self.C, self.E
        while len(self.Q) > 0:
            minPoint = self.findMinCostPoint()
            Q.remove(minPoint)
            F.append(minPoint)
            if E[minPoint] != "N/A":
                F.append(E[minPoint])
            for point in Q:
                dist = self.distance(makePoint(minPoint), makePoint(point))
                if dist < C[point]:
                    C[point] = dist
                    E[point] = minPoint

    def distance(self, point1, point2):
        x1, z1 = point1[0], point1[-1]
        x2, z2 = point2[0], point2[-1]
        return sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2)

    def findMinCostPoint(self):
        min_point = self.Q[0]
        min_cost = self.C[self.Q[0]]
        for pointstr in self.Q:
            if self.C[pointstr] < min_cost:
                min_point = pointstr
                min_cost = self.C[pointstr]
        return min_point

    # Return pairs of points connected by edges
    def group(self):
        groups = []
        for point in self.F:
            if point == "N/A":
                continue
            point2 = self.E[point]
            if point2 == "N/A":
                continue
            groups.append([point, point2])
        temp = []
        for i in range(len(groups)):
            group = groups[i]
            point1 = makePoint(group[0])
            point2 = makePoint(group[1])
            if [point1, point2] not in temp and [point2, point1] not in temp:
                temp.append([point1, point2])
        return temp

