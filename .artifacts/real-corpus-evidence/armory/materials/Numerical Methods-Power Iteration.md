[[numerical-methods.base]]

> Source: [[Power Iteration]]
> License: Wikipedia content is available under CC BY-SA 4.0.

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), **power iteration** (also known as the **power method**) is an [eigenvalue algorithm](https://en.wikipedia.org/wiki/Eigenvalue_algorithm): given a [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable) [matrix](https://en.wikipedia.org/wiki/Matrix_(mathematics) "Matrix (mathematics)") $A$, the algorithm will produce a number $\lambda$, which is the greatest (in absolute value) [eigenvalue](https://en.wikipedia.org/wiki/Eigenvalue) of $A$, and a nonzero vector $v$, which is a corresponding [eigenvector](https://en.wikipedia.org/wiki/Eigenvector) of $\lambda$, that is, $Av=\lambda v$. The algorithm is also known as the **[Von Mises](https://en.wikipedia.org/wiki/Richard_von_Mises) iteration**.

Power iteration is a very simple algorithm, but it may converge slowly. The most time-consuming operation of the algorithm is the multiplication of matrix $A$ by a vector, so it is effective for a very large [sparse matrix](https://en.wikipedia.org/wiki/Sparse_matrix) with appropriate implementation. The speed of convergence is like $(\lambda _{2}/\lambda _{1})^{k}$ where $k$ is the number of iterations, and $\lambda _{1}$ and $\lambda _{2}$ are, respectively, the eigenvalue of largest absolute value and an eigenvalue of second-largest absolute value (see a [later section](#Analysis)). In other words, convergence is exponential with base being the [spectral gap](https://en.wikipedia.org/wiki/Spectral_gap).

## The method

![[media/ae8451c2e84da1d576f0258679cc904e7d23456b.gif]]
Animation that visualizes the power iteration algorithm on a 2x2 matrix. The matrix is depicted by its two eigenvectors. Error is computed as $||{\text{approximation}}-{\text{largest eigenvector}}||$

The power iteration algorithm starts with a vector $b_{0}$, which may be an approximation to the dominant eigenvector or a random vector. The method is described by the [recurrence relation](https://en.wikipedia.org/wiki/Recurrence_relation)

$b_{k+1}={\frac {Ab_{k}}{\|Ab_{k}\|}}$

So, at every iteration, the vector $b_{k}$ is multiplied by the matrix $A$ and normalized.

If we assume $A$ has an eigenvalue that is strictly greater in magnitude than its other eigenvalues and the starting vector $b_{0}$ has a nonzero component in the direction of an eigenvector associated with the dominant eigenvalue, then a subsequence $\left(b_{k}\right)$ converges to an eigenvector associated with the dominant eigenvalue.

Without the two assumptions above, the sequence $\left(b_{k}\right)$ does not necessarily converge. In this sequence,

$b_{k}=e^{i\phi _{k}}v_{1}+r_{k}$,

where $v_{1}$ is an eigenvector associated with the dominant eigenvalue, and $\|r_{k}\|\rightarrow 0$. The presence of the term $e^{i\phi _{k}}$ implies that $\left(b_{k}\right)$ does not converge unless $e^{i\phi _{k}}=1$. Under the two assumptions listed above, the sequence $\left(\mu _{k}\right)$ defined by

$\mu _{k}={\frac {b_{k}^{*}Ab_{k}}{b_{k}^{*}b_{k}}}$

converges to the dominant eigenvalue (with [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient)).<sup>\[*[clarification needed](https://en.wikipedia.org/wiki/Wikipedia:Please_clarify)*\]</sup>

One may compute this with the following algorithm (shown in Python with NumPy):

    #!/usr/bin/env python3

    import numpy as np

    def power_iteration(A: np.ndarray, num_iterations: int) -> np.ndarray:
        # Ideally choose a random vector
        # To decrease the chance that our vector
        # Is orthogonal to the eigenvector
        b_k = np.random.rand(A.shape[1])

        for _ in range(num_iterations):
            # calculate the matrix-by-vector product Ab
            b_k1 = np.dot(A, b_k)

            # calculate the norm
            b_k1_norm = np.linalg.norm(b_k1)

            # re normalize the vector
            b_k = b_k1 / b_k1_norm

        return b_k

    power_iteration(np.array([[0.5, 0.5], [0.2, 0.8]]), 10)

The vector $b_{k}$ converges to an associated eigenvector. Ideally, one should use the [Rayleigh quotient](https://en.wikipedia.org/wiki/Rayleigh_quotient) in order to get the associated eigenvalue.

This algorithm is used to calculate the *Google [PageRank](https://en.wikipedia.org/wiki/PageRank)*.

The method can also be used to calculate the [spectral radius](https://en.wikipedia.org/wiki/Spectral_radius) (the eigenvalue with the largest magnitude, for a square matrix) by computing the Rayleigh quotient

$\rho (A)=\max \left\{|\lambda _{1}|,\dotsc ,|\lambda _{n}|\right\}={\frac {b_{k}^{\top }Ab_{k}}{b_{k}^{\top }b_{k}}}.$

## Analysis

Let $A$ be decomposed into its [Jordan canonical form](https://en.wikipedia.org/wiki/Jordan_canonical_form): $A=VJV^{-1}$, where the first column of $V$ is an eigenvector of $A$ corresponding to the dominant eigenvalue $\lambda _{1}$. Since [generically](https://en.wikipedia.org/wiki/Generic_property), the dominant eigenvalue of $A$ is unique, the first Jordan block of $J$ is the $1\times 1$ matrix $[\lambda _{1}],$ where $\lambda _{1}$ is the largest eigenvalue of $A$ in magnitude. The starting vector $b_{0}$ can be written as a linear combination of the columns of $V$:

$b_{0}=c_{1}v_{1}+c_{2}v_{2}+\cdots +c_{n}v_{n}.$

By assumption, $b_{0}$ has a nonzero component in the direction of the dominant eigenvector, so $c_{1}\neq 0$.

The computationally useful [recurrence relation](https://en.wikipedia.org/wiki/Recurrence_relation) for $b_{k+1}$ can be rewritten as:

$b_{k+1}={\frac {Ab_{k}}{\|Ab_{k}\|}}={\frac {A^{k+1}b_{0}}{\|A^{k+1}b_{0}\|}},$

where the expression: ${\frac {A^{k+1}b_{0}}{\|A^{k+1}b_{0}\|}}$ is more amenable to the following analysis.

${\begin{aligned}b_{k}&={\frac {A^{k}b_{0}}{\|A^{k}b_{0}\|}}\\&={\frac {\left(VJV^{-1}\right)^{k}b_{0}}{\|\left(VJV^{-1}\right)^{k}b_{0}\|}}\\&={\frac {VJ^{k}V^{-1}b_{0}}{\|VJ^{k}V^{-1}b_{0}\|}}\\&={\frac {VJ^{k}V^{-1}\left(c_{1}v_{1}+c_{2}v_{2}+\cdots +c_{n}v_{n}\right)}{\|VJ^{k}V^{-1}\left(c_{1}v_{1}+c_{2}v_{2}+\cdots +c_{n}v_{n}\right)\|}}\\&={\frac {VJ^{k}\left(c_{1}e_{1}+c_{2}e_{2}+\cdots +c_{n}e_{n}\right)}{\|VJ^{k}\left(c_{1}e_{1}+c_{2}e_{2}+\cdots +c_{n}e_{n}\right)\|}}\\&=\left({\frac {\lambda _{1}}{|\lambda _{1}|}}\right)^{k}{\frac {c_{1}}{|c_{1}|}}{\frac {v_{1}+{\frac {1}{c_{1}}}V\left({\frac {1}{\lambda _{1}}}J\right)^{k}\left(c_{2}e_{2}+\cdots +c_{n}e_{n}\right)}{\left\|v_{1}+{\frac {1}{c_{1}}}V\left({\frac {1}{\lambda _{1}}}J\right)^{k}\left(c_{2}e_{2}+\cdots +c_{n}e_{n}\right)\right\|}}\end{aligned}}$

The expression above simplifies as $k\to \infty$

$\left({\frac {1}{\lambda _{1}}}J\right)^{k}={\begin{bmatrix}[1]&&&&\\&\left({\frac {1}{\lambda _{1}}}J_{2}\right)^{k}&&&\\&&\ddots &\\&&&\left({\frac {1}{\lambda _{1}}}J_{m}\right)^{k}\\\end{bmatrix}}\rightarrow {\begin{bmatrix}1&&&&\\&0&&&\\&&\ddots &\\&&&0\\\end{bmatrix}}\quad {\text{as}}\quad k\to \infty .$

The limit follows from the fact that the eigenvalue of ${\frac {1}{\lambda _{1}}}J_{i}$ is less than 1 in magnitude, so

$\left({\frac {1}{\lambda _{1}}}J_{i}\right)^{k}\to 0\quad {\text{as}}\quad k\to \infty .$

It follows that:

${\frac {1}{c_{1}}}V\left({\frac {1}{\lambda _{1}}}J\right)^{k}\left(c_{2}e_{2}+\cdots +c_{n}e_{n}\right)\to 0\quad {\text{as}}\quad k\to \infty$

Using this fact, $b_{k}$ can be written in a form that emphasizes its relationship with $v_{1}$ when $k$ is large:

${\begin{aligned}b_{k}&=\left({\frac {\lambda _{1}}{|\lambda _{1}|}}\right)^{k}{\frac {c_{1}}{|c_{1}|}}{\frac {v_{1}+{\frac {1}{c_{1}}}V\left({\frac {1}{\lambda _{1}}}J\right)^{k}\left(c_{2}e_{2}+\cdots +c_{n}e_{n}\right)}{\left\|v_{1}+{\frac {1}{c_{1}}}V\left({\frac {1}{\lambda _{1}}}J\right)^{k}\left(c_{2}e_{2}+\cdots +c_{n}e_{n}\right)\right\|}}\\[6pt]&=e^{i\phi _{k}}{\frac {c_{1}}{|c_{1}|}}{\frac {v_{1}}{\|v_{1}\|}}+r_{k}\end{aligned}}$

where $e^{i\phi _{k}}=\left(\lambda _{1}/|\lambda _{1}|\right)^{k}$ and $\|r_{k}\|\to 0$ as $k\to \infty$

The sequence $\left(b_{k}\right)$ is bounded, so it contains a convergent subsequence. Note that the eigenvector corresponding to the dominant eigenvalue is only unique up to a scalar, so although the sequence $\left(b_{k}\right)$ may not converge, $b_{k}$ is nearly an eigenvector of $A$ for large $k$.

Alternatively, if $A$ is [diagonalizable](https://en.wikipedia.org/wiki/Diagonalizable), then the following proof yields the same result:

Let $\lambda _{1},\lambda _{2},\ldots ,\lambda _{m}$ be the $m$ eigenvalues (counted with multiplicity) of $A$ in the order of descending absolute value (equalities allowed), that is $|\lambda _{1}|\geq |\lambda _{2}|\ldots \geq |\lambda _{m}|$, and let $v_{1},v_{2},\ldots ,v_{m}$ be the corresponding eigenvectors. Suppose that $\lambda _{1}$ is the dominant eigenvalue, so that $|\lambda _{1}|>|\lambda _{j}|$ for $j>1$.

The initial vector $b_{0}$ can be written:

$b_{0}=c_{1}v_{1}+c_{2}v_{2}+\cdots +c_{m}v_{m}.$

If $b_{0}$ is chosen randomly (with uniform probability), then $c_{1}\neq 0$ with [probability 1](https://en.wikipedia.org/wiki/Almost_surely). Now,

${\begin{aligned}A^{k}b_{0}&=c_{1}A^{k}v_{1}+c_{2}A^{k}v_{2}+\cdots +c_{m}A^{k}v_{m}\\&=c_{1}\lambda _{1}^{k}v_{1}+c_{2}\lambda _{2}^{k}v_{2}+\cdots +c_{m}\lambda _{m}^{k}v_{m}\\&=c_{1}\lambda _{1}^{k}\left(v_{1}+{\frac {c_{2}}{c_{1}}}\left({\frac {\lambda _{2}}{\lambda _{1}}}\right)^{k}v_{2}+\cdots +{\frac {c_{m}}{c_{1}}}\left({\frac {\lambda _{m}}{\lambda _{1}}}\right)^{k}v_{m}\right)\\&\to c_{1}\lambda _{1}^{k}v_{1}&&\left|{\frac {\lambda _{j}}{\lambda _{1}}}\right|<1{\text{ for }}j>1\end{aligned}}$

On the other hand:

$b_{k}={\frac {A^{k}b_{0}}{\|A^{k}b_{0}\|}}.$

Therefore, $b_{k}$ converges to (a multiple of) the eigenvector $v_{1}$. The convergence is [geometric](https://en.wikipedia.org/wiki/Geometric_sequence), with ratio

$\left|{\frac {\lambda _{2}}{\lambda _{1}}}\right|.$

Thus, the method converges slowly if there is an eigenvalue close in magnitude to the dominant eigenvalue.

## Applications

Although the power iteration method approximates only one eigenvalue of a matrix, it remains useful for certain [computational problems](https://en.wikipedia.org/wiki/Computational_problem). For instance, [Google](https://en.wikipedia.org/wiki/Google) uses it to calculate the [PageRank](https://en.wikipedia.org/wiki/PageRank) of documents in their search engine, and [Twitter](https://en.wikipedia.org/wiki/Twitter) uses it to show users recommendations of whom to follow. The power iteration method is especially suitable for [sparse matrices](https://en.wikipedia.org/wiki/Sparse_matrix), such as the web matrix, or as the [matrix-free method](https://en.wikipedia.org/wiki/Matrix-free_methods) that does not require storing the coefficient matrix $A$ explicitly, but can instead access a function evaluating matrix-vector products $Ax$. For non-symmetric matrices that are [[Condition Number|well-conditioned]] the power iteration method can outperform more complex [Arnoldi iteration](https://en.wikipedia.org/wiki/Arnoldi_iteration). For symmetric matrices, the power iteration method is rarely used, since its convergence speed can be easily increased without sacrificing the small cost per iteration; see, e.g., [Lanczos iteration](https://en.wikipedia.org/wiki/Lanczos_iteration) and [LOBPCG](https://en.wikipedia.org/wiki/LOBPCG).

## See also

- [Rayleigh quotient iteration](https://en.wikipedia.org/wiki/Rayleigh_quotient_iteration)
- [Inverse iteration](https://en.wikipedia.org/wiki/Inverse_iteration)

## References

1.  [Richard von Mises](https://en.wikipedia.org/wiki/Richard_von_Mises) and H. Pollaczek-Geiringer, *Praktische Verfahren der Gleichungsauflösung*, ZAMM - Zeitschrift für Angewandte Mathematik und Mechanik 9, 152-164 (1929).
2.  [Ipsen, Ilse](https://en.wikipedia.org/wiki/Ilse_Ipsen), and Rebecca M. Wills (5–8 May 2005). ["7th IMACS International Symposium on Iterative Methods in Scientific Computing"](https://ipsen.math.ncsu.edu/ps/slides_imacs.pdf) (PDF). Fields Institute, Toronto, Canada.`{{`[`cite news`](https://en.wikipedia.org/wiki/Template:Cite_news)`}}`: CS1 maint: multiple names: authors list ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_multiple_names:_authors_list))
3.  Pankaj Gupta, Ashish Goel, Jimmy Lin, Aneesh Sharma, Dong Wang, and Reza Bosagh Zadeh [WTF: The who-to-follow system at Twitter](http://dl.acm.org/citation.cfm?id=2488433), Proceedings of the 22nd international conference on World Wide Web
4.  Delattre, B.; Barthélemy, Q.; Araujo, A.; Allauzen, A. (2023), ["Efficient Bound of Lipschitz Constant for Convolutional Layers by Gram Iteration"](https://proceedings.mlr.press/v202/delattre23a.html), *Proceedings of the 40th International Conference on Machine Learning*: 7513–7532
