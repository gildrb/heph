# Shortest Paths

Dijkstra shortest paths choose the next frontier node with the smallest tentative
distance. The standard implementation uses a priority queue, relaxes outgoing
weighted edges, and assumes edge weights are non-negative.

Bellman-Ford also computes shortest paths, but it tolerates negative edge
weights and repeatedly relaxes every edge.
