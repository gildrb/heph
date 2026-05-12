[[geometry-manifolds.base]]

> Source: [[Laplacian Matrix]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In the [mathematical](https://en.wikipedia.org/wiki/Mathematics) field of [graph theory](https://en.wikipedia.org/wiki/Graph_theory), the **Laplacian matrix**, also called the **[graph Laplacian](https://en.wikipedia.org/wiki/Discrete_Laplace_operator#Graph_Laplacians)**, **[admittance matrix](https://en.wikipedia.org/wiki/Admittance_matrix)**, **Kirchhoff matrix,** or **[discrete Laplacian](https://en.wikipedia.org/wiki/Discrete_Laplace_operator)**, is a [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") representation of a [graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics) "Graph (discrete mathematics)"). Named after [Pierre-Simon Laplace](https://en.wikipedia.org/wiki/Pierre-Simon_Laplace), the graph Laplacian matrix can be viewed as a matrix form of the negative [discrete Laplace operator](https://en.wikipedia.org/wiki/Discrete_Laplace_operator) on a graph approximating the negative continuous [Laplacian](https://en.wikipedia.org/wiki/Laplacian) obtained by the [finite difference method](https://en.wikipedia.org/wiki/Finite_difference_method).

The Laplacian matrix relates to many functional graph properties. [Kirchhoff's theorem](https://en.wikipedia.org/wiki/Kirchhoff%27s_theorem) can be used to calculate the number of [spanning trees](https://en.wikipedia.org/wiki/Spanning_tree_(mathematics)) for a given graph. The [sparsest cut](https://en.wikipedia.org/wiki/Cut_(graph_theory)#Sparsest_cut "Cut (graph theory)") of a graph can be approximated through the [Fiedler vector](https://en.wikipedia.org/wiki/Fiedler_vector) — the eigenvector corresponding to the second smallest eigenvalue of the graph Laplacian — as established by [Cheeger's inequality](https://en.wikipedia.org/wiki/Cheeger_constant_(graph_theory)#Cheeger_Inequalities "Cheeger constant (graph theory)"). The [spectral decomposition](https://en.wikipedia.org/wiki/Eigendecomposition_of_a_matrix) of the Laplacian matrix allows the construction of [low-dimensional embeddings](https://en.wikipedia.org/wiki/Nonlinear_dimensionality_reduction#Laplacian_eigenmaps) that appear in many [machine learning](https://en.wikipedia.org/wiki/Machine_learning) applications and determines a [spectral layout](https://en.wikipedia.org/wiki/Spectral_layout) in [graph drawing](https://en.wikipedia.org/wiki/Graph_drawing). Graph-based [signal processing](https://en.wikipedia.org/wiki/Signal_processing) is based on the [graph Fourier transform](https://en.wikipedia.org/wiki/Graph_Fourier_transform) that extends the traditional [discrete Fourier transform](https://en.wikipedia.org/wiki/Discrete_Fourier_transform) by substituting the standard basis of [complex](https://en.wikipedia.org/wiki/Complex_number) [sinusoids](https://en.wikipedia.org/wiki/Sine_wave) for eigenvectors of the Laplacian matrix of a graph corresponding to the signal.

The Laplacian matrix is the easiest to define for a [simple graph](https://en.wikipedia.org/wiki/Simple_graph) but is more common in applications for an [edge-weighted graph](https://en.wikipedia.org/wiki/Glossary_of_graph_theory#weighted_graph), i.e., with weights on its edges — the entries of the graph [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix). [[Spectral Graph Theory]] relates properties of a graph to a spectrum, i.e., eigenvalues and eigenvectors of matrices associated with the graph, such as its adjacency matrix or Laplacian matrix. Imbalanced weights may undesirably affect the matrix spectrum, leading to the need of normalization — a column/row scaling of the matrix entries — resulting in normalized adjacency and Laplacian matrices.

## Definitions for *simple graphs*

### Laplacian matrix

Given a [simple graph](https://en.wikipedia.org/wiki/Simple_graph) $G$ with $n$ vertices $v_{1},\ldots ,v_{n}$, its Laplacian matrix $L_{n\times n}$ is defined element-wise as

$L_{i,j}:={\begin{cases}\deg(v_{i})&{\mbox{if}}\ i=j\\-1&{\mbox{if}}\ i\neq j\ {\mbox{and}}\ v_{i}{\mbox{ is adjacent to }}v_{j}\\0&{\mbox{otherwise}},\end{cases}}$

or equivalently by the matrix

$L=D-A,$

where *D* is the [degree matrix](https://en.wikipedia.org/wiki/Degree_matrix), and *A* is the graph's [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix). Since $G$ is a simple graph, $A$ only contains 1s or 0s and its diagonal elements are all 0s.

Here is a simple example of a labelled, undirected graph and its Laplacian matrix.

|  |  |  |  |
|----|----|----|----|
| [Labelled graph](https://en.wikipedia.org/wiki/Labelled_graph) | [Degree matrix](https://en.wikipedia.org/wiki/Degree_matrix) | [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Laplacian matrix |
| ![[media/ed0f0ce2f9b252a9a91998de033eebc616610e08.png]] | $\left({\begin{array}{rrrrrr}2&0&0&0&0&0\\0&3&0&0&0&0\\0&0&2&0&0&0\\0&0&0&3&0&0\\0&0&0&0&3&0\\0&0&0&0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrrrrr}0&1&0&0&1&0\\1&0&1&0&1&0\\0&1&0&1&0&0\\0&0&1&0&1&1\\1&1&0&1&0&0\\0&0&0&1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrrrrr}2&-1&0&0&-1&0\\-1&3&-1&0&-1&0\\0&-1&2&-1&0&0\\0&0&-1&3&-1&-1\\-1&-1&0&-1&3&0\\0&0&0&-1&0&1\\\end{array}}\right)$ |

We observe for the undirected graph that both the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) and the Laplacian matrix are symmetric and that the row- and column-sums of the Laplacian matrix are all zeros (which directly implies that the Laplacian matrix is singular).

For [directed graphs](https://en.wikipedia.org/wiki/Directed_graph), either the [indegree or outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") might be used, depending on the application, as in the following example:

<table class="wikitable" style="width:100%;">

Labelled graph
[Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix)
Out-Degree matrix
Out-Degree Laplacian
In-Degree matrix
In-Degree Laplacian

&#10;
<figure class="mw-halign-center" typeof="mw:File">
![[media/71513ab23cc4b709bea27d7b1e045069acfb8d4d.png]]
</figure>
$\left({\begin{array}{rrr}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$
$\left({\begin{array}{rrr}2&0&0\\0&1&0\\0&0&1\\\end{array}}\right)$
$\left({\begin{array}{rrr}2&0&-1\\-1&1&0\\-1&-1&1\\\end{array}}\right)$
$\left({\begin{array}{rrr}1&0&0\\0&1&0\\0&0&2\\\end{array}}\right)$
$\left({\begin{array}{rrr}1&-1&-1\\0&1&-1\\-1&0&2\\\end{array}}\right)$

</table>

In the directed graph, the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) and Laplacian matrix are asymmetric. In its Laplacian matrix, column-sums or row-sums are zero, depending on whether the [indegree or outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") has been used.

### Laplacian matrix for an undirected graph via the oriented incidence matrix

The $|v|\times |e|$ oriented [incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) *B* with element *B*<sub>*ve*</sub> for the vertex *v* and the edge *e* (connecting vertices $v_{i}$ and $v_{j}$, with *i* ≠ *j*) is defined by

$B_{ve}=\left\{{\begin{array}{rl}1,&{\text{if }}v=v_{i}\\-1,&{\text{if }}v=v_{j}\\0,&{\text{otherwise}}.\end{array}}\right.$

Even though the edges in this definition are technically directed, their directions can be arbitrary, still resulting in the same symmetric Laplacian $|v|\times |v|$ matrix *L* defined as

$L=BB^{\textsf {T}}$

where $B^{\textsf {T}}$ is the [matrix transpose](https://en.wikipedia.org/wiki/Transpose) of *B*.

|  |  |  |
|----|----|----|
| [Undirected graph](https://en.wikipedia.org/wiki/Undirected_graph) | [Incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) | Laplacian matrix |
| ![[media/1b6a9b255365a9e6ba21d355d328100286b597dd.png]] | $\left({\begin{array}{rrrr}1&1&1&0\\-1&0&0&0\\0&-1&0&1\\0&0&-1&-1\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}3&-1&-1&-1\\-1&1&0&0\\-1&0&2&-1\\-1&0&-1&2\\\end{array}}\right)$ |

An alternative product $B^{\textsf {T}}B$ defines the so-called $|e|\times |e|$ *edge-based Laplacian,* as opposed to the original commonly used *vertex-based Laplacian* matrix *L*.

### Symmetric Laplacian for a directed graph

The Laplacian matrix of a directed graph is by definition generally non-symmetric, while, e.g., traditional [spectral clustering](https://en.wikipedia.org/wiki/Spectral_clustering) is primarily developed for undirected graphs with symmetric adjacency and Laplacian matrices. A trivial approach to applying techniques requiring the symmetry is to turn the original directed graph into an undirected graph and build the Laplacian matrix for the latter.

In the matrix notation, the adjacency matrix of the undirected graph could, e.g., be defined as a [Boolean sum](https://en.wikipedia.org/wiki/OR_gate) of the adjacency matrix $A$ of the original directed graph and its [matrix transpose](https://en.wikipedia.org/wiki/Matrix_transpose) $A^{T}$, where the zero and one entries of $A$ are treated as logical, rather than numerical, values, as in the following example:

|  |  |  |
|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Symmetrized adjacency | Symmetric Laplacian matrix |
| $\left({\begin{array}{ccc}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{ccc}0&1&1\\1&0&1\\1&1&0\\\end{array}}\right)$ | $\left({\begin{array}{ccc}2&-1&-1\\-1&2&-1\\-1&-1&2\\\end{array}}\right)$ |

### Laplacian matrix normalization

A vertex with a large degree, also called a *heavy node*, results in a large diagonal entry in the Laplacian matrix dominating the matrix properties. Normalization is aimed to make the influence of such vertices more equal to that of other vertices, by dividing the entries of the Laplacian matrix by the vertex degrees. To avoid division by zero, isolated vertices with zero degrees are excluded from the process of the normalization.

#### Symmetrically normalized Laplacian

The symmetrically normalized Laplacian matrix is defined as:

$L^{\text{sym}}:=(D^{+})^{1/2}L(D^{+})^{1/2}=I-(D^{+})^{1/2}A(D^{+})^{1/2},$

where $D^{+}$ is the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse) of the degree matrix.

The elements of $L^{\text{sym}}$ are thus given by

$L_{i,j}^{\text{sym}}:={\begin{cases}1&{\mbox{if }}i=j{\mbox{ and }}\deg(v_{i})\neq 0\\-{\frac {1}{\sqrt {\deg(v_{i})\deg(v_{j})}}}&{\mbox{if }}i\neq j{\mbox{ and }}v_{i}{\mbox{ is adjacent to }}v_{j}\\0&{\mbox{otherwise}}.\end{cases}}$

The symmetrically normalized Laplacian matrix is symmetric if and only if the adjacency matrix is symmetric.

|  |  |  |
|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Degree matrix | Normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&0\\1&0&1\\0&1&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&2&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-{\sqrt {1/2}}&0\\-{\sqrt {1/2}}&1&-{\sqrt {1/2}}\\0&-{\sqrt {1/2}}&1\\\end{array}}\right)$ |

For a non-symmetric adjacency matrix of a directed graph, either of [indegree and outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") can be used for normalization:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Out-Degree matrix | Out-Degree normalized Laplacian | In-Degree matrix | In-Degree normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}2&0&0\\0&1&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-{\sqrt {1/2}}&-{\sqrt {1/2}}\\0&1&-1\\-{\sqrt {1/2}}&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&1&0\\0&0&2\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&-{\sqrt {1/2}}\\0&1&-{\sqrt {1/2}}\\-{\sqrt {1/2}}&0&1\\\end{array}}\right)$ |

#### Left (random-walk) and right normalized Laplacians

The left (random-walk) normalized Laplacian matrix is defined as:

$L^{\text{rw}}:=D^{+}L=I-D^{+}A,$

where $D^{+}$ is the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse). The elements of $L^{\text{rw}}$ are given by

$L_{i,j}^{\text{rw}}:={\begin{cases}1&{\mbox{if }}i=j{\mbox{ and }}\deg(v_{i})\neq 0\\-{\frac {1}{\deg(v_{i})}}&{\mbox{if }}i\neq j{\mbox{ and }}v_{i}{\mbox{ is adjacent to }}v_{j}\\0&{\mbox{otherwise}}.\end{cases}}$

Similarly, the right normalized Laplacian matrix is defined as

$LD^{+}=I-AD^{+}$.

The left or right normalized Laplacian matrix is symmetric if the adjacency matrix is symmetric and the graph is regular. Otherwise, the left or right normalized Laplacian matrix is asymmetric. For example,

|  |  |  |  |
|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Degree matrix | Left normalized Laplacian | Right normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&0\\1&0&1\\0&1&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&2&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&0\\-1/2&1&-1/2\\0&-1&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1/2&0\\-1&1&-1\\0&-1/2&1\\\end{array}}\right)$ |

The example also demonstrates that if $G$ has no isolated vertices, then $D^{+}A$ [right stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix) and hence is the matrix of a [random walk](https://en.wikipedia.org/wiki/Random_walk), so that the left normalized Laplacian $L^{\text{rw}}:=D^{+}L=I-D^{+}A$ has each row summing to zero. Thus we sometimes alternatively call $L^{\text{rw}}$ the [random-walk](https://en.wikipedia.org/wiki/Random_walk) normalized Laplacian. In the less uncommonly used right normalized Laplacian $LD^{+}=I-AD^{+}$ each column sums to zero since $AD^{+}$ is [left stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix).

For a non-symmetric adjacency matrix of a directed graph, one also needs to choose [indegree or outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") for normalization:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Out-Degree matrix | Out-Degree left normalized Laplacian | In-Degree matrix | In-Degree right normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}2&0&0\\0&1&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1/2&-1/2\\0&1&-1\\-1&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&1&0\\0&0&2\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&-1/2\\0&1&-1/2\\-1&0&1\\\end{array}}\right)$ |

The left out-degree normalized Laplacian with row-sums all 0 relates to [right stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix) $D_{\text{out}}^{+}A$ , while the right in-degree normalized Laplacian with column-sums all 0 contains [left stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix) $AD_{\text{in}}^{+}$.

## Definitions for graphs with weighted edges

Common in applications graphs with weighted edges are conveniently defined by their adjacency matrices where values of the entries are numeric and no longer limited to zeros and ones. In [spectral clustering](https://en.wikipedia.org/wiki/Spectral_clustering) and graph-based [signal processing](https://en.wikipedia.org/wiki/Signal_processing), where graph vertices represent data points, the edge weights can be computed, e.g., as inversely proportional to the [distances](https://en.wikipedia.org/wiki/Distance_matrix) between pairs of data points, leading to all weights being non-negative with larger values informally corresponding to more similar pairs of data points. Using correlation and anti-correlation between the data points naturally leads to both positive and negative weights. Most definitions for simple graphs are trivially extended to the standard case of non-negative weights, while negative weights require more attention, especially in normalization.

### Laplacian matrix

The Laplacian matrix is defined by

$L=D-A,$

where *D* is the [degree matrix](https://en.wikipedia.org/wiki/Degree_matrix) and *A* is the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) of the graph.

For [directed graphs](https://en.wikipedia.org/wiki/Directed_graph), either the [indegree or outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") might be used, depending on the application, as in the following example:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | In-Degree matrix | In-Degree Laplacian | Out-Degree matrix | Out-Degree Laplacian |
| $\left({\begin{array}{rrr}0&1&2\\3&0&5\\6&7&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}9&0&0\\0&8&0\\0&0&7\\\end{array}}\right)$ | $\left({\begin{array}{rrr}9&-1&-2\\-3&8&-5\\-6&-7&7\\\end{array}}\right)$ | $\left({\begin{array}{rrr}3&0&0\\0&8&0\\0&0&13\\\end{array}}\right)$ | $\left({\begin{array}{rrr}3&-1&-2\\-3&8&-5\\-6&-7&13\\\end{array}}\right)$ |

Graph self-loops, manifesting themselves by non-zero entries on the main diagonal of the adjacency matrix, are allowed but do not affect the graph Laplacian values.

### Symmetric Laplacian via the incidence matrix

![[media/7a5be9c23db7137d67371a5c7e00b6f791d02774.png]]
A 2-dimensional spring system.

For graphs with weighted edges one can define a weighted incidence matrix *B* and use it to construct the corresponding symmetric Laplacian as $L=BB^{\textsf {T}}$. An alternative cleaner approach, described here, is to separate the weights from the connectivity: continue using the [incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) as for regular graphs and introduce a matrix just holding the values of the weights. A [spring system](https://en.wikipedia.org/wiki/Spring_system) is an example of this model used in [mechanics](https://en.wikipedia.org/wiki/Mechanics) to describe a system of springs of given stiffnesses and unit length, where the values of the stiffnesses play the role of the weights of the graph edges.

We thus reuse the definition of the weightless $|v|\times |e|$ [incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) *B* with element *B*<sub>*ve*</sub> for the vertex *v* and the edge *e* (connecting vertexes $v_{i}$ and $v_{j}$, with *i* \> *j*) defined by

$B_{ve}=\left\{{\begin{array}{rl}1,&{\text{if }}v=v_{i}\\-1,&{\text{if }}v=v_{j}\\0,&{\text{otherwise}}.\end{array}}\right.$

We now also define a diagonal $|e|\times |e|$ matrix *W* containing the edge weights. Even though the edges in the definition of *B* are technically directed, their directions can be arbitrary, still resulting in the same symmetric Laplacian $|v|\times |v|$ matrix *L* defined as

$L=BWB^{\textsf {T}}$

where $B^{\textsf {T}}$ is the [matrix transpose](https://en.wikipedia.org/wiki/Transpose) of *B*.

The construction is illustrated in the following example, where every edge $e_{i}$ is assigned the weight value *i*, with $i=1,2,3,4.$

|  |  |  |  |
|----|----|----|----|
| [Undirected graph](https://en.wikipedia.org/wiki/Undirected_graph) | [Incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) | Edge weights | Laplacian matrix |
| ![[media/1b6a9b255365a9e6ba21d355d328100286b597dd.png]] | $\left({\begin{array}{rrrr}1&1&1&0\\-1&0&0&0\\0&-1&0&1\\0&0&-1&-1\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}1&0&0&0\\0&2&0&0\\0&0&3&0\\0&0&0&4\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}6&-1&-2&-3\\-1&1&0&0\\-2&0&6&-4\\-3&0&-4&7\\\end{array}}\right)$ |

### Symmetric Laplacian for a directed graph

Just like for simple graphs, the Laplacian matrix of a directed weighted graph is by definition generally non-symmetric. The symmetry can be enforced by turning the original directed graph into an undirected graph first before constructing the Laplacian. The adjacency matrix of the undirected graph could, e.g., be defined as a sum of the adjacency matrix $A$ of the original directed graph and its [matrix transpose](https://en.wikipedia.org/wiki/Matrix_transpose) $A^{T}$ as in the following example:

|  |  |  |
|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Symmetrized adjacency matrix | Symmetric Laplacian matrix |
| $\left({\begin{array}{rrr}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}0&1&2\\1&0&1\\2&1&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}3&-1&-2\\-1&2&-1\\-2&-1&3\\\end{array}}\right)$ |

where the zero and one entries of $A$ are treated as numerical, rather than logical as for simple graphs, values, explaining the difference in the results - for simple graphs, the symmetrized graph still needs to be simple with its symmetrized adjacency matrix having only logical, not numerical values, e.g., the logical sum is 1 v 1 = 1, while the numeric sum is 1 + 1 = 2.

Alternatively, the symmetric Laplacian matrix can be calculated from the two Laplacians using the [indegree and outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)"), as in the following example:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Out-Degree matrix | Out-Degree Laplacian | In-Degree matrix | In-Degree Laplacian |
| $\left({\begin{array}{rrr}0&1&1\\0&0&1\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}2&0&0\\0&1&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}2&-1&-1\\0&1&-1\\-1&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&1&0\\0&0&2\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&-1\\0&1&-1\\-1&0&2\\\end{array}}\right)$ |

The sum of the out-degree Laplacian transposed and the in-degree Laplacian equals to the symmetric Laplacian matrix.

### Laplacian matrix normalization

The goal of normalization is, like for simple graphs, to make the diagonal entries of the Laplacian matrix to be all unit, also scaling off-diagonal entries correspondingly. In a [weighted graph](https://en.wikipedia.org/wiki/Glossary_of_graph_theory#weighted_graph), a vertex may have a large degree because of a small number of connected edges but with large weights just as well as due to a large number of connected edges with unit weights.

Graph self-loops, i.e., non-zero entries on the main diagonal of the adjacency matrix, do not affect the graph Laplacian values, but may need to be counted for calculation of the normalization factors.

#### Symmetrically normalized Laplacian

The **symmetrically normalized Laplacian** is defined as

$L^{\text{sym}}:=(D^{+})^{1/2}L(D^{+})^{1/2}=I-(D^{+})^{1/2}A(D^{+})^{1/2},$

where *L* is the unnormalized Laplacian, *A* is the adjacency matrix, *D* is the degree matrix, and $D^{+}$ is the [Moore–Penrose inverse](https://en.wikipedia.org/wiki/Moore%E2%80%93Penrose_inverse). Since the degree matrix *D* is diagonal, its reciprocal square root $(D^{+})^{1/2}$ is just the diagonal matrix whose diagonal entries are the reciprocals of the square roots of the diagonal entries of *D*. If all the edge weights are nonnegative then all the degree values are automatically also nonnegative and so every degree value has a unique positive square root. To avoid the division by zero, vertices with zero degrees are excluded from the process of the normalization, as in the following example:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | In-Degree matrix | In-Degree normalized Laplacian | Out-Degree matrix | Out-Degree normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&0\\4&0&0\\0&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&4&0\\0&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1/2&0\\-2&1&0\\0&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}4&0&0\\0&1&0\\0&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1/2&0\\-2&1&0\\0&0&0\\\end{array}}\right)$ |

The symmetrically normalized Laplacian is a symmetric matrix if and only if the adjacency matrix *A* is symmetric and the diagonal entries of *D* are nonnegative, in which case we can use the term the ***symmetric normalized Laplacian***.

The symmetric normalized Laplacian matrix can be also written as

$L^{\text{sym}}:=(D^{+})^{1/2}L(D^{+})^{1/2}=(D^{+})^{1/2}BWB^{\textsf {T}}(D^{+})^{1/2}=SS^{T}$

using the weightless $|v|\times |e|$ [incidence matrix](https://en.wikipedia.org/wiki/Incidence_matrix) *B* and the diagonal $|e|\times |e|$ matrix *W* containing the edge weights and defining the new $|v|\times |e|$ weighted incidence matrix $S=(D^{+})^{1/2}BW^{{1}/{2}}$ whose rows are indexed by the vertices and whose columns are indexed by the edges of G such that each column corresponding to an edge *e = {u, v}* has an entry ${\frac {1}{\sqrt {d_{u}}}}$ in the row corresponding to *u*, an entry $-{\frac {1}{\sqrt {d_{v}}}}$ in the row corresponding to *v*, and has 0 entries elsewhere.

#### Random walk normalized Laplacian

The **random walk normalized Laplacian** is defined as

$L^{\text{rw}}:=D^{+}L=I-D^{+}A$

where *D* is the degree matrix. Since the degree matrix *D* is diagonal, its inverse $D^{+}$ is simply defined as a diagonal matrix, having diagonal entries which are the reciprocals of the corresponding diagonal entries of *D*. For the isolated vertices (those with degree 0), a common choice is to set the corresponding element $L_{i,i}^{\text{rw}}$ to 0. The matrix elements of $L^{\text{rw}}$ are given by

$L_{i,j}^{\text{rw}}:={\begin{cases}1&{\mbox{if}}\ i=j\ {\mbox{and}}\ \deg(v_{i})\neq 0\\-{\frac {1}{\deg(v_{i})}}&{\mbox{if}}\ i\neq j\ {\mbox{and}}\ v_{i}{\mbox{ is adjacent to }}v_{j}\\0&{\mbox{otherwise}}.\end{cases}}$

The name of the random-walk normalized Laplacian comes from the fact that this matrix is $L^{\text{rw}}=I-P$, where $P=D^{+}A$ is simply the transition matrix of a random walker on the graph, assuming non-negative weights. For example, let $e_{i}$ denote the i-th [standard basis](https://en.wikipedia.org/wiki/Standard_basis) vector. Then $x=e_{i}P$ is a [probability vector](https://en.wikipedia.org/wiki/Probability_vector) representing the distribution of a random walker's locations after taking a single step from vertex $i$; i.e., $x_{j}=\mathbb {P} \left(v_{i}\to v_{j}\right)$. More generally, if the vector $x$ is a probability distribution of the location of a random walker on the vertices of the graph, then $x'=xP^{t}$ is the probability distribution of the walker after $t$ steps.

The random walk normalized Laplacian can also be called the left normalized Laplacian $L^{\text{rw}}:=D^{+}L$ since the normalization is performed by multiplying the Laplacian by the normalization matrix $D^{+}$ on the left. It has each row summing to zero since $P=D^{+}A$ is [right stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix), assuming all the weights are non-negative.

In the less uncommonly used right normalized Laplacian $LD^{+}=I-AD^{+}$ each column sums to zero since $AD^{+}$ is [left stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix).

For a non-symmetric adjacency matrix of a directed graph, one also needs to choose [indegree or outdegree](https://en.wikipedia.org/wiki/Degree_(graph_theory) "Degree (graph theory)") for normalization:

|  |  |  |  |  |
|----|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Out-Degree matrix | Out-Degree left normalized Laplacian | In-Degree matrix | In-Degree right normalized Laplacian |
| $\left({\begin{array}{rrr}0&1&0\\0&0&2\\1&0&0\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&2&0\\0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&0\\0&1&-1\\-1&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&0&0\\0&1&0\\0&0&2\\\end{array}}\right)$ | $\left({\begin{array}{rrr}1&-1&0\\0&1&-1\\-1&0&1\\\end{array}}\right)$ |

The left out-degree normalized Laplacian with row-sums all 0 relates to [right stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix) $D_{\text{out}}^{+}A$ , while the right in-degree normalized Laplacian with column-sums all 0 contains [left stochastic](https://en.wikipedia.org/wiki/Stochastic_matrix) $AD_{\text{in}}^{+}$.

#### Negative weights

Negative weights present several challenges for normalization:

- The presence of negative weights may naturally result in zero row- and/or column-sums for non-isolated vertices. A vertex with a large row-sum of positive weights and equally negatively large row-sum of negative weights, together summing up to zero, could be considered a heavy node and both large values scaled, while the diagonal entry remains zero, like for an isolated vertex.
- Negative weights may also give negative row- and/or column-sums, so that the corresponding diagonal entry in the non-normalized Laplacian matrix would be negative and a positive square root needed for the symmetric normalization would not exist.
- Arguments can be made to take the absolute value of the row- and/or column-sums for the purpose of normalization, thus treating a possible value -1 as a legitimate unit entry of the main diagonal of the normalized Laplacian matrix.

## Properties

For an (undirected) graph *G* and its Laplacian matrix *L* with [eigenvalues](https://en.wikipedia.org/wiki/Eigenvalues) $\lambda _{0}\leq \lambda _{1}\leq \cdots \leq \lambda _{n-1}$:

- *L* is [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix).
- *L* is [[Positive-Definite Matrix|positive-semidefinite]] (that is $\lambda _{i}\geq 0$ for all $i$). This can be seen from the fact that the Laplacian is symmetric and [diagonally dominant](https://en.wikipedia.org/wiki/Diagonally_dominant_matrix#Applications_and_properties).
- *L* is an [M-matrix](https://en.wikipedia.org/wiki/M-matrix) (its off-diagonal entries are nonpositive, yet the real parts of its eigenvalues are nonnegative).
- Every row sum and column sum of *L* is zero. Indeed, in the sum, the degree of the vertex is summed with a "−1" for each neighbor.
- In consequence, $\lambda _{0}=0$, because the vector $\mathbf {v} _{0}=(1,1,\dots ,1)$ satisfies $L\mathbf {v} _{0}=\mathbf {0} .$ This also implies that the Laplacian matrix is singular.
- The number of [connected components](https://en.wikipedia.org/wiki/Connected_component_(graph_theory)) in the graph is the dimension of the [nullspace](https://en.wikipedia.org/wiki/Kernel_(linear_algebra) "Kernel (linear algebra)") of the Laplacian and the [[Eigenvalues and Eigenvectors|algebraic multiplicity]] of the 0 eigenvalue.
- The smallest non-zero eigenvalue of *L* is called the [spectral gap](https://en.wikipedia.org/wiki/Spectral_gap).
- The second smallest eigenvalue of *L* (could be zero) is the [algebraic connectivity](https://en.wikipedia.org/wiki/Algebraic_connectivity) (or [Fiedler value](https://en.wikipedia.org/wiki/Fiedler_value)) of *G* and approximates the [sparsest cut](https://en.wikipedia.org/wiki/Cut_(graph_theory)#Sparsest_cut "Cut (graph theory)") of a graph.
- The [Laplacian](https://en.wikipedia.org/wiki/Laplacian) is an operator on the n-dimensional vector space of functions $f:V\to \mathbb {R}$, where $V$ is the vertex set of G, and $n=|V|$.
- When G is [k-regular](https://en.wikipedia.org/wiki/K-regular_graph), the normalized Laplacian is: ${\mathcal {L}}={\tfrac {1}{k}}L=I-{\tfrac {1}{k}}A$, where A is the adjacency matrix and I is an identity matrix.
- For a graph with multiple [connected components](https://en.wikipedia.org/wiki/Connected_component_(graph_theory)), *L* is a [block diagonal](https://en.wikipedia.org/wiki/Block_matrix#Block_diagonal_matrices) matrix, where each block is the respective Laplacian matrix for each component, possibly after reordering the vertices (i.e. *L* is permutation-similar to a block diagonal matrix).
- The trace of the Laplacian matrix *L* is equal to $2m$ where $m$ is the number of edges of the considered graph.
- Now consider an eigendecomposition of $L$, with unit-norm eigenvectors $\mathbf {v} _{i}$ and corresponding eigenvalues $\lambda _{i}$:

${\begin{aligned}\lambda _{i}&=\mathbf {v} _{i}^{\textsf {T}}L\mathbf {v} _{i}\\&=\mathbf {v} _{i}^{\textsf {T}}M^{\textsf {T}}M\mathbf {v} _{i}\\&=\left(M\mathbf {v} _{i}\right)^{\textsf {T}}\left(M\mathbf {v} _{i}\right).\\\end{aligned}}$

Because $\lambda _{i}$ can be written as the inner product of the vector $M\mathbf {v} _{i}$ with itself, this shows that $\lambda _{i}\geq 0$ and so the eigenvalues of $L$ are all non-negative.

- All eigenvalues of the normalized symmetric Laplacian satisfy 0 = μ<sub>0</sub> ≤ … ≤ μ<sub>n−1</sub> ≤ 2. These eigenvalues (known as the spectrum of the normalized Laplacian) relate well to other graph invariants for general graphs.

- One can check that:

$L^{\text{rw}}=I-D^{-{\frac {1}{2}}}\left(I-L^{\text{sym}}\right)D^{\frac {1}{2}}$,

i.e., $L^{\text{rw}}$ is [similar](https://en.wikipedia.org/wiki/Matrix_similarity) to the normalized Laplacian $L^{\text{sym}}$. For this reason, even if $L^{\text{rw}}$ is in general not symmetric, it has real eigenvalues — exactly the same as the eigenvalues of the normalized symmetric Laplacian $L^{\text{sym}}$.

## Interpretation as the discrete Laplace operator approximating the continuous Laplacian

The graph Laplacian matrix can be further viewed as a matrix form of the negative [discrete Laplace operator](https://en.wikipedia.org/wiki/Discrete_Laplace_operator) on a graph approximating the negative continuous [Laplacian](https://en.wikipedia.org/wiki/Laplacian) operator obtained by the [finite difference method](https://en.wikipedia.org/wiki/Finite_difference_method). (See [Discrete Poisson equation](https://en.wikipedia.org/wiki/Discrete_Poisson_equation)) In this interpretation, every graph vertex is treated as a grid point; the local connectivity of the vertex determines the finite difference approximation [stencil](https://en.wikipedia.org/wiki/Stencil_(numerical_analysis) "Stencil (numerical analysis)") at this grid point, the grid size is always one for every edge, and there are no constraints on any grid points, which corresponds to the case of the homogeneous [Neumann boundary condition](https://en.wikipedia.org/wiki/Neumann_boundary_condition), i.e., free boundary. Such an interpretation allows one, e.g., generalizing the Laplacian matrix to the case of graphs with an infinite number of vertices and edges, leading to a Laplacian matrix of an infinite size.

## Generalizations and extensions of the Laplacian matrix

### Generalized Laplacian

The generalized Laplacian $Q$ is defined as:

${\begin{cases}Q_{i,j}<0&{\mbox{if }}i\neq j{\mbox{ and }}v_{i}{\mbox{ is adjacent to }}v_{j}\\Q_{i,j}=0&{\mbox{if }}i\neq j{\mbox{ and }}v_{i}{\mbox{ is not adjacent to }}v_{j}\\{\mbox{any number}}&{\mbox{otherwise}}.\end{cases}}$

Notice the ordinary Laplacian is a generalized Laplacian.

### Admittance matrix of an AC circuit

The Laplacian of a graph was first introduced to model electrical networks. In an alternating current (AC) electrical network, real-valued resistances are replaced by complex-valued impedances. The weight of edge (*i*, *j*) is, by convention, *minus* the reciprocal of the impedance directly between *i* and *j*. In models of such networks, the entries of the [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) are complex, but the Kirchhoff matrix remains symmetric, rather than being [Hermitian](https://en.wikipedia.org/wiki/Hermitian). Such a matrix is usually called an "[admittance matrix](https://en.wikipedia.org/wiki/Admittance_matrix)", denoted $Y$, rather than a "Laplacian". This is one of the rare applications that give rise to [complex symmetric matrices](https://en.wikipedia.org/wiki/Symmetric_matrix#Complex).

|  |  |  |
|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Weighted degree matrix | Admittance matrix |
| $\left({\begin{array}{rrrr}0&i&0&0\\i&0&1-2i&0\\0&1-2i&0&1\\0&0&1&0\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}i&0&0&0\\0&1-i&0&0\\0&0&2-2i&0\\0&0&0&1\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}-i&i&0&0\\i&-1+i&1-2i&0\\0&1-2i&-2+2i&1\\0&0&1&-1\\\end{array}}\right)$ |

### Magnetic Laplacian

There are other situations in which entries of the adjacency matrix are complex-valued, and the Laplacian does become a [Hermitian matrix](https://en.wikipedia.org/wiki/Hermitian_matrix). The Magnetic Laplacian for a directed graph with real weights $w_{ij}$ is constructed as the [Hadamard product](https://en.wikipedia.org/wiki/Hadamard_product_(matrices) "Hadamard product (matrices)") of the [real symmetric matrix](https://en.wikipedia.org/wiki/Symmetric_matrix#Real_symmetric_matrices) of the symmetrized Laplacian and the Hermitian phase matrix with the [complex](https://en.wikipedia.org/wiki/Complex_number) entries

$\gamma _{q}(i,j)=e^{i2\pi q(w_{ij}-w_{ji})}$

which encode the edge direction into the phase in the complex plane. In the context of quantum physics, the magnetic Laplacian can be interpreted as the operator that describes the phenomenology of a free charged particle on a graph, which is subject to the action of a magnetic field and the parameter $q$ is called electric charge. In the following example $q=1/4$:

|  |  |  |  |
|----|----|----|----|
| [Adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) | Symmetrized Laplacian | Phase matrix | Magnetic Laplacian |
| $\left({\begin{array}{rrrr}0&1&0&0\\1&0&1&0\\0&0&0&0\\0&0&1&0\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}2&-2&0&0\\-2&3&-1&0\\0&-1&2&-1\\0&0&-1&1\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}1&1&1&1\\1&1&i&1\\1&-i&1&-i\\1&1&i&1\\\end{array}}\right)$ | $\left({\begin{array}{rrrr}2&-2&0&0\\-2&3&-i&0\\0&i&2&i\\0&0&-i&1\\\end{array}}\right)$ |

### Deformed Laplacian

The **deformed Laplacian** is commonly defined as

$\Delta (s)=I-sA+s^{2}(D-I)$

where $I$ is the identity matrix, $A$ is the adjacency matrix, $D$ is the degree matrix, and $s$ is a (complex-valued) number.  
The standard Laplacian is just $\Delta (1)$ and $\Delta (-1)=D+A$ is the signless Laplacian.

### Signless Laplacian

The **signless Laplacian** is defined as

$Q=D+A$

where $D$ is the degree matrix, and $A$ is the adjacency matrix. Like the signed Laplacian $L$, the signless Laplacian $Q$ also is positive semi-definite as it can be factored as

$Q=RR^{\textsf {T}}$

where $R$ is the incidence matrix. $Q$ has a 0-eigenvector if and only if it has a bipartite connected component (isolated vertices being bipartite connected components). This can be shown as

$\mathbf {x} ^{\textsf {T}}Q\mathbf {x} =\mathbf {x} ^{\textsf {T}}RR^{\textsf {T}}\mathbf {x} \implies R^{\textsf {T}}\mathbf {x} =\mathbf {0} .$

This has a solution where $\mathbf {x} \neq \mathbf {0}$ if and only if the graph has a bipartite connected component.

### Directed multigraphs

An analogue of the Laplacian matrix can be defined for directed multigraphs. In this case the Laplacian matrix *L* is defined as

$L=D-A$

where *D* is a diagonal matrix with *D*<sub>*i*,*i*</sub> equal to the outdegree of vertex *i* and *A* is a matrix with *A*<sub>*i*,*j*</sub> equal to the number of edges from *i* to *j* (including loops).

## Open source software implementations

- [SciPy](https://en.wikipedia.org/wiki/SciPy)
- [NetworkX](https://en.wikipedia.org/wiki/NetworkX)
- [Julia](https://en.wikipedia.org/wiki/Julia_(programming_language) "Julia (programming language)")

## Application software

- [scikit-learn](https://en.wikipedia.org/wiki/Scikit-learn) Spectral Clustering
- PyGSP: Graph Signal Processing in Python
- megaman: Manifold Learning for Millions of Points
- smoothG
- Laplacian Change Point Detection for Dynamic Graphs (KDD 2020)
- LaplacianOpt (A Julia Package for Maximizing Laplacian's Second Eigenvalue of Weighted Graphs) 
- LigMG (Large Irregular Graph MultiGrid)
- Laplacians.jl

## See also

- [Stiffness matrix](https://en.wikipedia.org/wiki/Stiffness_matrix)
- [Resistance distance](https://en.wikipedia.org/wiki/Resistance_distance)
- [Transition rate matrix](https://en.wikipedia.org/wiki/Transition_rate_matrix)
- [Calculus on finite weighted graphs](https://en.wikipedia.org/wiki/Calculus_on_finite_weighted_graphs)
- [Graph Fourier transform](https://en.wikipedia.org/wiki/Graph_Fourier_Transform)

## References

1.  ^    [Chung, Fan](https://en.wikipedia.org/wiki/Fan_Chung) (1997) \[1992\]. [Spectral Graph Theory](https://www.math.ucsd.edu/~fan/research/revised.html). American Mathematical Society. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0821803158](https://en.wikipedia.org/wiki/Special:BookSources/978-0821803158).
2.  Smola, Alexander J.; Kondor, Risi (2003), "Kernels and regularization on graphs", *Learning Theory and Kernel Machines: 16th Annual Conference on Learning Theory and 7th Kernel Workshop, COLT/Kernel 2003, Washington, DC, USA, August 24–27, 2003, Proceedings*, Lecture Notes in Computer Science, vol. 2777, Springer, pp. 144–158, [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.3.7020](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.3.7020), [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-540-45167-9_12](https://doi.org/10.1007%2F978-3-540-45167-9_12), [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-3-540-40720-1](https://en.wikipedia.org/wiki/Special:BookSources/978-3-540-40720-1).
3.  Godsil, C.; Royle, G. (2001). *Algebraic Graph Theory, Graduate Texts in Mathematics*. Springer-Verlag.
4.  Satoshi Furutani; Toshiki Shibahara; Mitsuaki Akiyama; Kunio Hato; Masaki Aida (2020). [Graph Signal Processing for Directed Graphs based on the Hermitian Laplacian](https://ecmlpkdd2019.org/downloads/paper/499.pdf) (PDF). ECML PKDD 2019: Machine Learning and Knowledge Discovery in Databases. pp. 447–463. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/978-3-030-46150-8_27](https://doi.org/10.1007%2F978-3-030-46150-8_27).
5.  Morbidi, F. (2013). ["The Deformed Consensus Protocol"](https://hal.archives-ouvertes.fr/docs/00/96/14/91/PDF/Morbidi_AUTO13_ExtVer.pdf) (PDF). *Automatica*. **49** (10): 3049–3055. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.automatica.2013.07.006](https://doi.org/10.1016%2Fj.automatica.2013.07.006). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [205767404](https://api.semanticscholar.org/CorpusID:205767404).
6.  Cvetković, Dragoš; Simić, Slobodan K. (2010). ["Towards a Spectral Theory of Graphs Based on the Signless Laplacian, III"](https://doi.org/10.2298%2FAADM1000001C). *Applicable Analysis and Discrete Mathematics*. **4** (1): 156–166. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.2298/AADM1000001C](https://doi.org/10.2298%2FAADM1000001C). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1452-8630](https://search.worldcat.org/issn/1452-8630). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [43671298](https://www.jstor.org/stable/43671298).
7.  Chaiken, S.; [Kleitman, D.](https://en.wikipedia.org/wiki/Daniel_Kleitman) (1978). ["Matrix Tree Theorems"](https://doi.org/10.1016%2F0097-3165%2878%2990067-5). *Journal of Combinatorial Theory, Series A*. **24** (3): 377–381. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/0097-3165(78)90067-5](https://doi.org/10.1016%2F0097-3165%2878%2990067-5). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0097-3165](https://search.worldcat.org/issn/0097-3165).
8.  ["SciPy"](https://github.com/scipy/scipy/blob/main/scipy/sparse/csgraph/_laplacian.py). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 4 October 2023.
9.  ["NetworkX"](https://github.com/networkx/networkx/blob/main/networkx/linalg/laplacianmatrix.py). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 4 October 2023.
10. ["Julia"](https://github.com/JuliaGraphs/Graphs.jl/blob/0fa5f52856f7f779e8f2ca49bc6cee26e5e19b50/src/linalg/spectral.jl#L78-L88). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 4 October 2023.
11. ["2.3. Clustering"](https://scikit-learn.org/stable/modules/clustering.html#spectral-clustering).
12. ["PyGSP: Graph Signal Processing in Python"](https://github.com/epfl-lts2/pygsp). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 23 March 2022.
13. ["Megaman: Manifold Learning for Millions of Points"](https://github.com/mmp2/megaman). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 14 March 2022.
14. ["SmoothG"](https://github.com/LLNL/smoothG). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 17 September 2020.
15. ["Announcing Our Paper at KDD 2020"](https://complexdatalabmcgill.github.io/papers/post-andy-kdd2020paper/). 2 July 2020.
16. ["Harshangrjn/LaplacianOpt.jl"](https://github.com/harshangrjn/LaplacianOpt.jl). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 2 February 2022.
17. ["LigMG (Large Irregular Graph MultiGrid)-- A distributed memory graph Laplacian solver for large irregular graphs"](https://github.com/ligmg/ligmg). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 5 January 2022.
18. ["Laplacians.jl"](https://github.com/danspielman/Laplacians.jl). *[GitHub](https://en.wikipedia.org/wiki/GitHub)*. 11 March 2022.
