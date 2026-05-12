[[optimization.base]]

> Source: [Quadratic unconstrained binary optimization](https://en.wikipedia.org/wiki/Quadratic_unconstrained_binary_optimization)
> License: Wikipedia content is available under CC BY-SA 4.0.

**Quadratic unconstrained binary optimization** (**QUBO**), also known as **unconstrained binary quadratic programming** (**UBQP**), is a combinatorial [optimization problem](https://en.wikipedia.org/wiki/Optimization_problem) with a wide range of applications from [finance](https://en.wikipedia.org/wiki/Finance) and [economics](https://en.wikipedia.org/wiki/Economics) to [machine learning](https://en.wikipedia.org/wiki/Machine_learning). QUBO is an [NP hard](https://en.wikipedia.org/wiki/NP_hard) problem, and for many classical problems from [theoretical computer science](https://en.wikipedia.org/wiki/Theoretical_computer_science), like [maximum cut](https://en.wikipedia.org/wiki/Maximum_cut), [graph coloring](https://en.wikipedia.org/wiki/Graph_coloring) and the [partition problem](https://en.wikipedia.org/wiki/Partition_problem), embeddings into QUBO have been formulated. Embeddings for machine learning models include [support-vector machines](https://en.wikipedia.org/wiki/Support-vector_machine), [clustering](https://en.wikipedia.org/wiki/Cluster_analysis) and [probabilistic graphical models](https://en.wikipedia.org/wiki/Probabilistic_graphical_model). Moreover, due to its close connection to [Ising models](https://en.wikipedia.org/wiki/Ising_model), QUBO constitutes a central problem class for [adiabatic quantum computation](https://en.wikipedia.org/wiki/Adiabatic_quantum_computing), where it is solved through a physical process called [quantum annealing](https://en.wikipedia.org/wiki/Quantum_annealing).

## Definition

Let $\mathbb {B} =\lbrace 0,1\rbrace$ the set of [binary](https://en.wikipedia.org/wiki/Binary_data) digits (or *bits*), then $\mathbb {B} ^{n}$ is the set of binary vectors of fixed length $n\in \mathbb {N}$. Given a [symmetric](https://en.wikipedia.org/wiki/Symmetric_matrix) or upper [triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix) ${\boldsymbol {Q}}\in \mathbb {R} ^{n\times n}$, whose entries $Q_{ij}$ define a weight for each pair of indices $i,j\in \lbrace 1,\dots ,n\rbrace$, we can define the function $f_{\boldsymbol {Q}}:\mathbb {B} ^{n}\rightarrow \mathbb {R}$ that assigns a value to each binary vector ${\boldsymbol {x}}$ through

$f_{\boldsymbol {Q}}({\boldsymbol {x}})={\boldsymbol {x}}^{\intercal }{\boldsymbol {Qx}}=\sum _{i=1}^{n}\sum _{j=1}^{n}Q_{ij}x_{i}x_{j}.$

Alternatively, the linear and quadratic parts can be separated as

$f_{{\boldsymbol {Q}}',{\boldsymbol {q}}}({\boldsymbol {x}})={\boldsymbol {x}}^{\intercal }{\boldsymbol {Q}}'{\boldsymbol {x}}+{\boldsymbol {q}}^{\intercal }{\boldsymbol {x}},$

where ${\boldsymbol {Q}}'\in \mathbb {R} ^{n\times n}$ and ${\boldsymbol {q}}\in \mathbb {R} ^{n}$. This is equivalent to the previous definition through ${\boldsymbol {Q}}={\boldsymbol {Q}}'+\operatorname {diag} [{\boldsymbol {q}}]$ using the [diag](https://en.wikipedia.org/wiki/Diagonal_matrix#Vector-to-matrix_diag_operator) operator, exploiting that $x=x\cdot x$ for all binary values $x$.

Intuitively, the weight $Q_{ij}$ is added if both $x_{i}=1$ and $x_{j}=1$. The QUBO problem consists of finding a binary vector ${\boldsymbol {x}}^{*}$ that minimizes $f_{\boldsymbol {Q}}$, i.e., $\forall {\boldsymbol {x}}\in \mathbb {B} ^{n}:~f_{\boldsymbol {Q}}({\boldsymbol {x}}^{*})\leq f_{\boldsymbol {Q}}({\boldsymbol {x}})$.

In general, ${\boldsymbol {x}}^{*}$ is not unique, meaning there may be a set of minimizing vectors with equal value w.r.t. $f_{\boldsymbol {Q}}$. The complexity of QUBO arises from the number of candidate binary vectors to be evaluated, as $\left|\mathbb {B} ^{n}\right|=2^{n}$ grows exponentially in $n$.

Sometimes, QUBO is defined as the problem of *maximizing* $f_{\boldsymbol {Q}}$, which is equivalent to minimizing $f_{-{\boldsymbol {Q}}}=-f_{\boldsymbol {Q}}$.

## Properties

QUBO is scale invariant for positive factors $\alpha >0$, which leave the optimum ${\boldsymbol {x}}^{*}$ unchanged:

$f_{\alpha {\boldsymbol {Q}}}({\boldsymbol {x}})={\boldsymbol {x}}^{\intercal }(\alpha {\boldsymbol {Q}}){\boldsymbol {x}}=\alpha ({\boldsymbol {x}}^{\intercal }{\boldsymbol {Qx}})=\alpha f_{\boldsymbol {Q}}({\boldsymbol {x}})$.

In its general form, QUBO is [NP-hard](https://en.wikipedia.org/wiki/NP-hardness) and cannot be solved efficiently by any polynomial-time algorithm. However, there are polynomially-solvable special cases, where ${\boldsymbol {Q}}$ has certain properties, for example:

- If all coefficients are positive, the optimum is trivially ${\boldsymbol {x}}^{*}=(0,\dots ,0)^{\intercal }$. Similarly, if all coefficients are negative, the optimum is ${\boldsymbol {x}}^{*}=(1,\dots ,1)^{\intercal }$.
- If ${\boldsymbol {Q}}$ is [diagonal](https://en.wikipedia.org/wiki/Diagonal_matrix), the bits can be optimized independently, and the problem is solvable in ${\mathcal {O}}(n)$. The optimal variable assignments are simply $x_{i}^{*}=1$ if $Q_{ii}<0$, and $x_{i}^{*}=0$ otherwise.
- If all off-diagonal elements of ${\boldsymbol {Q}}$ are non-positive, the corresponding QUBO problem is solvable in polynomial time.

QUBO can be solved using [integer linear programming](https://en.wikipedia.org/wiki/Integer_linear_programming) solvers like [CPLEX](https://en.wikipedia.org/wiki/CPLEX) or [Gurobi Optimizer](https://en.wikipedia.org/wiki/Gurobi_Optimizer). This is possible since QUBO can be reformulated as a linear constrained binary optimization problem. To achieve this, substitute the product $x_{i}x_{j}$ by an additional binary variable $z_{ij}\in \mathbb {B}$ and add the constraints $x_{i}\geq z_{ij}$, $x_{j}\geq z_{ij}$ and $x_{i}+x_{j}-1\leq z_{ij}$. Note that $z_{ij}$ can also be [relaxed](https://en.wikipedia.org/wiki/Linear_programming_relaxation) to continuous variables within the bounds zero and one.

## Applications

QUBO is a structurally simple, yet computationally hard optimization problem. It can be used to encode a wide range of optimization problems from various scientific areas.

### Maximum Cut

Given a graph $G=(V,E)$ with vertex set $V=\lbrace 1,\dots ,n\rbrace$ and edges $E\subseteq V\times V$, the [maximum cut](https://en.wikipedia.org/wiki/Maximum_cut) (max-cut) problem consists of finding two subsets $S,T\subseteq V$ with $T=V\setminus S$, such that the number of edges between $S$ and $T$ is maximized.

The more general *weighted max-cut* problem assumes edge weights $w_{ij}\geq 0~\forall i,j\in V$, with $(i,j)\notin E\Rightarrow w_{ij}=0$, and asks for a [partition](https://en.wikipedia.org/wiki/Partition_of_a_set) $S,T\subseteq V$ that maximizes the sum of edge weights between $S$ and $T$, i.e.,

$\max _{S\subseteq V}\sum _{i\in S,j\notin S}w_{ij}.$

By setting $w_{ij}=1$ for all $(i,j)\in E$ this becomes equivalent to the original max-cut problem above, which is why we focus on this more general form in the following.

For every vertex in $i\in V$ we introduce a binary variable $x_{i}$ with the interpretation *$x_{i}=0$ if $i\in S$* and *$x_{i}=1$ if $i\in T$*. As $T=V\setminus S$, every $i$ is in exactly one set, meaning there is a 1:1 correspondence between binary vectors ${\boldsymbol {x}}\in \mathbb {B} ^{n}$ and partitions of $V$ into two subsets.

We observe that, for any $i,j\in V$, the expression $x_{i}(1-x_{j})+(1-x_{i})x_{j}$ evaluates to 1 if and only if $i$ and $j$ are in different subsets, equivalent to [logical XOR](https://en.wikipedia.org/wiki/Logical_XOR). Let ${\boldsymbol {W}}\in \mathbb {R} _{+}^{n\times n}$ with $W_{ij}=w_{ij}~\forall i,j\in V$. By extending above expression to matrix-vector form we find that

${\boldsymbol {x}}^{\intercal }{\boldsymbol {W}}({\boldsymbol {1}}-{\boldsymbol {x}})+({\boldsymbol {1}}-{\boldsymbol {x}})^{\intercal }{\boldsymbol {Wx}}=-2{\boldsymbol {x}}^{\intercal }{\boldsymbol {Wx}}+({\boldsymbol {W1}}+{\boldsymbol {W}}^{\intercal }{\boldsymbol {1}})^{\intercal }{\boldsymbol {x}}$

is the sum of weights of all edges between $S$ and $T$, where ${\boldsymbol {1}}=(1,1,\dots ,1)^{\intercal }\in \mathbb {R} ^{n}$. As this is a quadratic function over ${\boldsymbol {x}}$, it is a QUBO problem whose parameter matrix we can read from above expression as

${\boldsymbol {Q}}=2{\boldsymbol {W}}-\operatorname {diag} [{\boldsymbol {W1}}+{\boldsymbol {W}}^{\intercal }{\boldsymbol {1}}],$

after flipping the sign to make it a minimization problem.

### Cluster Analysis

Binary Clustering with QUBO

![[media/7cd3a01f1ad7007b14907ff49ffdfa4ecff82f74.png]]

A bad cluster assignment.

![[media/99ae7cd4cf57abc0175f3bc99e1ec3bb436cce89.png]]

A good cluster assignment.

Visual representation of a clustering problem with 20 points: Circles of the same color belong to the same cluster. Each circle can be understood as a binary variable in the corresponding QUBO problem.

Next, we consider the problem of [cluster analysis](https://en.wikipedia.org/wiki/Cluster_analysis), where we are given a set of $N$ points in $d$-dimensional space and want to assign each point to one of two classes or *clusters*, such that points in the same cluster are similar to each other. For this example we set $N=20$ and $d=2$. The data is given as a matrix ${\boldsymbol {X}}\in \mathbb {R} ^{20\times 2}$, where each row contains two [cartesian coordinates](https://en.wikipedia.org/wiki/Cartesian_coordinate_system). For two clusters, we can assign a binary variable $x_{i}\in \mathbb {B}$ to the point corresponding to the $i$-th row in ${\boldsymbol {X}}$, indicating whether it belongs to the first ($x_{i}=0$) or second cluster ($x_{i}=1$). Consequently, we have 20 binary variables, which form a binary vector ${\boldsymbol {x}}\in \mathbb {B} ^{20}$ that corresponds to a cluster assignment of all points (see figure).

One way to derive a clustering is to consider the pairwise distances between points. Given a cluster assignment ${\boldsymbol {x}}$, the expression $x_{i}x_{j}+(1-x_{i})(1-x_{j})$ evaluates to 1 if points $i$ and $j$ are in the same cluster. Similarly, $x_{i}(1-x_{j})+(1-x_{i})x_{j}=1$ indicates that they are in different clusters. Let $d_{ij}>0$ denote the [Euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance) between the points $i$ and $j$, i.e.,

$d_{ij}={\sqrt {{\boldsymbol {X}}_{i}^{\intercal }{\boldsymbol {X}}_{j}}}$,

where ${\boldsymbol {X}}_{i}$ is the $i$-th row of ${\boldsymbol {X}}$.

In order to define a cost function to minimize, when points $i$ and $j$ are in the same cluster we add their positive distance $d_{ij}$, and subtract it when they are in different clusters. This way, an optimal solution tends to place points which are far apart into different clusters, and points that are close into the same cluster.

Let ${\boldsymbol {D}}\in \mathbb {R} ^{N\times N}$ with $D_{ij}=d_{ij}/2$ for all $i,j\in \lbrace 1,\dots ,n\rbrace$. Given an assignment ${\boldsymbol {x}}\in \mathbb {B} ^{N}$, such a cost function is given by

${\begin{aligned}f({\boldsymbol {x}})&={\boldsymbol {x}}^{\intercal }{\boldsymbol {Dx}}-{\boldsymbol {x}}^{\intercal }{\boldsymbol {D}}({\boldsymbol {1}}-{\boldsymbol {x}})-({\boldsymbol {1}}-{\boldsymbol {x}})^{\intercal }{\boldsymbol {Dx}}+({\boldsymbol {1}}-{\boldsymbol {x}})^{\intercal }{\boldsymbol {D}}({\boldsymbol {1}}-{\boldsymbol {x}})\\&=4{\boldsymbol {x}}^{\intercal }{\boldsymbol {D}}{\boldsymbol {x}}-4{\boldsymbol {1}}^{\intercal }{\boldsymbol {D}}{\boldsymbol {x}}+{\boldsymbol {1}}^{\intercal }{\boldsymbol {D1}},\end{aligned}}$

where ${\boldsymbol {1}}=(1,1,\dots ,1)^{\intercal }\in \mathbb {R} ^{N}$.

From the second line we can see that this expression can be re-arranged to a QUBO problem by defining

${\boldsymbol {Q}}=4{\boldsymbol {D}}-4\operatorname {diag} [{\boldsymbol {D1}}]$

and ignoring the constant term ${\boldsymbol {1}}^{\intercal }{\boldsymbol {D1}}$. Using these parameters, a binary vector minimizing this QUBO instance ${\boldsymbol {Q}}$ will correspond to an optimal cluster assignment w.r.t. above cost function.

## Connection to Ising models

QUBO is very closely related and computationally equivalent to the [Ising model](https://en.wikipedia.org/wiki/Ising_model), whose [Hamiltonian function](https://en.wikipedia.org/wiki/Hamiltonian_function) is defined as

$H({\boldsymbol {\sigma }})={\boldsymbol {\sigma }}^{\intercal }{\boldsymbol {J}}{\boldsymbol {\sigma }}+{\boldsymbol {h}}^{\intercal }{\boldsymbol {\sigma }}=\sum _{i,j}J_{ij}\sigma _{i}\sigma _{j}+\sum _{j}h_{j}\sigma _{j}$

with real-valued parameters $h_{j},J_{ij}$ for all $i,j$. The *spin variables* $\sigma _{j}$ are binary with values from $\lbrace -1,+1\rbrace$ instead of $\mathbb {B}$. Note that this formulation is simplified, since, in a physics context, $\sigma _{i}$ are typically [Pauli operators](https://en.wikipedia.org/wiki/Pauli_matrix), which are complex-valued matrices of size $2^{n}\times 2^{n}$, whereas here we treat them as binary variables. Many formulations of the Ising model Hamiltonian further assume that the variables are arranged in a lattice, where only neighboring pairs of variables $\langle i~j\rangle$ can have non-zero coefficients; here, we simply assume that $J_{ij}=0$ if $i$ and $j$ are not neighbors.

Applying the identity $\sigma =1-2x$ yields an equivalent QUBO problem 

${\begin{aligned}&{\boldsymbol {\sigma }}^{\intercal }{\boldsymbol {J}}{\boldsymbol {\sigma }}+{\boldsymbol {h}}^{\intercal }{\boldsymbol {\sigma }}\\&=({\boldsymbol {1}}-2{\boldsymbol {x}})^{\intercal }{\boldsymbol {J}}({\boldsymbol {1}}-2{\boldsymbol {x}})+{\boldsymbol {h}}^{\intercal }({\boldsymbol {1}}-2{\boldsymbol {x}})\\&=4{\boldsymbol {x}}^{\intercal }{\boldsymbol {J}}{\boldsymbol {x}}-4{\boldsymbol {1}}^{\intercal }{\boldsymbol {Jx}}+{\boldsymbol {1}}^{\intercal }{\boldsymbol {J1}}-2{\boldsymbol {h}}^{\intercal }{\boldsymbol {x}}+{\boldsymbol {h}}^{\intercal }{\boldsymbol {1}}\\&={\boldsymbol {x}}^{\intercal }(4{\boldsymbol {J}}){\boldsymbol {x}}-(4{\boldsymbol {J}}^{\intercal }{\boldsymbol {1}}+2{\boldsymbol {h}})^{\intercal }{\boldsymbol {x}}+\underbrace {{\boldsymbol {1}}^{\intercal }{\boldsymbol {J1}}+{\boldsymbol {h}}^{\intercal }{\boldsymbol {1}}} _{\text{const.}},\end{aligned}}$

whose weight matrix ${\boldsymbol {Q}}$ is given by

${\boldsymbol {Q}}=4{\boldsymbol {J}}-\operatorname {diag} [4{\boldsymbol {J}}^{\intercal }{\boldsymbol {1}}+2{\boldsymbol {h}}],$

again ignoring the constant term, which does not affect the minization. Using the identity $x=(1-\sigma )/2$, a QUBO problem with matrix ${\boldsymbol {Q}}$ can be converted to an equivalent Ising model using the same technique, yielding

${\begin{aligned}{\boldsymbol {J}}&={\boldsymbol {Q}}/4,&{\boldsymbol {h}}&=-({\boldsymbol {Q1}}+{\boldsymbol {Q}}^{\intercal }{\boldsymbol {1}})/4,\end{aligned}}$

and a constant offset of ${\boldsymbol {1}}^{\intercal }{\boldsymbol {Q1}}/4$.

## References

1.  Kochenberger, Gary; Hao, Jin-Kao; Glover, Fred; Lewis, Mark; Lu, Zhipeng; Wang, Haibo; Wang, Yang (2014). ["The unconstrained binary quadratic programming problem: a survey"](https://leeds-faculty.colorado.edu/glover/454%20-%20xQx%20survey%20article%20as%20published%202014.pdf) (PDF). *Journal of Combinatorial Optimization*. **28**: 58–81. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10878-014-9734-0](https://doi.org/10.1007%2Fs10878-014-9734-0). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16808394](https://api.semanticscholar.org/CorpusID:16808394).
2.  Glover, Fred; Kochenberger, Gary (2019). "A Tutorial on Formulating and Using QUBO Models". [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1811.11538](https://arxiv.org/abs/1811.11538) \[[cs.DS](https://arxiv.org/archive/cs.DS)\].
3.  Lucas, Andrew (2014). ["Ising formulations of many NP problems"](https://doi.org/10.3389%2Ffphy.2014.00005). *Frontiers in Physics*. **2**: 5. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1302.5843](https://arxiv.org/abs/1302.5843). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2014FrP.....2....5L](https://ui.adsabs.harvard.edu/abs/2014FrP.....2....5L). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.3389/fphy.2014.00005](https://doi.org/10.3389%2Ffphy.2014.00005).
4.  Mücke, Sascha; Piatkowski, Nico; [Morik, Katharina](https://en.wikipedia.org/wiki/Katharina_Morik) (2019). ["Learning Bit by Bit: Extracting the Essence of Machine Learning"](https://web.archive.org/web/20200227143739/https://pdfs.semanticscholar.org/f484/b4a789e1563b91a416a7cfabbf72f0aa3b2a.pdf) (PDF). *LWDA*. [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [202760166](https://api.semanticscholar.org/CorpusID:202760166). Archived from [the original](https://pdfs.semanticscholar.org/f484/b4a789e1563b91a416a7cfabbf72f0aa3b2a.pdf) (PDF) on 2020-02-27.
5.  Tom Simonite (8 May 2013). ["D-Wave's Quantum Computer Goes to the Races, Wins"](https://web.archive.org/web/20150924141050/http://www.technologyreview.com/view/514686/d-waves-quantum-computer-goes-to-the-races-wins/). MIT Technology Review. Archived from [the original](http://www.technologyreview.com/view/514686/d-waves-quantum-computer-goes-to-the-races-wins/) on 24 September 2015. Retrieved 12 May 2013.
6.  A. P. Punnen (editor), Quadratic unconstrained binary optimization problem: Theory, Algorithms, and Applications, Springer, Springer, 2022.
7.  Çela, E., Punnen, A.P. (2022). Complexity and Polynomially Solvable Special Cases of QUBO. In: Punnen, A.P. (eds) The Quadratic Unconstrained Binary Optimization Problem. Springer, Cham. [https://doi.org/10.1007/978-3-031-04520-2_3](https://doi.org/10.1007/978-3-031-04520-2_3)
8.  See Theorem 3.16 in Punnen (2022); note that the authors assume the *maximization* version of QUBO.
9.  Ratke, Daniel (2021-06-10). ["List of QUBO formulations"](https://blog.xa0.de/post/List-of-QUBO-formulations/). Retrieved 2022-12-16.
10. ^   Mücke, S. (2025). Quantum-Classical Optimization in Machine Learning. Shaker Verlag. [https://d-nb.info/1368090214](https://d-nb.info/1368090214)

## External links

- [QUBO Benchmark](http://plato.asu.edu/ftp/qubo.html) (Benchmark of software packages for the exact solution of QUBOs; part of the well-known Mittelmann benchmark collection)
- Endre Boros, Peter L Hammer & Gabriel Tavares (April 2007). ["Local search heuristics for Quadratic Unconstrained Binary Optimization (QUBO)"](http://portal.acm.org/citation.cfm?id=1231283). *Journal of Heuristics*. **13** (2). Association for Computing Machinery: 99–132. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s10732-007-9009-3](https://doi.org/10.1007%2Fs10732-007-9009-3). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [32887708](https://api.semanticscholar.org/CorpusID:32887708). Retrieved 12 May 2013.
- Di Wang & Robert Kleinberg (November 2009). ["Analyzing quadratic unconstrained binary optimization problems via multicommodity flows"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2808708). *Discrete Applied Mathematics*. **157** (18). Elsevier: 3746–3753. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.dam.2009.07.009](https://doi.org/10.1016%2Fj.dam.2009.07.009). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [2808708](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2808708). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [20161596](https://pubmed.ncbi.nlm.nih.gov/20161596).
- [Hiroshima University and NTT DATA Group Corporation : "QUBO++ with ABS2 GPU QUBO Solver"](https://abs2.cs.hiroshima-u.ac.jp/) \# Software.
