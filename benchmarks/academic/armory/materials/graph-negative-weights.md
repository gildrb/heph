# Negative Edge Shortest Paths

Bellman-Ford solves single-source shortest paths when negative edge weights may
appear. It repeatedly relaxes every edge and can detect a negative cycle.

This is not the standard choice when all edge weights are non-negative and the
question asks for Dijkstra's frontier data structure.
