[[stochastic-processes.base]]

> Source: [[Brownian Motion]]
> License: Wikipedia content is available under CC BY-SA 4.0.

![[media/4caaa76314b0240a551273ea14897172b2a31d9e.gif]]
2-dimensional random walk of a silver [adatom](https://en.wikipedia.org/wiki/Adatom) on an Ag(111) surface

![[media/2d4f4f526a47157d48439dffd3096b0a34836a8c.gif]]
[Simulation](https://en.wikipedia.org/wiki/Brownian_dynamics) of the Brownian motion of a large particle, analogous to a dust particle, that collides with a large set of smaller particles, analogous to molecules of a gas, which move with different velocities in different random directions

**Brownian motion** is the random motion of [particles](https://en.wikipedia.org/wiki/Particle) suspended in a medium (a [liquid](https://en.wikipedia.org/wiki/Liquid) or a [gas](https://en.wikipedia.org/wiki/Gas)). The traditional mathematical formulation of Brownian motion is that of the [Wiener process](https://en.wikipedia.org/wiki/Wiener_process), which is often called Brownian motion, even in mathematical sources.

This motion pattern typically consists of [random](https://en.wikipedia.org/wiki/Randomness) fluctuations in a particle's position inside a fluid sub-domain, followed by a relocation to another sub-domain. Each relocation is followed by more fluctuations within the new closed volume. This pattern describes a fluid at [thermal equilibrium](https://en.wikipedia.org/wiki/Thermal_equilibrium), defined by a given [temperature](https://en.wikipedia.org/wiki/Temperature). Within such a fluid, there exists no preferential direction of flow (as in [transport phenomena](https://en.wikipedia.org/wiki/Transport_phenomena)). More specifically, the fluid's overall [linear](https://en.wikipedia.org/wiki/Linear_momentum) and [angular](https://en.wikipedia.org/wiki/Angular_momentum) momenta remain null over time. The [kinetic energies](https://en.wikipedia.org/wiki/Kinetic_energy) of the molecular Brownian motions, together with those of molecular rotations and vibrations, sum up to the caloric component of a fluid's [internal energy](https://en.wikipedia.org/wiki/Internal_energy) (the [equipartition theorem](https://en.wikipedia.org/wiki/Equipartition_theorem)).

This motion is named after the Scottish botanist [Robert Brown](https://en.wikipedia.org/wiki/Robert_Brown_(botanist,_born_1773) "Robert Brown (botanist, born 1773)"), who first described the phenomenon in 1827, while looking through a microscope at [pollen](https://en.wikipedia.org/wiki/Pollen) of the plant *[Clarkia pulchella](https://en.wikipedia.org/wiki/Clarkia_pulchella)* immersed in water. In 1900, the French mathematician [Louis Bachelier](https://en.wikipedia.org/wiki/Louis_Bachelier) modeled the stochastic process now called Brownian motion in his doctoral thesis, The Theory of Speculation (Théorie de la spéculation), prepared under the supervision of [Henri Poincaré](https://en.wikipedia.org/wiki/Henri_Poincar%C3%A9). Then, in 1905, theoretical physicist [Albert Einstein](https://en.wikipedia.org/wiki/Albert_Einstein) published [a paper](https://en.wikipedia.org/wiki/%C3%9Cber_die_von_der_molekularkinetischen_Theorie_der_W%C3%A4rme_geforderte_Bewegung_von_in_ruhenden_Fl%C3%BCssigkeiten_suspendierten_Teilchen) in which he modelled the motion of the pollen particles as being moved by individual water [molecules](https://en.wikipedia.org/wiki/Molecule), making one of his first major scientific contributions.

The direction of the force of atomic bombardment is constantly changing, and at different times the particle is hit more on one side than another, leading to the seemingly random nature of the motion. This explanation of Brownian motion served as convincing evidence that [atoms](https://en.wikipedia.org/wiki/Atom) and molecules exist and was further verified experimentally by [Jean Perrin](https://en.wikipedia.org/wiki/Jean_Baptiste_Perrin) in 1908. Perrin was awarded the [Nobel Prize in Physics](https://en.wikipedia.org/wiki/Nobel_Prize_in_Physics) in 1926 "for his work on the discontinuous structure of matter".

The [many-body interactions](https://en.wikipedia.org/wiki/Many-body_problem) that yield the Brownian pattern cannot be solved by a model accounting for every involved molecule. Consequently, only probabilistic models applied to [molecular populations](https://en.wikipedia.org/wiki/Statistical_ensemble) can be employed to describe it. Two such models of the [statistical mechanics](https://en.wikipedia.org/wiki/Statistical_mechanics), due to Einstein and Smoluchowski, are presented below. Another, pure probabilistic class of models is the class of the [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) models. There exist sequences of both simpler and more complicated stochastic processes which converge (in the [limit](https://en.wikipedia.org/wiki/Limit_of_a_function)) to Brownian motion (see [random walk](https://en.wikipedia.org/wiki/Random_walk) and [Donsker's theorem](https://en.wikipedia.org/wiki/Donsker%27s_theorem)).

## History

![[media/8979c7c52bcb659fb7b57e97f3a75855544af993.png]]
Reproduced from the [Jean Baptiste Perrin](https://en.wikipedia.org/wiki/Jean_Baptiste_Perrin) book <em>Les Atomes</em>: tracings of the motions of three colloidal particles of radius 0.53 μm, as seen under the microscope, with each point representing that particle's successive position every 30 seconds; the points are then joined by straight line segments (mesh size = 3.2 μm)

The Roman philosopher-poet [Lucretius](https://en.wikipedia.org/wiki/Lucretius)' scientific poem *[On the Nature of Things](https://en.wikipedia.org/wiki/On_the_Nature_of_Things)* (c. 60 BC) has a remarkable description of the motion of [dust](https://en.wikipedia.org/wiki/Dust) particles in verses 113–140 from Book II. He uses this as a proof of the existence of atoms:

> Observe what happens when sunbeams are admitted into a building and shed light on its shadowy places. You will see a multitude of tiny particles mingling in a multitude of ways... their dancing is an actual indication of underlying movements of matter that are hidden from our sight... It originates with the atoms which move of themselves \[i.e., spontaneously\]. Then those small compound bodies that are least removed from the impetus of the atoms are set in motion by the impact of their invisible blows and in turn cannon against slightly larger bodies. So the movement mounts up from the atoms and gradually emerges to the level of our senses so that those bodies are in motion that we see in sunbeams, moved by blows that remain invisible.<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup>

Although the mingling, tumbling motion of dust particles is caused largely by air currents, the glittering, jiggling motion of small dust particles is caused chiefly by true [Brownian dynamics](https://en.wikipedia.org/wiki/Brownian_dynamics); Lucretius "perfectly describes and explains the Brownian movement by a wrong example".

The discovery of this phenomenon is credited to the botanist [Robert Brown](https://en.wikipedia.org/wiki/Robert_Brown_(botanist,_born_1773) "Robert Brown (botanist, born 1773)") in 1827. Brown was studying plant reproduction when he observed [pollen](https://en.wikipedia.org/wiki/Pollen) grains of the plant *[Clarkia pulchella](https://en.wikipedia.org/wiki/Clarkia_pulchella)* in water under a microscope. These grains contain minute particles on the order of 1/4,000<sup>th</sup> of an inch (6.4 microns) in size. He observed these particles executing a jittery motion. By repeating the experiment with particles of inorganic matter he was able to rule out that the motion was life-related, although its origin was yet to be explained.

The mathematics of much of stochastic analysis including the mathematics of Brownian motion was introduced by [Louis Bachelier](https://en.wikipedia.org/wiki/Louis_Bachelier) in 1900 in his PhD thesis "The theory of speculation", in which he presented an analysis of the stock and option markets. However this work was largely unknown until the 1950s.

[Albert Einstein](https://en.wikipedia.org/wiki/Albert_Einstein) (in one of his [1905 papers](https://en.wikipedia.org/wiki/%C3%9Cber_die_von_der_molekularkinetischen_Theorie_der_W%C3%A4rme_geforderte_Bewegung_von_in_ruhenden_Fl%C3%BCssigkeiten_suspendierten_Teilchen)) provided an explanation of Brownian motion in terms of atoms and molecules at a time when their existence was still debated. Einstein proved the relation between the probability distribution of a Brownian particle and the [diffusion equation](https://en.wikipedia.org/wiki/Diffusion_equation). These equations describing Brownian motion were subsequently verified by the experimental work of [Jean Baptiste Perrin](https://en.wikipedia.org/wiki/Jean_Baptiste_Perrin) in 1908, leading to his Nobel prize. [Norbert Wiener](https://en.wikipedia.org/wiki/Norbert_Wiener) gave the first complete and rigorous mathematical analysis in 1923, leading to the underlying mathematical concept being called a [Wiener process](https://en.wikipedia.org/wiki/Wiener_process).

The instantaneous velocity of the Brownian motion can be defined as *v* = Δ*x*/Δ*t*, when Δ*t* \<\< *τ*, where τ is the momentum relaxation time. In 2010, the instantaneous velocity of a Brownian particle (a glass microsphere trapped in air with [optical tweezers](https://en.wikipedia.org/wiki/Optical_tweezers)) was measured successfully. The velocity data verified the [Maxwell–Boltzmann velocity distribution](https://en.wikipedia.org/wiki/Maxwell%E2%80%93Boltzmann_distribution), and the equipartition theorem for a Brownian particle.

## Statistical mechanics theories

### Einstein's theory

There are two parts to Einstein's theory: the first part consists in the formulation of a diffusion equation for Brownian particles, in which the diffusion coefficient is related to the [mean squared displacement](https://en.wikipedia.org/wiki/Mean_squared_displacement) of a Brownian particle, while the second part consists in relating the diffusion coefficient to measurable physical quantities. In this way Einstein was able to determine the size of atoms, and how many atoms there are in a mole, or the [molecular weight](https://en.wikipedia.org/wiki/Molecular_weight) in grams, of a gas. In accordance to [Avogadro's law](https://en.wikipedia.org/wiki/Avogadro%27s_law), this volume is the same for all ideal gases, namely 22.414 liters at standard temperature and pressure. The number of atoms contained in this volume is referred to as the [Avogadro constant](https://en.wikipedia.org/wiki/Avogadro_constant) or as [Avogadro's number](https://en.wikipedia.org/wiki/Avogadro%27s_number) (approximately 6.02×10<sup>23</sup> mol<sup>−1</sup>), and the determination of this number is tantamount to the knowledge of the mass of an atom, since the latter is obtained by dividing the [molar mass](https://en.wikipedia.org/wiki/Molar_mass) of the gas by the [Avogadro constant](https://en.wikipedia.org/wiki/Avogadro_constant).

![[media/40d1d17e17a6d3856d8ae0e47d8216286c4f80bb.png]]
The characteristic bell-shaped curves of the diffusion of Brownian particles. The distribution begins as a [Dirac delta function](https://en.wikipedia.org/wiki/Dirac_delta_function), indicating that all the particles are located at the origin at time <em>t</em> = 0. As <em>t</em> increases, the distribution flattens (though remains bell-shaped), and ultimately becomes uniform in the limit that time goes to infinity.

The first part of Einstein's argument was to determine how far a Brownian particle travels in a given time interval. Classical mechanics is unable to determine this distance because of the enormous number of bombardments a Brownian particle will undergo, roughly of the order of 10<sup>14</sup> collisions per second.

He regarded the increment of particle positions in time $\tau$ in a one-dimensional (*x*) space (with the coordinates chosen so that the origin lies at the initial position of the particle) as a [random variable](https://en.wikipedia.org/wiki/Random_variable) ($q$) with some [[Probability Density Function]] $\varphi (q)$ (i.e., $\varphi (q)$ is the probability density for a jump of magnitude $q$, i.e., the probability density of the particle incrementing its position from $x$ to $x+q$ in the time interval $\tau$). Further, assuming conservation of particle number, he expanded the [number density](https://en.wikipedia.org/wiki/Number_density) $\rho (x,t+\tau )$ (number of particles per unit volume around $x$) at time $t+\tau$ in a [[Taylor Series]], 

$$
{\begin{aligned}\rho (x,t+\tau )={}&\rho (x,t)+\tau {\frac {\partial \rho (x,t)}{\partial t}}+\cdots \\[2ex]={}&\int _{-\infty }^{\infty }\rho (x-q,t)\,\varphi (q)\,dq=\mathbb {E} _{q}{\left[\rho (x-q,t)\right]}\\[1ex]={}&\rho (x,t)\,\int _{-\infty }^{\infty }\varphi (q)\,dq-{\frac {\partial \rho }{\partial x}}\,\int _{-\infty }^{\infty }q\,\varphi (q)\,dq+{\frac {\partial ^{2}\rho }{\partial x^{2}}}\,\int _{-\infty }^{\infty }{\frac {q^{2}}{2}}\varphi (q)\,dq+\cdots \\[1ex]={}&\rho (x,t)\cdot 1-0+{\cfrac {\partial ^{2}\rho }{\partial x^{2}}}\,\int _{-\infty }^{\infty }{\frac {q^{2}}{2}}\varphi (q)\,dq+\cdots \end{aligned}}
$$

 where the second equality is by definition of $\varphi$. The [integral](https://en.wikipedia.org/wiki/Integral) in the first term is equal to one by the definition of probability, and the second and other even terms (i.e. first and other odd [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)")) vanish because of space symmetry. What is left gives rise to the following relation: 

$$
{\frac {\partial \rho }{\partial t}}={\frac {\partial ^{2}\rho }{\partial x^{2}}}\cdot \int _{-\infty }^{\infty }{\frac {q^{2}}{2\tau }}\varphi (q)\,dq+{\text{higher-order even moments.}}
$$

 Where the coefficient after the [Laplacian](https://en.wikipedia.org/wiki/Laplacian), the second moment of probability of displacement $q$, is interpreted as [mass diffusivity](https://en.wikipedia.org/wiki/Mass_diffusivity) *D*: 

$$
D=\int _{-\infty }^{\infty }{\frac {q^{2}}{2\tau }}\varphi (q)\,dq.
$$

 Then the density of Brownian particles ρ at point x at time t satisfies the [diffusion equation](https://en.wikipedia.org/wiki/Diffusion_equation): 

$$
{\frac {\partial \rho }{\partial t}}=D\cdot {\frac {\partial ^{2}\rho }{\partial x^{2}}},
$$

Assuming that *N* particles start from the origin at the initial time *t* = 0, the diffusion equation has the solution: 

$$
\rho (x,t)={\frac {N}{\sqrt {4\pi Dt}}}\exp {\left(-{\frac {x^{2}}{4Dt}}\right)}.
$$

 This expression (which is a [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) with the mean $\mu =0$ and variance $\sigma ^{2}=2Dt$ usually called Brownian motion $B_{t}$) allowed Einstein to calculate the [moments](https://en.wikipedia.org/wiki/Moment_(mathematics) "Moment (mathematics)") directly. The first moment is seen to vanish, meaning that the Brownian particle is equally likely to move to the left as it is to move to the right. The second moment is, however, non-vanishing, being given by 

$$
\mathbb {E} {\left[x^{2}\right]}=2Dt.
$$

 This equation expresses the mean squared displacement in terms of the time elapsed and the diffusivity. From this expression Einstein argued that the displacement of a Brownian particle is not proportional to the elapsed time, but rather to its square root. His argument is based on a conceptual switch from the "ensemble" of Brownian particles to the "single" Brownian particle: we can speak of the relative number of particles at a single instant just as well as of the time it takes a Brownian particle to reach a given point.

The second part of Einstein's theory relates the diffusion constant to physically measurable quantities, such as the mean squared displacement of a particle in a given time interval. This result enables the experimental determination of the Avogadro number and therefore the size of molecules. Einstein analyzed a dynamic equilibrium being established between opposing forces. The beauty of his argument is that the final result does not depend upon which forces are involved in setting up the dynamic equilibrium.

In his original treatment, Einstein considered an [osmotic pressure](https://en.wikipedia.org/wiki/Osmotic_pressure) experiment, but the same conclusion can be reached in other ways.

Consider, for instance, particles suspended in a viscous fluid in a gravitational field. Gravity tends to make the particles settle, whereas diffusion acts to homogenize them, driving them into regions of smaller concentration. Under the action of gravity, a particle acquires a downward speed of *v* = *μmg*, where m is the mass of the particle, g is the acceleration due to gravity, and μ is the particle's [mobility](https://en.wikipedia.org/wiki/Einstein_relation_(kinetic_theory) "Einstein relation (kinetic theory)") in the fluid. [George Stokes](https://en.wikipedia.org/wiki/Sir_George_Stokes,_1st_Baronet) had shown that the mobility for a spherical particle with radius r is $\mu ={\tfrac {1}{6\pi \eta r}}$, where η is the [dynamic viscosity](https://en.wikipedia.org/wiki/Dynamic_viscosity) of the fluid. In a state of dynamic equilibrium, and under the hypothesis of isothermal fluid, the particles are distributed according to the [barometric distribution](https://en.wikipedia.org/wiki/Barometric_formula) 

$$
\rho =\rho _{o}\,\exp \left({-{\frac {mgh}{k_{\text{B}}T}}}\right),
$$

 where *ρ* − *ρ*<sub>o</sub> is the difference in density of particles separated by a height difference, of $h=z-z_{o}$, *k*<sub>B</sub> is the [Boltzmann constant](https://en.wikipedia.org/wiki/Boltzmann_constant) (the ratio of the [universal gas constant](https://en.wikipedia.org/wiki/Universal_gas_constant), *R*, to the [Avogadro constant](https://en.wikipedia.org/wiki/Avogadro_constant), *N*<sub>A</sub>), and *T* is the [absolute temperature](https://en.wikipedia.org/wiki/Thermodynamic_temperature).

![[media/5e559afcfb2b1d57ce17d8cea35f0885f235da71.jpg]]
[Perrin](https://en.wikipedia.org/wiki/Jean_Baptiste_Perrin) examined the equilibrium ([barometric distribution](https://en.wikipedia.org/wiki/Barometric_formula)) of granules (0.6 [microns](https://en.wikipedia.org/wiki/Micron)) of [gamboge](https://en.wikipedia.org/wiki/Gamboge), a viscous substance, under the microscope. The granules move against gravity to regions of lower concentration. The relative change in density observed in 10 microns of suspension is equivalent to that occurring in 6 km of air.

[Dynamic equilibrium](https://en.wikipedia.org/wiki/Dynamic_equilibrium) is established because the more that particles are pulled down by [gravity](https://en.wikipedia.org/wiki/Gravity), the greater the tendency for the particles to migrate to regions of lower concentration. The flux is given by [Fick's law](https://en.wikipedia.org/wiki/Fick%27s_laws_of_diffusion), 

$$
J=-D{\frac {d\rho }{dh}},
$$

 where *J* = *ρv*. Introducing the formula for ρ, we find that 

$$
v={\frac {Dmg}{k_{\text{B}}T}}.
$$

In a state of dynamical equilibrium, this speed must also be equal to *v* = *μmg*. Both expressions for v are proportional to *mg*, reflecting that the derivation is independent of the type of forces considered. Similarly, one can derive an equivalent formula for identical [charged particles](https://en.wikipedia.org/wiki/Charged_particle) of charge q in a uniform [electric field](https://en.wikipedia.org/wiki/Electric_field) of magnitude E, where *mg* is replaced with the [electrostatic force](https://en.wikipedia.org/wiki/Electrostatic_force) *qE*. Equating these two expressions yields the [Einstein relation](https://en.wikipedia.org/wiki/Einstein_relation_(kinetic_theory) "Einstein relation (kinetic theory)") for the diffusivity, independent of *mg* or *qE* or other such forces: 

$$
{\frac {\mathbb {E} {\left[x^{2}\right]}}{2t}}=D=\mu k_{\text{B}}T={\frac {\mu RT}{N_{\text{A}}}}={\frac {RT}{6\pi \eta rN_{\text{A}}}}.
$$

 Here the first equality follows from the first part of Einstein's theory, the third equality follows from the definition of the [Boltzmann constant](https://en.wikipedia.org/wiki/Boltzmann_constant) as *k*<sub>B</sub> = *R* / *N*<sub>A</sub>, and the fourth equality follows from Stokes's formula for the mobility. By measuring the mean squared displacement over a time interval along with the universal gas constant *R*, the temperature T, the viscosity η, and the particle radius r, the Avogadro constant *N*<sub>A</sub> can be determined.

The type of dynamical equilibrium proposed by Einstein was not new. It had been pointed out previously by [J. J. Thomson](https://en.wikipedia.org/wiki/J._J._Thomson) in his series of lectures at Yale University in May 1903 that the dynamic equilibrium between the velocity generated by a [concentration gradient](https://en.wikipedia.org/wiki/Concentration_gradient) given by Fick's law and the velocity due to the variation of the partial pressure caused when ions are set in motion "gives us a method of determining Avogadro's constant which is independent of any hypothesis as to the shape or size of molecules, or of the way in which they act upon each other".

An identical expression to Einstein's formula for the diffusion coefficient was also found by [Walther Nernst](https://en.wikipedia.org/wiki/Walther_Nernst) in 1888 in which he expressed the diffusion coefficient as the ratio of the [osmotic pressure](https://en.wikipedia.org/wiki/Osmotic_pressure) to the ratio of the [frictional](https://en.wikipedia.org/wiki/Friction) force and the velocity to which it gives rise. The former was equated to the law of van 't Hoff while the latter was given by [Stokes's law](https://en.wikipedia.org/wiki/Stokes%27s_law). He writes $k'=p_{o}/k$ for the diffusion coefficient k′, where $p_{o}$ is the osmotic pressure and k is the ratio of the frictional force to the molecular viscosity which he assumes is given by Stokes's formula for the viscosity. Introducing the [ideal gas law](https://en.wikipedia.org/wiki/Ideal_gas_law) per unit volume for the osmotic pressure, the formula becomes identical to that of Einstein's. The use of Stokes's law in Nernst's case, as well as in Einstein and Smoluchowski, is not strictly applicable since it does not apply to the case where the radius of the sphere is small in comparison with the [mean free path](https://en.wikipedia.org/wiki/Mean_free_path).

Confirming Einstein's formula experimentally proved difficult. Initial attempts by [Theodor Svedberg](https://en.wikipedia.org/wiki/Theodor_Svedberg) in 1906 and 1907 were critiqued by Einstein and by Perrin as not measuring a quantity directly comparable to the formula. [Victor Henri](https://en.wikipedia.org/wiki/Victor_Henri) in 1908 took cinematographic shots through a microscope and found quantitative disagreement with the formula but again the analysis was uncertain. Einstein's predictions were finally confirmed in a series of experiments carried out by Chaudesaigues in 1908 and Perrin in 1909. The confirmation of Einstein's theory constituted empirical progress for the [kinetic theory of heat](https://en.wikipedia.org/wiki/Kinetic_theory_of_gases). In essence, Einstein showed that the motion can be predicted directly from the kinetic model of [thermal equilibrium](https://en.wikipedia.org/wiki/Thermal_equilibrium). The importance of the theory lay in the fact that it confirmed the kinetic theory's account of the [second law of thermodynamics](https://en.wikipedia.org/wiki/Second_law_of_thermodynamics) as being an essentially statistical law.

Brownian motion model of the trajectory of a particle of dye in water

### Smoluchowski model

[Smoluchowski](https://en.wikipedia.org/wiki/Marian_Smoluchowski)'s theory of Brownian motion starts from the same premise as that of Einstein and derives the same probability distribution *ρ*(*x*, *t*) for the displacement of a Brownian particle along the x in time t. He therefore gets the same expression for the mean squared displacement: $\mathbb {E} {\left[(\Delta x)^{2}\right]}$. However, when he relates it to a particle of mass m moving at a velocity u which is the result of a frictional force governed by Stokes's law, he finds 

$$
\mathbb {E} {\left[(\Delta x)^{2}\right]}=2Dt=t{\frac {32}{81}}{\frac {mu^{2}}{\pi \mu a}}=t{\frac {64}{27}}{\frac {{\frac {1}{2}}mu^{2}}{3\pi \mu a}},
$$

 where μ is the viscosity coefficient, and a is the radius of the particle. Associating the kinetic energy $mu^{2}/2$ with the thermal energy *RT*/*N*, the expression for the mean squared displacement is 64/27 times that found by Einstein. The fraction 27/64 was commented on by [Arnold Sommerfeld](https://en.wikipedia.org/wiki/Arnold_Sommerfeld) in his necrology on Smoluchowski: "The numerical coefficient of Einstein, which differs from Smoluchowski by 27/64 can only be put in doubt."

Smoluchowski attempts to answer the question of why a Brownian particle should be displaced by bombardments of smaller particles when the probabilities for striking it in the forward and rear directions are equal. If the probability of m gains and *n* − *m* losses follows a [binomial distribution](https://en.wikipedia.org/wiki/Binomial_distribution), 

$$
P_{m,n}={\binom {n}{m}}2^{-n},
$$

 with equal *a priori* probabilities of 1/2, the mean total gain is 

$$
\mathbb {E} {\left[2m-n\right]}=\sum _{m={\frac {n}{2}}}^{n}(2m-n)P_{m,n}={\frac {nn!}{2^{n+1}\left[\left({\frac {n}{2}}\right)!\right]^{2}}}.
$$

If n is large enough so that Stirling's approximation can be used in the form 

$$
n!\approx \left({\frac {n}{e}}\right)^{n}{\sqrt {2\pi n}},
$$

 then the expected total gain will be<sup>\[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*\]</sup> 

$$
\mathbb {E} {\left[2m-n\right]}\approx {\sqrt {\frac {n}{2\pi }}},
$$

 showing that it increases as the square root of the total population.

Suppose that a Brownian particle of mass M is surrounded by lighter particles of mass m which are traveling at a speed u. Then, reasons Smoluchowski, in any collision between a surrounding and Brownian particles, the velocity transmitted to the latter will be *mu*/*M*. This ratio is of the order of 10<sup>−7</sup> cm/s. But we also have to take into consideration that in a gas there will be more than 10<sup>16</sup> collisions in a second, and even greater in a liquid where we expect that there will be 10<sup>20</sup> collision in one second. Some of these collisions will tend to accelerate the Brownian particle; others will tend to decelerate it. If there is a mean excess of one kind of collision or the other to be of the order of 10<sup>8</sup> to 10<sup>10</sup> collisions in one second, then velocity of the Brownian particle may be anywhere between 10–1000 cm/s. Thus, even though there are equal probabilities for forward and backward collisions there will be a net tendency to keep the Brownian particle in motion, just as the ballot theorem predicts.

These orders of magnitude are not exact because they do not take into consideration the velocity of the Brownian particle, U, which depends on the collisions that tend to accelerate and decelerate it. The larger U is, the greater will be the collisions that will retard it so that the velocity of a Brownian particle can never increase without limit. Could such a process occur, it would be tantamount to a perpetual motion of the second type. And since equipartition of energy applies, the kinetic energy of the Brownian particle, $MU^{2}/2$, will be equal, on the average, to the kinetic energy of the surrounding fluid particle, $mu^{2}/2$.

In 1906, Smoluchowski published a one-dimensional model to describe a particle undergoing Brownian motion. The model assumes collisions with *M* ≫ *m* where M is the test particle's mass and m the mass of one of the individual particles composing the fluid. It is assumed that the particle collisions are confined to one dimension and that it is equally probable for the test particle to be hit from the left as from the right. It is also assumed that every collision always imparts the same magnitude of Δ*V*. If *N*<sub>R</sub> is the number of collisions from the right and *N*<sub>L</sub> the number of collisions from the left then after N collisions the particle's velocity will have changed by Δ*V*(2*N*<sub>R</sub> − *N*). The [multiplicity](https://en.wikipedia.org/wiki/Multiplicity_(mathematics) "Multiplicity (mathematics)") is then simply given by: 

$$
{\binom {N}{N_{\text{R}}}}={\frac {N!}{N_{\text{R}}!(N-N_{\text{R}})!}}
$$

 and the total number of possible states is given by 2<sup>*N*</sup>. Therefore, the probability of the particle being hit from the right *N*<sub>R</sub> times is: 

$$
P_{N}(N_{\text{R}})={\frac {N!}{2^{N}N_{\text{R}}!(N-N_{\text{R}})!}}
$$

As a result of its simplicity, Smoluchowski's 1D model can only qualitatively describe Brownian motion. For a realistic particle undergoing Brownian motion in a fluid, many of the assumptions do not apply. For example, the assumption that on average there are an equal number of collisions from the right as from the left falls apart once the particle is in motion. Also, there would be a distribution of different possible Δ*V*s instead of always just one in a realistic situation.

### Langevin equation

The [diffusion equation](https://en.wikipedia.org/wiki/Diffusion_equation) yields an approximation of the time evolution of the [[Probability Density Function]] associated with the position of the particle going under a Brownian movement under the physical definition. The approximation becomes valid on timescales much larger than the timescale of individual atomic collisions, since it does not include a term to describe the acceleration of particles during collision. The time evolution of the position of the Brownian particle over all time scales described using the [Langevin equation](https://en.wikipedia.org/wiki/Langevin_equation), an equation that involves a random force field representing the effect of the [thermal fluctuations](https://en.wikipedia.org/wiki/Thermal_fluctuations) of the solvent on the particle. At longer times scales, where acceleration is negligible, individual particle dynamics can be approximated using [Brownian dynamics](https://en.wikipedia.org/wiki/Brownian_dynamics) in place of [Langevin dynamics](https://en.wikipedia.org/wiki/Langevin_dynamics).

### Astrophysics: star motion within galaxies

In [stellar dynamics](https://en.wikipedia.org/wiki/Stellar_dynamics), a massive body (star, [black hole](https://en.wikipedia.org/wiki/Black_hole), etc.) can experience Brownian motion as it responds to [gravitational](https://en.wikipedia.org/wiki/Gravitational) forces from surrounding stars. The rms velocity V of the massive object, of mass M, is related to the rms velocity $v_{\star }$ of the background stars by 

$$
MV^{2}\approx mv_{\star }^{2}
$$

 where $m\ll M$ is the mass of the background stars. The gravitational force from the massive object causes nearby stars to move faster than they otherwise would, increasing both $v_{\star }$ and V. The Brownian velocity of [Sgr A\*](https://en.wikipedia.org/wiki/Sagittarius_A*), the [supermassive black hole](https://en.wikipedia.org/wiki/Supermassive_black_hole) at the center of the [Milky Way galaxy](https://en.wikipedia.org/wiki/Milky_Way_galaxy), is predicted from this formula to be less than 1 km s<sup>−1</sup>.

## Mathematics

An animated example of a Brownian motion-like [random walk](https://en.wikipedia.org/wiki/Random_walk) on a 2D surface with periodic boundary conditions. In the [scaling limit](https://en.wikipedia.org/wiki/Scaling_limit), random walk approaches the Wiener process according to [Donsker's theorem](https://en.wikipedia.org/wiki/Donsker%27s_theorem).

In [mathematics](https://en.wikipedia.org/wiki/Mathematics), Brownian motion is described by the **Wiener process**, a continuous-time [stochastic process](https://en.wikipedia.org/wiki/Stochastic_process) named in honor of [Norbert Wiener](https://en.wikipedia.org/wiki/Norbert_Wiener). It is one of the best known [Lévy processes](https://en.wikipedia.org/wiki/L%C3%A9vy_process) ([càdlàg](https://en.wikipedia.org/wiki/C%C3%A0dl%C3%A0g) stochastic processes with [stationary](https://en.wikipedia.org/wiki/Stationary_increments) [independent increments](https://en.wikipedia.org/wiki/Independent_increments)) and occurs frequently in pure and applied mathematics, [economics](https://en.wikipedia.org/wiki/Economy) and [physics](https://en.wikipedia.org/wiki/Physics).

![[media/3e38313e75c797e82ec8d253fb2be2aed738976d.png]]
A single realisation of three-dimensional Brownian motion for times 0 ≤ <em>t</em> ≤ 2

The Wiener process *W<sub>t</sub>* is characterized by four facts:

1.  *W*<sub>0</sub> = 0
2.  *W<sub>t</sub>* is [almost surely](https://en.wikipedia.org/wiki/Almost_surely) continuous
3.  *W<sub>t</sub>* has independent increments
4.  $W_{t}-W_{s}\sim {\mathcal {N}}(0,t-s)$ (for $0\leq s\leq t$).

${\mathcal {N}}(\mu ,\sigma ^{2})$ denotes the [normal distribution](https://en.wikipedia.org/wiki/Normal_distribution) with [expected value](https://en.wikipedia.org/wiki/Expected_value) μ and [variance](https://en.wikipedia.org/wiki/Variance) *σ*<sup>2</sup>. The condition that it has independent increments means that if $0\leq s_{1}<t_{1}\leq s_{2}<t_{2}$ then $W_{t_{1}}-W_{s_{1}}$ and $W_{t_{2}}-W_{s_{2}}$ are independent random variables. In addition, for some [filtration](https://en.wikipedia.org/wiki/Filtration_(probability_theory) "Filtration (probability theory)") ${\mathcal {F}}_{t}$, $W_{t}$ is ${\mathcal {F}}_{t}$ [measurable](https://en.wikipedia.org/wiki/Measurable) for all $t\geq 0$.

An alternative characterisation of the Wiener process is the so-called *Lévy characterisation* that says that the Wiener process is an almost surely continuous [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) "Martingale (probability theory)") with *W*<sub>0</sub> = 0 and [quadratic variation](https://en.wikipedia.org/wiki/Quadratic_variation) $[W_{t},W_{t}]=t$.

A third characterisation is that the Wiener process has a spectral representation as a sine series whose coefficients are independent ${\mathcal {N}}(0,1)$ random variables. This representation can be obtained using the [Kosambi–Karhunen–Loève theorem](https://en.wikipedia.org/wiki/Kosambi%E2%80%93Karhunen%E2%80%93Lo%C3%A8ve_theorem).

The Wiener process can be constructed as the [scaling limit](https://en.wikipedia.org/wiki/Scaling_limit) of a [random walk](https://en.wikipedia.org/wiki/Random_walk), or other discrete-time stochastic processes with stationary independent increments. This is known as [Donsker's theorem](https://en.wikipedia.org/wiki/Donsker%27s_theorem). Like the random walk, the Wiener process is recurrent in one or two dimensions (meaning that it returns almost surely to any fixed [neighborhood](https://en.wikipedia.org/wiki/Neighborhood_(mathematics)) of the origin infinitely often) whereas it is not recurrent in dimensions three and higher. Unlike the random walk, it is [scale invariant](https://en.wikipedia.org/wiki/Scale_invariance). A d-dimensional [Gaussian free field](https://en.wikipedia.org/wiki/Gaussian_free_field) has been described as "a d-dimensional-time analog of Brownian motion."

### Statistics

The Brownian motion can be modeled by a [random walk](https://en.wikipedia.org/wiki/Random_walk).

In the general case, Brownian motion is a [Markov process](https://en.wikipedia.org/wiki/Markov_process) and described by [stochastic integral equations](https://en.wikipedia.org/wiki/Stochastic_calculus).

### Lévy characterisation

The French mathematician [Paul Lévy](https://en.wikipedia.org/wiki/Paul_L%C3%A9vy_(mathematician) "Paul Lévy (mathematician)") proved the following theorem, which gives a necessary and sufficient condition for a continuous **R**<sup>*n*</sup>-valued stochastic process *X* to actually be n-dimensional Brownian motion. Hence, Lévy's condition can actually be used as an alternative definition of Brownian motion.

Let *X* = (*X*<sub>1</sub>, ..., *X*<sub>*n*</sub>) be a continuous stochastic process on a [probability space](https://en.wikipedia.org/wiki/Probability_space) (Ω, Σ, **P**) taking values in **R**<sup>*n*</sup>. Then the following are equivalent:

1.  *X* is a Brownian motion with respect to **P**, i.e., the law of *X* with respect to **P** is the same as the law of an n-dimensional Brownian motion, i.e., the [push-forward measure](https://en.wikipedia.org/wiki/Push-forward_measure) *X*<sub>∗</sub>(**P**) is [classical Wiener measure](https://en.wikipedia.org/wiki/Classical_Wiener_measure) on *C*<sub>0</sub>(\[0, ∞); **R**<sup>*n*</sup>).
2.  both
    1.  *X* is a [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) "Martingale (probability theory)") with respect to **P** (and its own [natural filtration](https://en.wikipedia.org/wiki/Natural_filtration)); and
    2.  for all 1 ≤ *i*, *j* ≤ *n*, *X*<sub>*i*</sub>(*t*) *X*<sub>*j*</sub>(*t*) − *δ*<sub>*ij*</sub> *t* is a martingale with respect to **P** (and its own [natural filtration](https://en.wikipedia.org/wiki/Natural_filtration)), where *δ*<sub>*ij*</sub> denotes the [Kronecker delta](https://en.wikipedia.org/wiki/Kronecker_delta).

### Spectral content

The spectral content of a stochastic process $X_{t}$ can be found from the [power spectral density](https://en.wikipedia.org/wiki/Power_spectral_density), formally defined as 

$$
S(\omega )=\lim _{T\to \infty }{\frac {1}{T}}\mathbb {E} \left\{\left|\int _{0}^{T}e^{i\omega t}X_{t}dt\right|^{2}\right\},
$$

 where $\mathbb {E}$ stands for the [expected value](https://en.wikipedia.org/wiki/Expected_value). The power spectral density of Brownian motion is found to be 

$$
S_{BM}(\omega )={\frac {4D}{\omega ^{2}}}.
$$

 where D is the [diffusion coefficient](https://en.wikipedia.org/wiki/Diffusion_coefficient) of *X<sub>t</sub>*. For naturally occurring signals, the spectral content can be found from the power spectral density of a single realization, with finite available time, i.e., 

$$
S^{(1)}(\omega ,T)={\frac {1}{T}}\left|\int _{0}^{T}e^{i\omega t}X_{t}dt\right|^{2},
$$

 which for an individual realization of a Brownian motion trajectory, it is found to have expected value $\mu _{BM}(\omega ,T)$ 

$$
\mu _{\text{BM}}(\omega ,T)={\frac {4D}{\omega ^{2}}}\left[1-{\frac {\sin \left(\omega T\right)}{\omega T}}\right]
$$

 and [variance](https://en.wikipedia.org/wiki/Variance) $\sigma _{\text{BM}}^{2}(\omega ,T)$ 

$$
\sigma _{S}^{2}(f,T)=\mathbb {E} \left\{\left(S_{T}^{(j)}(f)\right)^{2}\right\}-\mu _{S}^{2}(f,T)={\frac {20D^{2}}{f^{4}}}\left[1-{\Big (}6-\cos \left(fT\right){\Big )}{\frac {2\sin \left(fT\right)}{5fT}}+{\frac {{\Big (}17-\cos \left(2fT\right)-16\cos \left(fT\right){\Big )}}{10f^{2}T^{2}}}\right].
$$

For sufficiently long realization times, the expected value of the power spectrum of a single trajectory converges to the formally defined power spectral density $S(\omega )$, but its coefficient of variation $\gamma =\sigma /\mu$ tends to ${\sqrt {5}}/2$. This implies the distribution of $S^{(1)}(\omega ,T)$ is broad even in the infinite time limit.

### Riemannian manifolds

![[media/799ab58dc5b9916958b886746c5d8c84224adeff.jpg]]
Brownian motion on a sphere

Brownian motion is usually considered to take place in [Euclidean space](https://en.wikipedia.org/wiki/Euclidean_space). It is natural to consider how such motion generalizes to more complex shapes, such as [surfaces](https://en.wikipedia.org/wiki/Surface) or higher dimensional [[Manifold|manifolds]]. The formalization requires the space to possess some form of a [derivative](https://en.wikipedia.org/wiki/Derivative), as well as a [metric](https://en.wikipedia.org/wiki/Metric_space), so that a [Laplacian](https://en.wikipedia.org/wiki/Laplacian) can be defined. Both of these are available on [Riemannian manifolds](https://en.wikipedia.org/wiki/Riemannian_manifold).

Riemannian manifolds have the property that [geodesics](https://en.wikipedia.org/wiki/Geodesic) can be described in [polar coordinates](https://en.wikipedia.org/wiki/Polar_coordinates); that is, displacements are always in a radial direction, at some given angle. Uniform random motion is then described by Gaussians along the radial direction, independent of the angle, the same as in Euclidean space.

The [infinitesimal generator](https://en.wikipedia.org/wiki/Infinitesimal_generator_(stochastic_processes) "Infinitesimal generator (stochastic processes)") (and hence [characteristic operator](https://en.wikipedia.org/wiki/Characteristic_operator)) of Brownian motion on Euclidean **R**<sup>*n*</sup> is 1/2Δ, where Δ denotes the [Laplace operator](https://en.wikipedia.org/wiki/Laplace_operator). Brownian motion on an m-dimensional [Riemannian manifold](https://en.wikipedia.org/wiki/Riemannian_manifold) (*M*, *g*) can be defined as diffusion on M with the characteristic operator given by 1/2Δ<sub>LB</sub>, half the [Laplace–Beltrami operator](https://en.wikipedia.org/wiki/Laplace%E2%80%93Beltrami_operator) Δ<sub>LB</sub>.

One of the topics of study is a characterization of the [Poincaré recurrence time](https://en.wikipedia.org/wiki/Poincar%C3%A9_recurrence_theorem) for such systems.

## Narrow escape

The [narrow escape problem](https://en.wikipedia.org/wiki/Narrow_escape_problem) is a ubiquitous problem in biology, biophysics and cellular biology which has the following formulation: a Brownian particle ([ion](https://en.wikipedia.org/wiki/Ion), [molecule](https://en.wikipedia.org/wiki/Molecule), or [protein](https://en.wikipedia.org/wiki/Protein)) is confined to a bounded domain (a compartment or a cell) by a reflecting boundary, except for a small window through which it can escape. The narrow escape problem is that of calculating the mean escape time. This time diverges as the window shrinks, thus rendering the calculation a [singular perturbation](https://en.wikipedia.org/wiki/Singular_perturbation) problem.

## See also

- [Brownian bridge](https://en.wikipedia.org/wiki/Brownian_bridge) – Stochastic process in physics
- [Brownian covariance](https://en.wikipedia.org/wiki/Brownian_covariance) – Statistical measurePages displaying short descriptions of redirect targets
- [Brownian dynamics](https://en.wikipedia.org/wiki/Brownian_dynamics) – Ideal molecular motion where no average acceleration takes place
- [Brownian motor](https://en.wikipedia.org/wiki/Brownian_motor) – Nanoscale machine
- [Brownian noise](https://en.wikipedia.org/wiki/Brownian_noise) – Type of noise produced by Brownian motion
- [Brownian ratchet](https://en.wikipedia.org/wiki/Brownian_ratchet) – Perpetual motion device
- [Brownian surface](https://en.wikipedia.org/wiki/Brownian_surface)
- [Brownian tree](https://en.wikipedia.org/wiki/Brownian_tree) – Concept in probability theory
- [Brownian web](https://en.wikipedia.org/wiki/Brownian_web)
- [Fractional Brownian motion](https://en.wikipedia.org/wiki/Fractional_Brownian_motion) – Probability theory concept
- [Geometric Brownian motion](https://en.wikipedia.org/wiki/Geometric_Brownian_motion) – Continuous stochastic process
- [Itô diffusion](https://en.wikipedia.org/wiki/It%C3%B4_diffusion) – Solution to a specific type of stochastic differential equation
- [Lévy arcsine law](https://en.wikipedia.org/wiki/L%C3%A9vy_arcsine_law) – Collection of results for one-dimensional random walks and Brownian motionPages displaying short descriptions of redirect targets
- [Marangoni effect](https://en.wikipedia.org/wiki/Marangoni_effect) – Physical phenomenon between two fluids
- [Nanoparticle tracking analysis](https://en.wikipedia.org/wiki/Nanoparticle_tracking_analysis)
- [Reflected Brownian motion](https://en.wikipedia.org/wiki/Reflected_Brownian_motion) – Wiener process with reflecting spatial boundaries
- [Rotational Brownian motion](https://en.wikipedia.org/wiki/Rotational_Brownian_motion)
- [Schramm–Loewner evolution](https://en.wikipedia.org/wiki/Schramm%E2%80%93Loewner_evolution) – Concept in probability theory
- [Single particle tracking](https://en.wikipedia.org/wiki/Single_particle_tracking)
- [Single particle trajectories](https://en.wikipedia.org/wiki/Single_particle_trajectories)
- [Surface diffusion](https://en.wikipedia.org/wiki/Surface_diffusion) – Physical Process
- [Tyndall effect](https://en.wikipedia.org/wiki/Tyndall_effect) – Scattering of light by tiny particles in a colloidal suspension

## References

1.  Meyburg, Jan Philipp; Diesing, Detlef (2017). "Teaching the Growth, Ripening, and Agglomeration of Nanostructures in Computer Experiments". *Journal of Chemical Education*. **94** (9): 1225–1231. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2017JChEd..94.1225M](https://ui.adsabs.harvard.edu/abs/2017JChEd..94.1225M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/acs.jchemed.6b01008](https://doi.org/10.1021%2Facs.jchemed.6b01008).
2.  ^   Feynman, Richard (1964). ["The Brownian Movement"](https://feynmanlectures.caltech.edu/I_41.html). *The Feynman Lectures of Physics, Volume I*. p. 41.
3.  Pathria, RK (1972). Statistical Mechanics. Pergamon Press. pp. 43–48, 73–74. ISBN 0-08-016747-0.
4.  ^   Einstein, Albert (1905). ["Über die von der molekularkinetischen Theorie der Wärme geforderte Bewegung von in ruhenden Flüssigkeiten suspendierten Teilchen"](http://www.physik.uni-augsburg.de/annalen/history/einstein-papers/1905_17_549-560.pdf) \[On the Movement of Small Particles Suspended in Stationary Liquids Required by the Molecular-Kinetic Theory of Heat\] (PDF). *Annalen der Physik* (in German). **322** (8): 549–560. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1905AnP...322..549E](https://ui.adsabs.harvard.edu/abs/1905AnP...322..549E). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/andp.19053220806](https://doi.org/10.1002%2Fandp.19053220806). [Archived](https://ghostarchive.org/archive/20221009/http://www.physik.uni-augsburg.de/annalen/history/einstein-papers/1905_17_549-560.pdf) (PDF) from the original on 9 October 2022.
5.  ["The Nobel Prize in Physics 1926"](https://www.nobelprize.org/prizes/physics/1926/perrin/lecture/). *NobelPrize.org*. Retrieved 29 May 2019.
6.  Tsekov, Roumen (1995). "Brownian motion of molecules: the classical theory". *Ann. Univ. Sofia*. **88**: 57. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1005.1490](https://arxiv.org/abs/1005.1490). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1995AUSFC..88...57T](https://ui.adsabs.harvard.edu/abs/1995AUSFC..88...57T). “the behavior of a Brownian particle is quite irregular and can be described only in the frames of a statistical approach.”
7.  Knight, Frank B. (1 February 1962). ["On the random walk and Brownian motion"](https://www.ams.org/jourcgi/jour-getitem?pii=S0002-9947-1962-0139211-2). *Transactions of the American Mathematical Society*. **103** (2): 218–228. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0002-9947-1962-0139211-2](https://doi.org/10.1090%2FS0002-9947-1962-0139211-2). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0002-9947](https://search.worldcat.org/issn/0002-9947).
8.  ["Donsker invariance principle – Encyclopedia of Mathematics"](https://encyclopediaofmath.org/wiki/Donsker_invariance_principle). *encyclopediaofmath.org*. Retrieved 28 June 2020.
9.  Perrin, Jean (1914). [Atoms](https://archive.org/stream/atomsper00perruoft#page/115/mode/1up). London : Constable. p. 115.`{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: CS1 maint: publisher location ([link](https://en.wikipedia.org/wiki/Category:CS1_maint:_publisher_location))
10. Tabor, D. (1991). [Gases, Liquids and Solids: And Other States of Matter](https://books.google.com/books?id=bTrJ15y2IksC&pg=PA120) (3rd ed.). Cambridge: Cambridge University Press. p. 120. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-40667-3](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-40667-3).
11. ^   Brush, Stephen G. (1968). ["A History of Random Processes: I. Brownian Movement from Brown to Perrin"](https://www.jstor.org/stable/41133279). *Archive for History of Exact Sciences*. **5** (1): 1–36. [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0003-9519](https://search.worldcat.org/issn/0003-9519).
12. Brown, Robert; Bennett, John J.; Hardwicke, Robert (1866). [The miscellaneous botanical works of Robert Brown](https://www.biodiversitylibrary.org/page/18531045). Vol. 1. Published for the Ray society by R. Hardwicke. pp. 463–486.
13. Davis, Mark H. A.; Bachelier, Louis; Etheridge, Alison (2011). *Louis Bachelier's Theory of Speculation: The Origins of Modern Finance*. Princeton: Princeton University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4008-2930-9](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4008-2930-9).
14. ^    Mörters, Peter; Peres, Yuval (1 January 2001). [Brownian Motion](https://www.cambridge.org/core/product/identifier/9780511750489/type/book) (1 ed.). Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511750489](https://doi.org/10.1017%2Fcbo9780511750489). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-76018-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-76018-8).
15. ^   Grigor'yan, Alexander (19 February 1999). ["Analytic and geometric background of recurrence and non-explosion of the Brownian motion on Riemannian manifolds"](https://www.ams.org/bull/1999-36-02/S0273-0979-99-00776-4/). *Bulletin of the American Mathematical Society*. **36** (2): 135–249. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1090/S0273-0979-99-00776-4](https://doi.org/10.1090%2FS0273-0979-99-00776-4). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0273-0979](https://search.worldcat.org/issn/0273-0979).
16. ^   Li, Tongcang; Kheifets, Simon; Medellin, David; Raizen, Mark (2010). ["Measurement of the instantaneous velocity of a Brownian particle"](https://wayback.archive-it.org/all/20110331172407/http://chaos.utexas.edu/wp-uploads/2010/06/science.1189403v1.pdf) (PDF). *[Science](https://en.wikipedia.org/wiki/Science_(journal) "Science (journal)")*. **328** (5986): 1673–1675. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2010Sci...328.1673L](https://ui.adsabs.harvard.edu/abs/2010Sci...328.1673L). [CiteSeerX](https://en.wikipedia.org/wiki/CiteSeerX_(identifier)) [10.1.1.167.8245](https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.167.8245). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1126/science.1189403](https://doi.org/10.1126%2Fscience.1189403). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [20488989](https://pubmed.ncbi.nlm.nih.gov/20488989). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [45828908](https://api.semanticscholar.org/CorpusID:45828908). Archived from [the original](http://chaos.utexas.edu/wp-uploads/2010/06/science.1189403v1.pdf) (PDF) on 31 March 2011.
17. ^   Einstein, Albert (1956) \[1926\]. [Investigations on the Theory of the Brownian Movement](http://users.physik.fu-berlin.de/~kleinert/files/eins_brownian.pdf) (PDF). Dover Publications. [Archived](https://ghostarchive.org/archive/20221009/http://users.physik.fu-berlin.de/~kleinert/files/eins_brownian.pdf) (PDF) from the original on 9 October 2022. Retrieved 25 December 2013.
18. Stachel, J., ed. (1989). ["Einstein's Dissertation on the Determination of Molecular Dimensions"](http://www.csun.edu/~dchoudhary/Physics-Year_files/ed_diss.pdf) (PDF). *The Collected Papers of Albert Einstein, Volume 2*. Princeton University Press. [Archived](https://ghostarchive.org/archive/20221009/http://www.csun.edu/~dchoudhary/Physics-Year_files/ed_diss.pdf) (PDF) from the original on 9 October 2022.
19. Kozdron, Michael J. (2008). ["Brownian Motion and the Heat Equation – chpt. 3 Albert Einstein's proof of the existence of Brownian motion"](https://web.archive.org/web/20241126184903/https://uregina.ca/~kozdron/Research/UgradTalks/BM_and_Heat/heat_and_BM.pdf) (PDF). *University of Regina*. Archived from [the original](https://uregina.ca/~kozdron/Research/UgradTalks/BM_and_Heat/heat_and_BM.pdf) (PDF) on 26 November 2024. Retrieved 3 November 2025.
20. Lavenda, Bernard H. (1985). [Nonequilibrium Statistical Thermodynamics](https://archive.org/details/nonequilibriumst00lave). John Wiley & Sons. p. [20](https://archive.org/details/nonequilibriumst00lave/page/n29). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-471-90670-4](https://en.wikipedia.org/wiki/Special:BookSources/978-0-471-90670-4).
21. ^   Thomson, J. J. (1904). [Electricity and Matter](https://archive.org/details/electricitymatte00thomuoft). Yale University Press. pp. [80](https://archive.org/details/electricitymatte00thomuoft/page/80)–83.
22. Nernst, Walther (1888). "Zur Kinetik der in Lösung befindlichen Körper". *[Zeitschrift für Physikalische Chemie](https://en.wikipedia.org/wiki/Zeitschrift_f%C3%BCr_Physikalische_Chemie)* (in German). **9**: 613–637.
23. Leveugle, J. (2004). *La Relativité, Poincaré et Einstein, Planck, Hilbert*. Harmattan. p. 181.
24. Townsend, J.E.S. (1915). [Electricity in Gases](https://archive.org/details/electricityinga00towngoog). Clarendon Press. p. [254](https://archive.org/details/electricityinga00towngoog/page/n282).
25. Maiocchi, Roberto (September 1990). ["The case of Brownian motion"](https://www.cambridge.org/core/journals/british-journal-for-the-history-of-science/article/abs/case-of-brownian-motion/7E6FCB8188956D072CC83581B5645099). *The British Journal for the History of Science*. **23** (3): 257–283. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/S0007087400043983](https://doi.org/10.1017%2FS0007087400043983). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1474-001X](https://search.worldcat.org/issn/1474-001X).
26. Haw, M D (26 August 2002). ["Colloidal suspensions, Brownian motion, molecular reality: a short history"](https://iopscience.iop.org/article/10.1088/0953-8984/14/33/315). *Journal of Physics: Condensed Matter*. **14** (33): 7769–7779. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/0953-8984/14/33/315](https://doi.org/10.1088%2F0953-8984%2F14%2F33%2F315).
27. See P. Clark 1976, p. 97
29. See p. 535 in Sommerfeld, A. (1917). "Zum Andenken an Marian von Smoluchowski" \[In Memory of Marian von Smoluchowski\]. *[Physikalische Zeitschrift](https://en.wikipedia.org/wiki/Physikalische_Zeitschrift)* (in German). **18** (22): 533–539.
31. von Smoluchowski, M. (1906). ["Zur kinetischen Theorie der Brownschen Molekularbewegung und der Suspensionen"](https://zenodo.org/record/1424073). *[Annalen der Physik](https://en.wikipedia.org/wiki/Annalen_der_Physik)* (in German). **326** (14): 756–780. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1906AnP...326..756V](https://ui.adsabs.harvard.edu/abs/1906AnP...326..756V). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/andp.19063261405](https://doi.org/10.1002%2Fandp.19063261405).
32. ^   Merritt, David (2013). *Dynamics and Evolution of Galactic Nuclei*. Princeton University Press. p. 575. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-4008-4612-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4008-4612-2). [OL](https://en.wikipedia.org/wiki/OL_(identifier)) [16802359W](https://openlibrary.org/works/OL16802359W).
33. Reid, M. J.; Brunthaler, A. (2004). "The Proper Motion of Sagittarius A\*. II. The Mass of Sagittarius A\*". *[The Astrophysical Journal](https://en.wikipedia.org/wiki/The_Astrophysical_Journal)*. **616** (2): 872–884. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[astro-ph/0408107](https://arxiv.org/abs/astro-ph/0408107). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2004ApJ...616..872R](https://ui.adsabs.harvard.edu/abs/2004ApJ...616..872R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1086/424960](https://doi.org/10.1086%2F424960). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [16568545](https://api.semanticscholar.org/CorpusID:16568545).
34. Bass, Richard F. (2011). [Stochastic Processes](https://www.cambridge.org/core/books/stochastic-processes/055A84B1EB586FE3032C0CA7D49598AC). Cambridge Series in Statistical and Probabilistic Mathematics. Cambridge: Cambridge University Press. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9780511997044](https://doi.org/10.1017%2Fcbo9780511997044). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-107-00800-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-107-00800-7).
35. Sheffield, Scott (9 May 2007). ["Gaussian free fields for mathematicians"](https://link.springer.com/10.1007/s00440-006-0050-1). *Probability Theory and Related Fields*. **139** (3–4): 521–541. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[math/0312099](https://arxiv.org/abs/math/0312099). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1007/s00440-006-0050-1](https://doi.org/10.1007%2Fs00440-006-0050-1). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [0178-8051](https://search.worldcat.org/issn/0178-8051).
36. Weiss, G. H. (1994). *Aspects and applications of the random walk*. North Holland.
37. Morozov, A. N.; Skripkin, A. V. (2011). "Spherical particle Brownian motion in viscous medium as non-Markovian random process". *[Physics Letters A](https://en.wikipedia.org/wiki/Physics_Letters_A)*. **375** (46): 4113–4115. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2011PhLA..375.4113M](https://ui.adsabs.harvard.edu/abs/2011PhLA..375.4113M). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1016/j.physleta.2011.10.001](https://doi.org/10.1016%2Fj.physleta.2011.10.001).
38. Karczub, D. G.; Norton, M. P. (2003). *Fundamentals of Noise and Vibration Analysis for Engineers by M. P. Norton*. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1017/cbo9781139163927](https://doi.org/10.1017%2Fcbo9781139163927). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-139-16392-7](https://en.wikipedia.org/wiki/Special:BookSources/978-1-139-16392-7).
39. ^   Krapf, Diego; Marinari, Enzo; Metzler, Ralf; Oshanin, Gleb; Xu, Xinran; Squarcini, Alessio (2018). ["Power spectral density of a single Brownian trajectory: what one can and cannot learn from it"](https://iopscience.iop.org/article/10.1088/1367-2630/aaa67c). *New Journal of Physics*. **20** (2): 023029. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1801.02986](https://arxiv.org/abs/1801.02986). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2018NJPh...20b3029K](https://ui.adsabs.harvard.edu/abs/2018NJPh...20b3029K). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1088/1367-2630/aaa67c](https://doi.org/10.1088%2F1367-2630%2Faaa67c). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1367-2630](https://search.worldcat.org/issn/1367-2630). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [485685](https://api.semanticscholar.org/CorpusID:485685).

## Further reading

- Brown, Robert (1828). ["A brief account of microscopical observations made in the months of June, July and August, 1827, on the particles contained in the pollen of plants; and on the general existence of active molecules in organic and inorganic bodies"](http://sciweb.nybg.org/science2/pdfs/dws/Brownian.pdf) (PDF). *[Philosophical Magazine](https://en.wikipedia.org/wiki/Philosophical_Magazine)*. **4** (21): 161–173. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1080/14786442808674769](https://doi.org/10.1080%2F14786442808674769). [Archived](https://ghostarchive.org/archive/20221009/http://sciweb.nybg.org/science2/pdfs/dws/Brownian.pdf) (PDF) from the original on 9 October 2022. Also includes a subsequent defense by Brown of his original observations, *Additional remarks on active molecules*.
- Chaudesaigues, M. (1908). "Le mouvement brownien et la formule d'Einstein" \[Brownian motion and Einstein's formula\]. *[Comptes Rendus](https://en.wikipedia.org/wiki/Comptes_Rendus)* (in French). **147**: 1044–6.
- Clark, P. (1976). "Atomism versus thermodynamics". In Howson, Colin (ed.). [Method and appraisal in the physical sciences](https://archive.org/details/methodappraisali0000unse). Cambridge University Press. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-521-21110-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-521-21110-9).
- Cohen, Ruben D. (1986). ["Self Similarity in Brownian Motion and Other Ergodic Phenomena"](http://rdcohen.50megs.com/BrownianMotion.pdf) (PDF). *[Journal of Chemical Education](https://en.wikipedia.org/wiki/Journal_of_Chemical_Education)*. **63** (11): 933–934. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1986JChEd..63..933C](https://ui.adsabs.harvard.edu/abs/1986JChEd..63..933C). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1021/ed063p933](https://doi.org/10.1021%2Fed063p933). [Archived](https://ghostarchive.org/archive/20221009/http://rdcohen.50megs.com/BrownianMotion.pdf) (PDF) from the original on 9 October 2022.
- Dubins, Lester E.; Schwarz, Gideon (15 May 1965). ["On Continuous Martingales"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC301348). *[Proceedings of the National Academy of Sciences of the United States of America](https://en.wikipedia.org/wiki/Proceedings_of_the_National_Academy_of_Sciences_of_the_United_States_of_America)*. **53** (3): 913–916. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1965PNAS...53..913D](https://ui.adsabs.harvard.edu/abs/1965PNAS...53..913D). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1073/pnas.53.5.913](https://doi.org/10.1073%2Fpnas.53.5.913). [JSTOR](https://en.wikipedia.org/wiki/JSTOR_(identifier)) [72837](https://www.jstor.org/stable/72837). [PMC](https://en.wikipedia.org/wiki/PMC_(identifier)) [301348](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC301348). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [16591279](https://pubmed.ncbi.nlm.nih.gov/16591279).
- Einstein, A. (1956). [Investigations on the Theory of Brownian Movement](https://archive.org/details/investigationson00eins). New York: Dover. [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-0-486-60304-9](https://en.wikipedia.org/wiki/Special:BookSources/978-0-486-60304-9). Retrieved 6 January 2014. `{{`[`cite book`](https://en.wikipedia.org/wiki/Template:Cite_book)`}}`: ISBN / Date incompatibility ([help](https://en.wikipedia.org/wiki/Help:CS1_errors#invalid_isbn_date))
- Henri, V. (1908). "Études cinématographique du mouvement brownien" \[Cinematographic studies of Brownian motion\]. *[Comptes Rendus](https://en.wikipedia.org/wiki/Comptes_Rendus)* (in French) (146): 1024–6.
- [Lucretius](https://en.wikipedia.org/wiki/Lucretius), *On The Nature of Things*, translated by [William Ellery Leonard](https://en.wikipedia.org/wiki/William_Ellery_Leonard). (*[on-line version](http://onlinebooks.library.upenn.edu/webbin/gutbook/lookup?num=785)*, from [Project Gutenberg](https://en.wikipedia.org/wiki/Project_Gutenberg). See the heading 'Atomic Motions'; this translation differs slightly from the one quoted).
- [Nelson, Edward](https://en.wikipedia.org/wiki/Edward_Nelson), (1967). *Dynamical Theories of Brownian Motion*. [(PDF version of this out-of-print book, from the author's webpage.)](https://web.math.princeton.edu/~nelson/books/bmotion.pdf) This is primarily a mathematical work, but the first four chapters discuss the history of the topic, in the era from Brown to Einstein.
- Pearle, P.; Collett, B.; Bart, K.; Bilderback, D.; Newman, D.; Samuels, S. (2010). "What Brown saw and you can too". *[American Journal of Physics](https://en.wikipedia.org/wiki/American_Journal_of_Physics)*. **78** (12): 1278–1289. [arXiv](https://en.wikipedia.org/wiki/ArXiv_(identifier)):[1008.0039](https://arxiv.org/abs/1008.0039). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2010AmJPh..78.1278P](https://ui.adsabs.harvard.edu/abs/2010AmJPh..78.1278P). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1119/1.3475685](https://doi.org/10.1119%2F1.3475685). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [12342287](https://api.semanticscholar.org/CorpusID:12342287).
- Perrin, J. (1909). "Mouvement brownien et réalité moléculaire" \[Brownian movement and molecular reality\]. *[Annales de chimie et de physique](https://en.wikipedia.org/wiki/Annales_de_chimie_et_de_physique)*. 8th series. **18**: 5–114.
  - See also Perrin's book "Les Atomes" (1914).
- von Smoluchowski, M. (1906). ["Zur kinetischen Theorie der Brownschen Molekularbewegung und der Suspensionen"](http://gallica.bnf.fr/ark:/12148/bpt6k15328k/f770.chemindefer). *[Annalen der Physik](https://en.wikipedia.org/wiki/Annalen_der_Physik)*. **21** (14): 756–780. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[1906AnP...326..756V](https://ui.adsabs.harvard.edu/abs/1906AnP...326..756V). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1002/andp.19063261405](https://doi.org/10.1002%2Fandp.19063261405).
- Svedberg, T. (1907). *Studien zur Lehre von den kolloiden Losungen*.
- [Theile, T. N](https://en.wikipedia.org/wiki/Thorvald_N._Thiele).
  - Danish version: "Om Anvendelse af mindste Kvadraters Methode i nogle Tilfælde, hvor en Komplikation af visse Slags uensartede tilfældige Fejlkilder giver Fejlene en 'systematisk' Karakter".
  - French version: "Sur la compensation de quelques erreurs quasi-systématiques par la méthodes de moindre carrés" published simultaneously in *Vidensk. Selsk. Skr. 5. Rk., naturvid. og mat. Afd.*, 12:381–408, 1880.

## External links

- [Einstein on Brownian Motion](https://web.archive.org/web/20010222031055/http://www.bun.kyoto-u.ac.jp/~suchii/einsteinBM.html)
- [Discusses history, botany and physics of Brown's original observations, with videos](http://physerver.hamilton.edu/Research/Brownian/index.html)
- ["Einstein's prediction finally witnessed one century later"](http://www.gizmag.com/einsteins-prediction-finally-witnessed/16212/) : a test to observe the velocity of Brownian motion
- [Large-Scale Brownian Motion Demonstration](https://web.archive.org/web/20220331054344/https://demos.smu.ca/demos/thermo/90-brownian-motion)
