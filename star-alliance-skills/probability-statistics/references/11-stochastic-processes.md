# Stochastic Processes: Markov Chains, Martingales, Brownian Motion, and Poisson Processes

A stochastic process is a sequence of random variables indexed by time, written $X_0, X_1, X_2, \ldots$ (discrete-time) or $\{X_t : t \geq 0\}$ (continuous-time), where the value at time $n$ may depend on past values. This reference covers discrete-time processes (random walks, Markov chains, martingales), continuous-time processes (Brownian motion, Poisson processes), and computational techniques (Markov Chain Monte Carlo). Foundational concepts include the Markov property (future conditionally independent of past given present), stationarity, reversibility, and the fundamental limit theorems governing long-run behavior.

---

## Simple Random Walk

### Definition and Construction

Let $Z_1, Z_2, \ldots$ be i.i.d. with $P(Z_i = 1) = p$ and $P(Z_i = -1) = q = 1-p$, where $0 < p < 1$. The simple random walk is
$$X_0 = a, \qquad X_n = a + Z_1 + Z_2 + \cdots + Z_n \quad (n \geq 1).$$
The walk models a gambler with initial fortune $a$, winning $\$1$ with probability $p$ and losing $\$1$ with probability $q$ at each bet. The game is **fair** if $p = 1/2$, **subfair** if $p < 1/2$, and **superfair** if $p > 1/2$.

### Distribution of the Fortune

**Theorem (Distribution of $X_n$).** Let $W_n$ be the number of wins among the first $n$ bets. Then $W_n \sim \text{Binomial}(n, p)$, and $X_n = a + 2W_n - n$. For any integer $k$ with $|k| \leq n$ and $n-k$ even:
$$P(X_n = a + k) = \binom{n}{(n+k)/2} p^{(n+k)/2} q^{(n-k)/2}.$$
For all other $k$, $P(X_n = a + k) = 0$. The expected value is
$$E[X_n] = a + n(2p - 1).$$

The parity constraint (parity of $n+k$ must be even) follows from the fact that $X_n - a$ has the same parity as $n$.

### Game Classification

| Condition | Classification | Long-run $E[X_n]$ |
|-----------|---------------|---------------------|
| $p = 1/2$ | Fair | $E[X_n] = a$ for all $n$ |
| $p < 1/2$ | Subfair | $E[X_n] < a$ for $n \geq 1$ |
| $p > 1/2$ | Superfair | $E[X_n] > a$ for $n \geq 1$ |

Real casinos operate subfair games, so the long-run expected fortune is below the entry fortune.

### Gambler's Ruin Problem

Let $0 < a < c$ be integers and define the first hitting times
$$\tau_0 = \min\{n \geq 0 : X_n = 0\}, \qquad \tau_c = \min\{n \geq 0 : X_n = c\}.$$

**Theorem (Gambler's Ruin).** The probability of reaching $\$c$ before going broke is
$$P(\tau_c < \tau_0) = \begin{cases} \dfrac{a}{c} & \text{if } p = 1/2, \\[8pt] \dfrac{1 - (q/p)^a}{1 - (q/p)^c} & \text{if } p \neq 1/2. \end{cases}$$

**Theorem (Ruin probability).** For $a > 0$,
$$P(\tau_0 < \infty) = \begin{cases} 1 & \text{if } p = 1/2, \\ (q/p)^a & \text{if } p < 1/2, \\ 0 & \text{if } p > 1/2. \end{cases}$$

When $p < 1/2$, the probability of ruin grows exponentially toward 1 as initial fortune $a$ increases; even tiny per-bet disadvantages compound dramatically over many bets.

### Strategy Note: Double-Til-You-Win

Bet $\$1$ first; if you lose, double the bet; continue doubling until a win, then stop. Since $p > 0$, a win eventually occurs with probability 1, and the net gain is $\$1$ regardless of $p$. The catch: arbitrarily large capital may be needed before the first win, so this "cheats fate" only with infinite capital.

---

## Markov Chains

### Markov Property

A random process $\{\tilde{X}(t)\}$ satisfies the **Markov property** if, for any $t_1 < t_2 < \cdots < t_i < t_{i+1}$ and any admissible values,
$$p_{\tilde{X}(t_{i+1})|\tilde{X}(t_1), \ldots, \tilde{X}(t_i)}(x_{i+1}|x_1, \ldots, x_i) = p_{\tilde{X}(t_{i+1})|\tilde{X}(t_i)}(x_{i+1}|x_i)$$
for discrete state spaces, with the analogous density form $f_{\cdot|\cdot}$ for continuous state spaces. The future is conditionally independent of the past given the present.

### Time-Homogeneous Finite-State Markov Chains

A **Markov chain** is a sequence $X_0, X_1, X_2, \ldots$ on a state space $S$ with **transition probabilities** $p_{ij}$ satisfying
$$P(X_{n+1} = j \mid X_n = i) = p_{ij}, \qquad p_{ij} \geq 0, \qquad \sum_{j \in S} p_{ij} = 1,$$
and where the jump probability does not depend on the chain's previous history. An **initial distribution** $\lambda_i = P(X_0 = i)$ satisfies $\lambda_i \geq 0$, $\sum_i \lambda_i = 1$.

The chain is **time-homogeneous** if the transition probabilities are constant over time. For a finite state space of size $s$, the transition matrix $T_{\tilde{X}}$ has entries $(T_{\tilde{X}})_{jk} = p_{\tilde{X}(i+1)|\tilde{X}(i)}(x_j | x_k)$, with each column summing to 1.

**Joint distribution** of the chain at $n+1$ time points:
$$p_{\tilde{X}(0), \ldots, \tilde{X}(n)}(x_0, \ldots, x_n) = \prod_{i=0}^{n} p_{\tilde{X}(i)|\tilde{X}(i-1)}(x_i | x_{i-1}).$$

**State vector** at time $i$:
$$\vec{p}_{\tilde{X}(i)} = \begin{bmatrix} P(\tilde{X}(i) = x_1) \\ \vdots \\ P(\tilde{X}(i) = x_s) \end{bmatrix}.$$

**Lemma (State vector recursion).** $\vec{p}_{\tilde{X}(i)} = T_{\tilde{X}} \vec{p}_{\tilde{X}(i-1)}$, and by induction
$$\vec{p}_{\tilde{X}(i)} = T_{\tilde{X}}^i \, \vec{p}_{\tilde{X}(0)}.$$

For a Markov chain starting at state $i$ (i.e., $\lambda_i = 1$), the higher-order transition probabilities are
$$P_i(X_n = j) = \sum_{i_1, \ldots, i_{n-1} \in S} p_{i,i_1} p_{i_1, i_2} \cdots p_{i_{n-1}, j},$$
which is the $(i,j)$ entry of $T_{\tilde{X}}^n$.

### Standard Examples

| Example | State space | Transition structure |
|---------|-------------|----------------------|
| Simple random walk | $\mathbb{Z}$ | $p_{i,i+1} = p$, $p_{i,i-1} = q$ |
| Random walk on circle | $\{0, 1, \ldots, d-1\}$ | $p_{i,i} = 1/3$, neighbors with prob $1/3$ each |
| Ehrenfest's urn | $\{0, 1, \ldots, d\}$ | $p_{i,i-1} = i/d$, $p_{i,i+1} = (d-i)/d$ |
| Weather chain | $\{0, 1\}$ | arbitrary $2 \times 2$ stochastic matrix |

For **Ehrenfest's urn** with $d$ balls split between two urns: at each step, choose one ball uniformly at random and switch urns. The number $X_n$ of balls in urn #1 follows the stated transition probabilities.

### Stationary Distributions

A distribution $\{\pi_i : i \in S\}$ is **stationary** if, for all $j \in S$,
$$\sum_{i \in S} \pi_i \, p_{ij} = \pi_j, \quad \text{i.e.,} \quad \vec{\pi} \, T_{\tilde{X}} = \vec{\pi}.$$

Equivalently, $\pi$ is a left eigenvector of $T_{\tilde{X}}$ with eigenvalue 1. If $P(X_n = i) = \pi_i$ for all $i$ at some time $n$, then $P(X_m = i) = \pi_i$ for all $m \geq n$.

**Theorem (Reversibility implies stationarity).** If a chain is **reversible** with respect to $\pi$ (i.e., $\pi_i p_{ij} = \pi_j p_{ji}$ for all $i, j \in S$), then $\pi$ is stationary. Reversibility is sufficient but not necessary.

**Doubly stochastic matrices** (rows and columns each sum to 1) have the uniform distribution as stationary.

### Irreducibility and Period

A chain is **irreducible** if for every pair $i, j \in S$ there exists $n \geq 1$ with $P_i(X_n = j) > 0$. Equivalently, every state is reachable from every other state in some number of steps.

The **period** of state $i$ is $\gcd\{n \geq 1 : p_{ii}^{(n)} > 0\}$ where $p_{ii}^{(n)} = P_i(X_n = i)$. A chain is **aperiodic** if every state has period 1.

**Sufficient condition.** If $p_{ij} > 0$ for all $i, j \in S$, the chain is irreducible and aperiodic.

### Recurrent and Transient States

State $x$ is **recurrent** if $P(\tilde{X}(j) = x \text{ for some } j > i \mid \tilde{X}(i) = x) = 1$, and **transient** if this probability is less than 1 (equivalently, the probability of never returning is positive).

**Theorem.** All states in an irreducible finite-state Markov chain are recurrent.

### Convergence to Stationary Distribution

**Theorem (Markov Chain Limit Theorem).** If a Markov chain is **irreducible and aperiodic** with stationary distribution $\pi$, then
$$\lim_{n \to \infty} P(X_n = i) = \pi_i \quad \text{for all } i \in S,$$
regardless of the initial distribution. Such chains are called **ergodic**.

For an irreducible chain, Perron-Frobenius guarantees a unique stationary distribution.

**Eigendecomposition approach.** If $T_{\tilde{X}} = Q \Lambda Q^{-1}$ with eigenvalues $\lambda_1 = 1, \lambda_2, \ldots, \lambda_s$ where $|\lambda_k| < 1$ for $k \geq 2$, then
$$\vec{p}_{\tilde{X}(i)} = \pi + \sum_{k=2}^{s} c_k \lambda_k^i \vec{q}_k \to \pi$$
as $i \to \infty$, where $c_k$ depends on the initial distribution and the eigenvectors $\vec{q}_k$.

### When Convergence Fails

Two obstacles prevent convergence to a stationary distribution:
1. **Non-irreducible chains:** Some states are unreachable from others.
2. **Periodic chains:** If the chain has period $m > 1$, then $P(X_n = i) = 0$ for many values of $n$, preventing convergence.

---

## Markov Chain Monte Carlo (MCMC)

### Problem Setup

Many distributions of interest lack a tractable direct simulation method. MCMC sidesteps this by constructing a Markov chain whose stationary distribution equals the target.

**Theorem (MCMC Estimation).** Let $X^{(i)}_0, X^{(i)}_1, \ldots, X^{(i)}_N$ for $i = 1, \ldots, M$ be independent runs of an irreducible, aperiodic Markov chain with stationary distribution $\pi$, where $\pi_j = P(Z = j)$. Then
$$\hat{A} = \frac{1}{M} \sum_{i=1}^{M} h(X^{(i)}_N) \approx E[h(Z)] = A$$
for large $M$ and $N$.

**Single-chain variant (with burn-in $B$):**
$$\hat{A} = \frac{1}{N - B + 1} \sum_{i=B}^{N} h(X_i) \approx A,$$
where $B$ is a burn-in time to wash out the influence of the initial state.

### Metropolis-Hastings Algorithm

Given a target distribution $\pi$ on state space $S$ and an arbitrary irreducible proposal chain $q_{ij}$:

1. Given $X_n = i$, sample candidate $Y_{n+1} = j$ from $q_{ij}$.
2. Compute the **acceptance probability**
$$\alpha_{ij} = \min\left(1, \frac{\pi_j \, q_{ji}}{\pi_i \, q_{ij}}\right).$$
3. With probability $\alpha_{ij}$, accept: $X_{n+1} = j$. Otherwise, reject: $X_{n+1} = i$.

**Theorem.** The resulting chain $\{X_n\}$ is reversible with respect to $\pi$, hence has $\pi$ as a stationary distribution. The normalizing constant of $\pi$ cancels in $\alpha_{ij}$ — only ratios of target probabilities are needed.

For continuous targets with density $f(y)$, use proposal density $q(x, y)$ and acceptance
$$\alpha_{xy} = \min\left(1, \frac{f(y) \, q(y, x)}{f(x) \, q(x, y)}\right).$$

### Gibbs Sampler

For multivariate state space $S$ with target $\pi$, the **Gibbs sampler** is Metropolis-Hastings with special proposals that always accept:

1. Conditional on $X_n = (i_1, \ldots, i_d)$, propose $Y$ on the slice where all coordinates except the $k$-th are fixed at $i_1, \ldots, i_{k-1}, i_{k+1}, \ldots, i_d$, drawing the $k$-th coordinate from its conditional distribution $\pi(\cdot | \text{others})$.
2. Always accept: $X_{n+1} = Y$.

Alternating between coordinate updates (e.g., vertical then horizontal moves on a grid) yields an irreducible, aperiodic chain with $\pi$ stationary. The acceptance probability is identically 1.

### Practical Issues

- **Burn-in:** The mixing time (number of iterations until the chain is approximately stationary) may be hundreds or thousands of steps. Disregard early samples.
- **Total budget:** With a fixed iteration budget $N \cdot M$, moderate $N$ and $M$ (e.g., $N = 1000, M = 1000$) generally outperform extremes (e.g., $N = 10^6, M = 1$).

---

## Martingales

### Definition

A Markov chain $\{X_n\}$ is a **martingale** if, for all $n \geq 0$,
$$E[X_{n+1} \mid X_n = X_n^{(n)}, \ldots, X_0] = X_n,$$
i.e., the chain stays the same on average, regardless of its current value. Equivalently, $E[X_{n+1} \mid \mathcal{F}_n] = X_n$ where $\mathcal{F}_n$ is the sigma-algebra generated by $X_0, \ldots, X_n$.

### Examples and Construction

**Simple random walk** with $p = 1/2$ is a martingale because $E[X_{n+1} - X_n \mid X_n] = p - q = 0$.

**Doubling strategy check:** If $X_{n+1} - X_n = +3$ with prob $1/4$ and $-1$ with prob $3/4$, then $E[X_{n+1} - X_n \mid X_n] = 3/4 - 3/4 = 0$, so $\{X_n\}$ is a martingale.

**Transformed random walk:** For simple random walk with general $p$, define
$$Z_n = \left(\frac{1-p}{p}\right)^{X_n}.$$
This is a martingale because increasing $X_n$ by 1 multiplies $Z_n$ by $(1-p)/p$ with probability $p$, while decreasing multiplies by $p/(1-p)$ with probability $q$, and the expected value telescopes to $Z_n$.

### Expected Value Property

**Theorem.** If $\{X_n\}$ is a martingale with $X_0 = a$, then $E[X_n] = a$ for all $n \geq 0$. This follows by iterating the martingale property:
$$E[X_{n+1}] = E[E[X_{n+1} \mid X_n]] = E[X_n] = \cdots = X_0.$$

### Stopping Times

A random variable $T$ taking values in $\{0, 1, 2, \ldots\}$ is a **stopping time** for $\{X_n\}$ if the event $\{T = m\}$ is independent of $X_{m+1}, X_{m+2}, \ldots$ for all $m$. Equivalently, the decision to stop at time $m$ depends only on $X_0, \ldots, X_m$, not future values.

**Examples:** $T_b = \min\{n \geq 0 : X_n = b\}$ is a stopping time; $T_b - 1$ (stop just before hitting $b$) is not.

**Combinations:** $\min(T_1, T_2)$ is a stopping time, but $\max(T_1, T_2)$ is generally not.

### Optional Stopping Theorem

**Theorem.** Let $\{X_n\}$ be a martingale with $X_0 = a$ and $T$ a stopping time. If either:
- (a) The martingale is bounded up to time $T$: $|X_n| \leq M$ for all $n \leq T$, **or**
- (b) The stopping time is bounded: $T \leq M$,

then $E[X_T] = a$.

This is the principal tool for computing hitting probabilities in martingale problems.

### Application: Gambler's Ruin via Martingales

For $p = 1/2$, let $T = \min(\tau_r, \tau_s)$ where $r < a < s$. Then $|X_n| \leq \max(|r|, |s|)$ for $n \leq T$, so by optional stopping $E[X_T] = a$. With probability $h$ the walk hits $r$ and with probability $1-h$ it hits $s$, giving
$$a = h \cdot r + (1-h) \cdot s \quad \Rightarrow \quad h = \frac{a - s}{r - s}.$$
For $r = 0, s = c$: $P(\tau_c < \tau_0) = a/c$.

For $p \neq 1/2$, use $Z_n = (q/p)^{X_n}$, a martingale, to obtain
$$P(\tau_c < \tau_0) = \frac{1 - (q/p)^a}{1 - (q/p)^c},$$
matching the gambler's ruin formula with much less effort than direct computation.

### Pitfall: Unbounded Cases

If neither boundedness condition holds, the optional stopping theorem may fail. Example: $T = \tau_1$ for $X_0 = 0$ with $p = 1/2$. Then $X_T = 1$ with probability 1, so $E[X_T] = 1 \neq 0 = X_0$, because the walk can drift arbitrarily far before hitting 1.

---

## Brownian Motion

### Construction as a Limit of Random Walks

Let $Z_1, Z_2, \ldots$ be i.i.d. with $P(Z_i = \pm 1) = 1/2$. Define the speeded-up, space-shrunken random walk
$$Y^{(M)}_{i/M} = \frac{1}{M} \sum_{k=1}^{i} Z_k, \quad Y^{(M)}_0 = 0,$$
extended linearly between integer multiples of $1/M$. As $M \to \infty$, $Y^{(M)}_t$ converges in distribution to a limit process $\{B_t : t \geq 0\}$, which is **Brownian motion** (also called the **Wiener process**).

### Defining Properties of Brownian Motion

A process $\{B_t : t \geq 0\}$ is a (standard) Brownian motion if:

1. $B_0 = 0$.
2. $B_t \sim N(0, t)$ for all $t \geq 0$: $E[B_t] = 0$, $\text{Var}(B_t) = t$.
3. For $0 \leq s < t$, the increment $B_t - B_s \sim N(0, t-s)$ and is independent of $\{B_u : u \leq s\}$.
4. The map $t \mapsto B_t$ is continuous (with probability 1).

**Covariance:** $\text{Cov}(B_s, B_t) = \min(s, t)$ for $s, t \geq 0$.

**Key consequence:** Brownian motion is a martingale ($E[B_{t+h} \mid B_t] = B_t$).

### Computations with Brownian Motion

For any $t > 0$, normalize $B_t / \sqrt{t} \sim N(0, 1)$. Use the standard normal CDF $\Phi(x) = P(Z \leq x)$ for $Z \sim N(0, 1)$.

| Quantity | Computation |
|----------|-------------|
| $P(B_t \leq x)$ | $\Phi(x / \sqrt{t})$ |
| $P(B_t - B_s \leq x)$ | $\Phi(x / \sqrt{t-s})$ for $s < t$ |
| $E[B_t B_s]$ | $\min(s, t)$ |
| $E[B_t^2]$ | $t$ |

For joint or conditional events, use independence of $B_s$ and $B_t - B_s$.

### Hitting Probabilities

For $c > 0 > b$, let $T = \min(\tau_c, \tau_b)$ where $\tau_x = \inf\{t \geq 0 : B_t = x\}$. By the optional stopping theorem (with boundedness $|B_t| \leq \max(|b|, c)$ for $t \leq T$):
$$0 = E[B_T] = h \cdot c + (1-h) \cdot b \quad \Rightarrow \quad h = P(\tau_c < \tau_b) = \frac{-b}{c - b}.$$

### Nondifferentiability

Brownian motion is continuous everywhere but differentiable **nowhere** (with probability 1). A heuristic indicator: $E[(B_{t+h} - B_t)^2] / h = h \to 0$, whereas a differentiable function would have a nonzero limit. The infinite variation makes Brownian motion a poor model for actual physical particle motion but useful for finance and as a mathematical limit object.

### Diffusion Processes and Stock Prices

A **diffusion** is $X_t = a + \mu t + \sigma B_t$ where $a$ is the initial value, $\mu$ the **drift**, and $\sigma$ the **volatility parameter**. Then:
- $E[X_t] = a + \mu t$
- $\text{Var}(X_t) = \sigma^2 t$
- $X_t \sim N(a + \mu t, \sigma^2 t)$

**Stock price model:** $X_t$ represents the price at time $t$. Probabilities of price thresholds are computed by standardizing:
$$P(X_t \leq x) = \Phi\left(\frac{x - (a + \mu t)}{\sigma \sqrt{t}}\right).$$

---

## Poisson Processes

### Definition

Let $R_1, R_2, \ldots$ be i.i.d. $\text{Exponential}(a)$ with density $f(r) = a e^{-ar}$ for $r \geq 0$, $a > 0$. Define arrival times and counting process:
$$T_0 = 0, \qquad T_n = R_1 + R_2 + \cdots + R_n, \qquad N_t = \max\{n : T_n \leq t\}.$$
$N_t$ counts the number of events by time $t$. The collection $\{N_t : t \geq 0\}$ is a **Poisson process** with intensity (rate) $a$.

### Distributional Properties

**Theorem (Number of events).** For all $t \geq 0$, $N_t \sim \text{Poisson}(at)$:
$$P(N_t = k) = \frac{(at)^k e^{-at}}{k!}, \quad k = 0, 1, 2, \ldots$$
Mean and variance: $E[N_t] = at$, $\text{Var}(N_t) = at$.

**Theorem (Independent increments).** For $0 = t_0 < t_1 < \cdots < t_d$, the increments $N_{t_i} - N_{t_{i-1}}$ are independent with $N_{t_i} - N_{t_{i-1}} \sim \text{Poisson}(a(t_i - t_{i-1}))$.

This follows from the memoryless property of the exponential distribution: regardless of $N_s$ for $s \leq t_{i-1}$, the future from $t_{i-1}$ onward looks like a fresh Poisson process with that starting count.

### Computation Pattern

For joint probabilities, use independent increments:
$$P(N_s = j, N_t = k) = P(N_s = j) \cdot P(N_t - N_s = k - j) \quad (j \leq k,\; s < t).$$

For conditional probabilities of the form $P(N_s = j \mid N_t = k)$ with $j \leq k$, $s < t$, the result is **Binomial**:
$$P(N_s = j \mid N_t = k) = \binom{k}{j} \left(\frac{s}{t}\right)^j \left(1 - \frac{s}{t}\right)^{k-j}.$$
This does not depend on the intensity $a$.

### Derivation Sketch

Since $T_n = R_1 + \cdots + R_n$ is the sum of $n$ i.i.d. Exponential$(a)$ variables, $T_n \sim \text{Gamma}(n, a)$ with density
$$g_n(t) = \frac{a^n t^{n-1} e^{-at}}{(n-1)!}, \quad t \geq 0.$$
Then $P(N_t \geq n) = P(T_n \leq t) = \int_0^t g_n(s) \, ds$. Using the identity
$$\int_0^t g_n(s) \, ds = \sum_{k=n}^{\infty} \frac{(at)^k e^{-at}}{k!},$$
one obtains $P(N_t = j) = (at)^j e^{-at} / j!$.

---

## Related Distributions and Limit Theorems

### Chebyshev's Theorem

**Theorem (Chebyshev).** For any random variable $X$ with mean $\mu$ and variance $\sigma^2$, and any $k > 0$:
$$P(|X - \mu| \geq k\sigma) \leq \frac{1}{k^2}, \qquad P(|X - \mu| < k\sigma) \geq 1 - \frac{1}{k^2}.$$

**Proof sketch.** Partition the sample space into $R_1 = \{x : x - \mu \leq -k\sigma\}$, $R_2 = \{|x - \mu| < k\sigma\}$, $R_3 = \{x - \mu \geq k\sigma\}$. Since $(x - \mu)^2 \geq k^2 \sigma^2$ on $R_1 \cup R_3$:
$$\sigma^2 \geq \sum_{R_1} (x-\mu)^2 f(x) + \sum_{R_3} (x-\mu)^2 f(x) \geq k^2 \sigma^2 [P(R_1) + P(R_3)] = k^2 \sigma^2 P(|X-\mu| \geq k\sigma).$$

**Strengths/weaknesses:** Applies to any distribution but gives only upper bounds on tail probabilities — often loose compared to exact values (e.g., 0.25 vs. 0.077 for Binomial(16, 1/2) at $k=2$).

**Application to Law of Large Numbers.** For $X_i$ i.i.d. with mean $\mu$ and variance $\sigma^2$, the sample mean $\bar{X}_n = (1/n) \sum X_i$ satisfies $P(|\bar{X}_n - \mu| < \epsilon) \geq 1 - \sigma^2/(n\epsilon^2) \to 1$ as $n \to \infty$. For Binomial, this yields the **law of large numbers**: the proportion of successes converges in probability to $p$.

### Poisson Distribution

The **Poisson distribution** with parameter $\lambda > 0$ has pmf
$$f(x; \lambda) = \frac{\lambda^x e^{-\lambda}}{x!}, \quad x = 0, 1, 2, \ldots$$
with $E[X] = \text{Var}(X) = \lambda$. It serves as a model for unbounded counts: events per unit time/space. Recursion: $f(x+1; \lambda) / f(x; \lambda) = \lambda / (x+1)$.

**Poisson approximation to binomial.** When $n$ is large, $p$ is small, with $\lambda = np$ held fixed:
$$\binom{n}{x} p^x (1-p)^{n-x} \to \frac{\lambda^x e^{-\lambda}}{x!}.$$
Rule of thumb: use Poisson approximation when $n \geq 20$ and $p \leq 0.05$; excellent when $n \geq 100$.

**Cumulative distribution:** $F(x; \lambda) = \sum_{k=0}^{x} f(k; \lambda)$, typically tabulated.

### Geometric and Negative Binomial Distributions

**Geometric distribution:** Number of trials until first success (inclusive):
$$g(x; p) = p(1-p)^{x-1}, \quad x = 1, 2, 3, \ldots$$
with $E[X] = 1/p$ and $\text{Var}(X) = (1-p)/p^2$.

**Negative binomial distribution:** Total trials to obtain $r$ successes:
$$f(x; r, p) = \binom{x-1}{r-1} p^r (1-p)^{x-r}, \quad x = r, r+1, \ldots$$
with $E[X] = r/p$ and $\text{Var}(X) = r(1-p)/p^2$. The geometric is the special case $r = 1$.

### Multinomial Distribution

For $n$ independent trials with $k$ mutually exclusive outcomes having probabilities $p_1, \ldots, p_k$ ($\sum p_i = 1$), the joint distribution of $(X_1, \ldots, X_k)$ where $X_i$ is the count of outcome $i$ is
$$f(x_1, \ldots, x_k) = \frac{n!}{x_1! x_2! \cdots x_k!} p_1^{x_1} p_2^{x_2} \cdots p_k^{x_k}, \quad \sum x_i = n.$$

| Distribution | Support | Pmf/Pdf | Mean | Variance |
|--------------|---------|---------|------|----------|
| Binomial$(n,p)$ | $\{0,\ldots,n\}$ | $\binom{n}{x}p^x(1-p)^{n-x}$ | $np$ | $np(1-p)$ |
| Poisson$(\lambda)$ | $\{0,1,2,\ldots\}$ | $\lambda^x e^{-\lambda}/x!$ | $\lambda$ | $\lambda$ |
| Geometric$(p)$ | $\{1,2,\ldots\}$ | $p(1-p)^{x-1}$ | $1/p$ | $(1-p)/p^2$ |
| Neg Bin$(r,p)$ | $\{r,r+1,\ldots\}$ | $\binom{x-1}{r-1}p^r(1-p)^{x-r}$ | $r/p$ | $r(1-p)/p^2$ |
| Multinomial | $\{(x_1,\ldots,x_k):\sum x_i = n\}$ | $n! \prod p_i^{x_i} / \prod x_i!$ | $np_i$ | $np_i(1-p_i)$ |

### Descriptive Statistics

For data $\{x_1, \ldots, x_n\}$:
- **Sample mean:** $\bar{x} = (1/n) \sum_{i=1}^n x_i$.
- **Sample variance:** $s^2 = \frac{1}{n-1} \sum_{i=1}^n (x_i - \bar{x})^2$.
- **Sample standard deviation:** $s = \sqrt{s^2}$.
- **Sample median:** middle value (or average of two middle values if $n$ is even).
- **$q$-quantile:** $x_{(\lceil q(n+1) \rceil)}$ in the ordered data. Quartiles are at $q = 0.25, 0.5, 0.75$; the **interquartile range** is $Q_3 - Q_1$.

The $1/(n-1)$ normalization in $s^2$ makes $E[s^2] = \sigma^2$ for i.i.d. data (unbiased estimator), whereas the $1/n$ version targets the maximum-likelihood quantity $E[(X-\mu)^2]$.

---

## Simulation and Monte Carlo

### Random Variable Generation

For **discrete** distributions with known pmf, use **inverse transform**: compute cumulative probabilities $F(x) = P(X \leq x)$, generate $U \sim \text{Uniform}(0,1)$, and return the smallest $x$ with $F(x) \geq U$.

For **binomial** $b(x; n, p)$: simulate as sum of $n$ Bernoulli$(p)$ variables; or use Poisson approximation for large $n$ and small $p$.

For **Poisson$(\lambda)$** (small $\lambda$): use the Knuth algorithm — repeatedly generate $U_i$ until $\prod U_i < e^{-\lambda}$; return $i - 1$.

### Monte Carlo Estimation

To estimate $E[h(Z)]$ for a distribution that is hard to sample directly:
1. Generate $Y_1, \ldots, Y_M \stackrel{iid}{\sim} \pi$ (the target distribution).
2. Return $\hat{A} = (1/M) \sum_{i=1}^M h(Y_i)$.

Error decreases as $O(1/\sqrt{M})$. For complex distributions, replace step 1 with MCMC sampling.

### Computational Strategy

When the target pmf/pdf is known only up to a normalizing constant (common in Bayesian posterior computation), MCMC methods like Metropolis-Hastings are essential because the ratio $f(x_1)/f(x_2)$ cancels the unknown constant. This is the key advantage over direct sampling.

---

## Key Theorems at a Glance

| Result | Statement | Use case |
|--------|-----------|----------|
| Markov property | Future ⊥ Past \| Present | Defining Markov chains |
| Gambler's ruin (fair) | $P(\tau_c < \tau_0) = a/c$ | Symmetric random walks |
| Gambler's ruin (unfair) | $(1-(q/p)^a)/(1-(q/p)^c)$ | Asymmetric random walks |
| Markov chain limit | $\pi_i = \lim P(X_n = i)$ if irreducible, aperiodic | Long-run behavior |
| Optional stopping | $E[X_T] = E[X_0]$ if bounded | Hitting probability problems |
| Reversibility | $\pi_i p_{ij} = \pi_j p_{ji} \Rightarrow \pi$ stationary | Finding stationary distributions |
| Chebyshev | $P(\|X-\mu\| \geq k\sigma) \leq 1/k^2$ | Universal tail bound |
| Poisson process | $N_t \sim \text{Poisson}(at)$ | Random event counts |
| Brownian motion | $B_t \sim N(0,t)$, independent increments | Continuous-time limits |
| Martingale property | $E[X_{n+1} \mid X_n] = X_n$ | Constructing unbiased processes |
