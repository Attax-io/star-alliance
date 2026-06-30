# Descriptive Statistics

Descriptive statistics condense raw data into graphical displays and numerical summaries that expose the central tendency, spread, shape, and unusual features of an observed data set. These summaries serve both as end products in their own right and as the foundation for formal statistical inference, where the sample quantities are interpreted as estimates of corresponding population parameters. The topics below cover one-dimensional descriptive methods (display, center, spread, order statistics), their multivariate extensions, the empirical cumulative distribution function, and the probabilistic properties that link these sample statistics to the underlying population distribution.

---

## Populations, Samples, and Variables

A **population** is the entire collection of units about which information is desired. A **sample** is a subset of the population actually observed. The **unit** (or **population unit**) is the individual object on which a measurement is taken, and the **variable of interest** is the characteristic being measured. A **statement of purpose** is a clear specification of the population, the variable, and the inferential goal, written before data collection begins.

Variables are classified along two axes:

| Type | Definition | Examples |
|---|---|---|
| **Quantitative** | Values are numerical and arithmetic is meaningful | Height, mass, time, current |
| **Categorical** | Values are labels that only classify | Gender, type of defect, color |
| **Discrete quantitative** | Takes isolated numerical values | Number of defects, count of arrivals |
| **Continuous quantitative** | Can in principle be measured to any precision | Length, voltage, time interval |

A **census** observes every member of a population; a **sampling study** observes only a subset selected by a known randomized mechanism; an **observational study** collects data that may or may not have arisen from a random mechanism and is therefore vulnerable to selection bias. Whenever feasible, sampling studies are preferred because every subset of size $n$ from a population of size $N$ has the same probability $1/\binom{N}{n}$ of being selected under **simple random sampling**, which avoids selection effects.

---

## Graphical Displays for One-Dimensional Data

### Dot Diagrams

A **dot diagram** plots each observation as a dot above a horizontal axis. Open and closed circles can distinguish groups. Dot diagrams are most useful for small samples (typically $n\le 25$); they expose outliers and gaps but lose effectiveness with large $n$. Each isolated, far-flung observation is an **outlier**, a value that does not fit the overall pattern.

### Frequency Distributions

A **frequency distribution** divides the data into $k$ non-overlapping **classes** with **class limits** (the endpoints of the original data values) and **class boundaries** (endpoints with consistent convention so no observation falls on two boundaries). For each class:

- **Class frequency** $f_i$ = number of observations in class $i$.
- **Relative frequency** $= f_i/n$.
- **Class mark** $m_i$ = midpoint of the class.
- **Class interval** $c$ = common width of classes.

Two endpoint conventions are used: the right-hand endpoint included $(a,c]$ or the left-hand endpoint included $[a,c)$. The chosen convention must be stated explicitly.

Practical guidelines for classes:

- Number of classes: usually 5 to 15; more for very large data sets.
- All classes equal width when possible.
- Class limits stated to as many decimal places as the original data.
- Use the boundary convention to avoid placing an observation on a class boundary.

### Histograms

A **histogram** consists of adjacent rectangles over the class intervals, with heights equal to class frequencies (or relative frequencies). The histogram for the **nanopillar height data** (50 observations, smallest 221, largest 391) using boundaries 205, 245, 285, 325, 365, 405 produces classes:

| Class | Frequency |
|---|---|
| (205, 245] | 3 |
| (245, 285] | 11 |
| (285, 325] | 23 |
| (325, 365] | 9 |
| (365, 405] | 4 |

**Density histogram**: when classes have unequal widths, the height must be set to relative frequency / width so that the area of each rectangle equals the relative frequency. Total area equals 1, which anticipates probability density functions. Always plot a density histogram, not a raw frequency histogram, for unequal class widths.

### Ogives

A **cumulative distribution** ("less than or equal to" or "less than") tabulates $F(x)$, the total number of observations $\le x$ (or $< x$) as $x$ ranges over class boundaries. An **ogive** is the line graph of this cumulative distribution plotted at the class boundaries. The steepest portion of the ogive corresponds to the modal class.

### Pareto Diagrams

A **Pareto diagram** is a bar chart with categories sorted by decreasing frequency, augmented with a cumulative-percentage curve. It is built on the empirical observation (Pareto's law) that a small number of categories often account for the majority of the total. Use it to identify the few vital opportunities that drive the majority of defects or losses.

### Stem-and-Leaf Displays

A **stem-and-leaf display** keeps all original information while exposing the distribution. The **stem** lists leading digits; the **leaves** are the trailing digits, written in ascending order. There must be no gaps in the stem, even for stems with no leaves. Variants:

- **Double-stem display**: each stem is repeated, with leaves 0–4 on the first, 5–9 on the second, doubling the number of stems.
- **Five-stem display**: each stem holds two adjacent leaf values (0,1), (2,3), (4,5), (6,7), (8,9), tripling the number of stems.

The leaf unit must be specified. For example, the display

$$1.2\ |\ 0\ 2\ 3\ 5\ 8,\quad \text{leaf unit}=0.01$$

represents the observations 1.20, 1.22, 1.23, 1.25, 1.28.

### Bar Charts and Pie Charts

A **bar chart** uses separated rectangles of equal width to display frequencies or proportions of categorical data. A **pie chart** divides a circle into sectors with area proportional to category frequency. Both are used for categorical data only; the bar positions on the horizontal axis are labels, not numerical values.

### Boxplots

A **boxplot** displays the five-number summary (minimum, $Q_1$, median, $Q_3$, maximum) as a box from $Q_1$ to $Q_3$ with an internal line at the median, and "whiskers" extending to the minimum and maximum.

A **modified boxplot** defines:

- **Upper limit** $=Q_3 + 1.5\cdot IQR$
- **Lower limit** $=Q_1 - 1.5\cdot IQR$
- **Upper adjacent value** = largest observation $\le$ upper limit
- **Lower adjacent value** = smallest observation $\ge$ lower limit

The whisker extends to the adjacent value; observations beyond it are plotted individually as outliers. This is Tukey's boxplot.

---

## Measures of Central Tendency

### Sample Mean

For observations $x_1,x_2,\ldots,x_n$:

$$\bar{x}=\frac{1}{n}\sum_{i=1}^{n} x_i$$

The sample mean has the physical interpretation of the **center of mass** (balance point) of the data when each observation is represented by a unit mass on a massless axis. It is the preferred measure in problems of estimation because it uses all the information in the data.

### Sample Median

Order the $n$ observations from smallest to largest. Then:

$$\text{sample median}=\begin{cases} x_{((n+1)/2)} & \text{if }n\text{ is odd,}\\[4pt] \tfrac{1}{2}\bigl(x_{(n/2)}+x_{(n/2+1)}\bigr) & \text{if }n\text{ is even.}\end{cases}$$

The median is the 50th percentile. It is **robust**: a single extreme observation can change $\bar{x}$ arbitrarily but cannot change the median by more than a single rank. The median is the preferred measure of location for skewed distributions and is unaffected by a small fraction of outliers.

### Weighted Mean

If observations $x_1,\ldots,x_k$ carry weights $w_1,\ldots,w_k$:

$$\bar{x}_w=\frac{\sum_{i=1}^{k} w_i x_i}{\sum_{i=1}^{k} w_i}$$

If a set of $k$ groups contains $n_i$ observations with mean $\bar{x}_i$, the **pooled mean** is $\bar{x}=\frac{\sum n_i \bar{x}_i}{\sum n_i}$, a special case with $w_i=n_i$.

### Mean vs Median

- $\bar{x}$ uses every observation; median uses only ranks.
- $\bar{x}$ is sensitive to outliers; median is resistant.
- For symmetric distributions they agree; for right-skewed data $\bar{x}>\text{median}$, and vice versa.
- A useful diagnostic: the skewness of a distribution may be inferred from the discrepancy.

---

## Measures of Dispersion

### Deviation from the Mean

For observations with mean $\bar{x}$, the deviations are $d_i=x_i-\bar{x}$. They always sum to zero:

$$\sum_{i=1}^{n}(x_i-\bar{x})=0$$

so a meaningful measure of spread must remove the sign. Squaring is the standard choice; absolute value gives the mean absolute deviation $\frac{1}{n}\sum |d_i|$.

### Sample Variance and Standard Deviation

$$s^2=\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2,\qquad s=\sqrt{s^2}$$

Division by $n-1$ rather than $n$ reflects that only $n-1$ of the deviations are independent (the $n$th is determined by the constraint that they sum to zero). The units of $s^2$ are squared units of the data; the units of $s$ are the original units, so $s$ is interpretable as a typical distance from $\bar{x}$.

**Computing (calculator) formula**, useful to avoid accumulated roundoff in hand calculation:

$$s^2=\frac{\sum_{i=1}^{n} x_i^2 - \bigl(\sum_{i=1}^{n} x_i\bigr)^2/n}{n-1}$$

**Coding transformation**: if $x_i=c\,u_i+a$ with $c\ne 0$, then $\bar{x}=c\,\bar{u}+a$ and $s_x=|c|\,s_u$. The shift $a$ affects only the mean; the scaling $|c|$ scales both.

### Range and Interquartile Range

- **Range** $R=\max x_i-\min x_i$. Sensitive to a single extreme observation.
- **Interquartile range** $IQR=Q_3-Q_1$. Insensitive to outliers; preferred for skewed data.

### Coefficient of Variation

$$V=\frac{s}{\bar{x}}\cdot 100\%$$

A scale-free measure of relative variability, used to compare precision between measurements on different scales or in different units. The instrument with smaller $V$ is relatively more precise.

### Summary Table for One-Dimensional Data

| Measure | Symbol | Formula | Resistant? |
|---|---|---|---|
| Mean | $\bar{x}$ | $\sum x_i/n$ | No |
| Median | – | Middle (or two middle) ordered values | Yes |
| Variance | $s^2$ | $\sum(x_i-\bar{x})^2/(n-1)$ | No |
| Standard deviation | $s$ | $\sqrt{s^2}$ | No |
| Range | $R$ | $\max-\min$ | No |
| IQR | – | $Q_3-Q_1$ | Yes |
| Coefficient of variation | $V$ | $s/\bar{x}\cdot 100\%$ | No |
| Mean abs. deviation | – | $\sum|x_i-\bar{x}|/n$ | Somewhat |

---

## Order Statistics, Quantiles, Percentiles, Quartiles

### Order Statistics

Given observations $x_1,\ldots,x_n$, the **order statistics** are the values arranged in non-decreasing order: $x_{(1)}\le x_{(2)}\le\cdots\le x_{(n)}$.

### Sample Percentile

The **sample $100p$th percentile** $P_p$ satisfies: at least $100p\%$ of the observations are at or below it, and at least $100(1-p)\%$ are at or above it. A standard computation rule:

1. Order the $n$ observations.
2. Compute $np$.
3. If $np$ is not an integer, round up to the next integer $k$ and take $P_p=x_{(k)}$.
4. If $np$ is an integer $k$, take $P_p=\tfrac{1}{2}\bigl(x_{(k)}+x_{(k+1)}\bigr)$.

An alternative interpolation-based definition: with $x_{(1)},\ldots,x_{(n)}$ and $i$ satisfying $(i-1)/n<p\le i/n$, set

$$\hat{x}_p = x_{(i-1)} + \frac{np-(i-1)}{1}\bigl(x_{(i)}-x_{(i-1)}\bigr)$$

(linear interpolation on the empirical cdf). For the sample median with even $n$, all conventions give $(x_{(n/2)}+x_{(n/2+1)})/2$.

### Quartiles

The three quartiles divide the ordered data into quarters:

$$Q_1=P_{0.25},\quad Q_2=P_{0.50}=\text{median},\quad Q_3=P_{0.75}$$

### Five-Number Summary and Boxplot Inputs

$$\bigl(\text{minimum},\;Q_1,\;Q_2,\;Q_3,\;\text{maximum}\bigr)$$

For the GDP-per-capita data (2014, all countries): $130,\ 1960,\ 6350,\ 20100,\ 188000$ (dollars). The 0.5-quantile ($6350) is far below the mean ($16{,}500$), reflecting strong right skew; 71% of the data fall below the mean.

### Quantiles for Grouped Data

For grouped data, the median is located by linear interpolation within the median class. If the median falls in the class with boundaries $L$ (lower) and $U$ (upper) containing $j$ values, with $k$ values below, and class width $c$:

$$\text{median}\approx L + \frac{(n/2)-k}{j}\,c$$

The same formula gives $Q_1$ and $Q_3$ by counting $n/4$ and $3n/4$ observations, respectively.

---

## Computing Mean and Variance from Grouped Data

When only the frequency distribution is available, replace every observation in class $i$ by the class mark $m_i$:

$$\bar{x}=\frac{\sum_{i=1}^{k} m_i f_i}{n},\qquad s^2=\frac{\sum_{i=1}^{k} m_i^2 f_i - \bigl(\sum_{i=1}^{k} m_i f_i\bigr)^2/n}{n-1}$$

where $n=\sum f_i$. Because the actual values are replaced by class marks, the result is approximate and ignores within-class variation. For the nanopillar height data the grouped-data mean is 305.0 versus 305.6 from the raw data; grouped-data standard deviation is 39.6 versus 37.0 raw.

---

## The Empirical Cumulative Distribution Function

Under iid sampling from a population with cdf $F_X$, the **empirical cdf** based on data $x_1,\ldots,x_n$ is

$$\hat{F}_n(x)=\frac{1}{n}\sum_{i=1}^{n}\mathbf{1}\{x_i\le x\}$$

The empirical cdf is **unbiased**: $\mathbb{E}\hat{F}_n(x)=F_X(x)$ for every $x$. It is **consistent** in mean square: $\hat{F}_n(x)\to F_X(x)$ as $n\to\infty$. The Glivenko–Cantelli theorem (not detailed here) upgrades this pointwise convergence to uniform convergence on $\mathbb{R}$. Each indicator $\mathbf{1}\{x_i\le x\}$ is Bernoulli with parameter $F_X(x)$, so

$$\mathrm{Var}\bigl(\hat{F}_n(x)\bigr)=\frac{F_X(x)(1-F_X(x))}{n}$$

A continuous version $\tilde{F}_n$ that linearly interpolates between order statistics gives a function that is continuous on $(x_{(1)},\infty)$, right-continuous everywhere, increasing from 0 to 1, and satisfies $\tilde{F}_n(x_{(i)})=i/n$ at each order statistic.

---

## Multivariate Extensions

### Sample Mean (Vector)

For $d$-dimensional data vectors $\vec{x}_1,\ldots,\vec{x}_n$:

$$\mathrm{av}(\vec{x}_1,\ldots,\vec{x}_n)=\frac{1}{n}\sum_{i=1}^{n}\vec{x}_i$$

A data set is **centered** by subtracting the sample mean from each vector, yielding vectors with sample mean zero.

### Sample Covariance and Correlation

For paired data $(x_1,y_1),\ldots,(x_n,y_n)$:

$$\mathrm{cov}\bigl((x_1,y_1),\ldots,(x_n,y_n)\bigr)=\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})$$

The **sample correlation coefficient** is

$$\rho=\frac{\mathrm{cov}\bigl((x_1,y_1),\ldots,(x_n,y_n)\bigr)}{s_x\,s_y}$$

By the Cauchy–Schwarz inequality, $-1\le\rho\le 1$, with $\rho=\pm 1$ iff the centered data are exactly collinear.

### Sample Covariance Matrix

For $d$-dimensional vectors $\vec{x}_1,\ldots,\vec{x}_n$:

$$\hat{\Sigma}=\frac{1}{n-1}\sum_{i=1}^{n}(\vec{x}_i-\mathrm{av})(\vec{x}_i-\mathrm{av})^{\!\top}$$

The $(i,j)$ entry is the sample variance of the $i$th coordinate if $i=j$, and the sample covariance between coordinates $i$ and $j$ otherwise. The matrix is symmetric and positive semidefinite. The sample variance of projections along a unit vector $\vec{v}$ is $\vec{v}^{\!\top}\hat{\Sigma}\,\vec{v}$.

### Principal Component Analysis (PCA)

Let $\hat{\Sigma}=U\Lambda U^{\!\top}$ be the eigendecomposition with eigenvalues ordered $\lambda_1\ge\lambda_2\ge\cdots\ge\lambda_d$. The columns of $U$ are the **principal directions** $\vec{u}_1,\ldots,\vec{u}_d$. The optimality theorem:

$$\lambda_1=\max_{\|\vec{v}\|=1}\mathrm{var}(\vec{v}^{\!\top}\vec{x}_1,\ldots,\vec{v}^{\!\top}\vec{x}_n),\quad \vec{u}_1=\arg\max_{\|\vec{v}\|=1}\mathrm{var}(\vec{v}^{\!\top}\vec{x}_1,\ldots)$$

$$\lambda_k=\max_{\|\vec{v}\|=1,\ \vec{v}\perp\vec{u}_1,\ldots,\vec{u}_{k-1}}\mathrm{var}(\vec{v}^{\!\top}\vec{x}_1,\ldots)$$

Thus $\vec{u}_1$ is the direction of greatest variation, $\vec{u}_2$ the orthogonal direction of next greatest variation, and so on. PCA requires centered data, otherwise the first principal direction aligns with the mean rather than the axis of greatest spread.

**Whitening** is the preprocessing transformation that converts the data to a sample covariance matrix equal to the identity. With $\hat{\Sigma}=U\Lambda U^{\!\top}$:

$$\vec{y}_i=\Lambda^{-1/2}U^{\!\top}\vec{x}_i,\qquad \hat{\Sigma}(\vec{y}_1,\ldots,\vec{y}_n)=I_d$$

This rotates to align with eigenvectors and then rescales so all directions have equal variation, revealing nonlinear structure obscured by linear skew.

---

## Probability Foundation: From Data to Inference

When data $x_1,\ldots,x_n$ are modeled as realizations of iid random variables $X_1,\ldots,X_n$ with common cdf $F_X$, the descriptive statistics become **estimators** of corresponding population quantities. The **population relative frequency function** is $f_X(x)=\#\{i:X_i=x\}/N$ for a finite population, and for a continuous setting the **density** $f_X$ plays the same role.

### Population vs Sample Quantities

| Population quantity | Definition | Sample estimator |
|---|---|---|
| Mean $\mu$ | $\mathbb{E}[X]$ | $\bar{x}=\tfrac{1}{n}\sum x_i$ |
| Variance $\sigma^2$ | $\mathbb{E}[(X-\mu)^2]$ | $s^2=\tfrac{1}{n-1}\sum(x_i-\bar{x})^2$ |
| cdf at $x$ | $F_X(x)$ | $\hat{F}_n(x)$ |
| $p$th quantile | $F_X^{-1}(p)$ | Sample $p$th quantile |
| Proportion $f_X(c)$ | $P(X=c)$ | Empirical proportion |
| Coefficient of variation | $\sigma/\mu$ | $s/\bar{x}$ |

### Estimator Properties

For an estimator $Y=h(X_1,\ldots,X_n)$ of a fixed quantity $\gamma$:

- **Bias**: $\mathrm{Bias}(Y)=\mathbb{E}[Y]-\gamma$. $Y$ is **unbiased** if $\mathbb{E}[Y]=\gamma$.
- **Mean square error (MSE)**: $\mathrm{MSE}(Y)=\mathbb{E}[(Y-\gamma)^2]$.
- **Bias–variance decomposition**: $\mathrm{MSE}(Y)=\mathrm{Var}(Y)+\mathrm{Bias}(Y)^2$.
- **Consistency**: $Y^{(n)}\to\gamma$ in mean square, with probability one, or in probability as $n\to\infty$.

The sample mean is unbiased:

$$\mathbb{E}[\bar{X}]=\frac{1}{n}\sum_{i=1}^{n}\mathbb{E}[X_i]=\mu$$

The sample variance is unbiased:

$$\mathbb{E}[s^2]=\frac{1}{n-1}\sum_{i=1}^{n}\mathbb{E}[(X_i-\bar{X})^2]=\sigma^2$$

The sample mean is **consistent** as long as $\sigma^2<\infty$ (law of large numbers). The sample median is also consistent and remains so even when the mean does not exist (e.g., for Cauchy data, where the moving average diverges but the moving median converges). The sample variance and sample covariance are consistent under bounded higher-moment conditions.

### Mean Square Error of the Sample Mean

For the sample mean of an iid sequence with mean $\mu$ and variance $\sigma^2$:

$$\mathrm{MSE}(\bar{X})=\mathrm{Var}(\bar{X})+\mathrm{Bias}(\bar{X})^2=\frac{\sigma^2}{n}+0=\frac{\sigma^2}{n}$$

### Confidence Intervals for the Mean

A **$1-\alpha$ confidence interval** $I$ for $\gamma$ satisfies $P(\gamma\in I)\ge 1-\alpha$. For the mean $\mu$ of an iid sequence:

**Chebyshev-based interval**: if $\sigma^2\le b^2$, then for any $0<\alpha<1$:

$$I_n=\Bigl[\bar{X}_n-b\sqrt{\alpha/n},\ \bar{X}_n+b\sqrt{\alpha/n}\Bigr]$$

is a $1-\alpha$ confidence interval, by Chebyshev's inequality. The width is $2b\sqrt{\alpha/n}$; this interval is distribution-free but typically conservative.

**CLT-based interval** (approximate, valid for large $n$): by the central limit theorem with sample standard deviation substituted for the unknown $\sigma$,

$$I_n=\Bigl[\bar{X}_n-\frac{S_n}{\sqrt{n}}Q^{-1}(\alpha/2),\ \bar{X}_n+\frac{S_n}{\sqrt{n}}Q^{-1}(\alpha/2)\Bigr]$$

is an approximate $1-\alpha$ confidence interval, where $Q(x)=\int_x^{\infty}\frac{1}{\sqrt{2\pi}}e^{-u^2/2}\,du$ is the Gaussian tail function. Common values: $Q^{-1}(0.025)\approx 1.96$, $Q^{-1}(0.05)\approx 1.645$.

**Frequentist interpretation of $I_n$**: the *coverage* statement $P(\mu\in I_n)\ge 1-\alpha$ refers to the random interval over hypothetical repetitions of the data-acquisition process. For any single realized interval, $\mu$ is either inside it or not; the probability interpretation is about the procedure, not the realized set.

---

## Issues and Pitfalls in Descriptive Statistics

**Aggregating dissimilar data** can mask differences. For circuit-board defects: aggregating Products A, B, C gives 2.0 defects/board, but separately the rates are 1.51, 5.78, 0.30, requiring very different responses. Always stratify by known groupings before summarizing.

**Time order matters**. Summarizing by a five-number summary can erase a trend; a time plot of a defect series revealed that the average was appropriate but individual values followed a systematic drift.

**Outliers in boxplots**. Tukey's modified boxplot caps the whisker at $Q_3+1.5\,\mathrm{IQR}$ and $Q_1-1.5\,\mathrm{IQR}$; values beyond are plotted individually. Their existence and possible causes (data error vs heavy-tailed distribution) should be investigated.

**Mean vs median sensitivity**. Replacing the maximum from 50 to 5000 leaves the median at 1.5 but moves the mean from 1.73 to 51.23. Report both for skewed data.

**The influence of a single outlier** is greater on $\bar{x}$ and $s$ than on the median and IQR; it is greater on the range than on the IQR. A single replacement can change $\bar{x}$ and $s$ by an arbitrary amount.

**Misleading histograms**: plotting frequencies with unequal class widths (without rescaling to densities) misrepresents the distribution. Plot a density histogram in that case.

**Pictograms**: scaling one dimension of an icon while leaving the other fixed can exaggerate apparent differences. Use proportional symbols or stick to bar charts.

---

## Key Formulas (Compact Reference)

| Quantity | Formula |
|---|---|
| Sample mean | $\bar{x}=\sum x_i/n$ |
| Sample variance | $s^2=\sum(x_i-\bar{x})^2/(n-1)$ |
| Sample standard deviation | $s=\sqrt{s^2}$ |
| Sample median (odd $n$) | $x_{((n+1)/2)}$ |
| Sample median (even $n$) | $\frac{1}{2}(x_{(n/2)}+x_{(n/2+1)})$ |
| Sample percentile (rule) | See algorithm above |
| Range | $R=\max-\min$ |
| IQR | $Q_3-Q_1$ |
| Coefficient of variation | $V=s/\bar{x}\cdot 100\%$ |
| Empirical cdf | $\hat{F}_n(x)=\frac{1}{n}\sum\mathbf{1}\{x_i\le x\}$ |
| Sample covariance | $\mathrm{cov}=\frac{1}{n-1}\sum(x_i-\bar{x})(y_i-\bar{y})$ |
| Sample correlation | $\rho=\mathrm{cov}/(s_x s_y)$ |
| Sample covariance matrix | $\hat{\Sigma}=\frac{1}{n-1}\sum(\vec{x}_i-\bar{\vec{x}})(\vec{x}_i-\bar{\vec{x}})^{\!\top}$ |
| Variance of projection on $\vec{v}$ | $\vec{v}^{\!\top}\hat{\Sigma}\vec{v}$ |
| Whitening transform | $\vec{y}_i=\Lambda^{-1/2}U^{\!\top}\vec{x}_i$ |
| Bias–variance decomposition | $\mathrm{MSE}=\mathrm{Var}+\mathrm{Bias}^2$ |
| $\mathrm{Var}(\bar{X})$ for iid | $\sigma^2/n$ |
| Chebyshev CI half-width | $b\sqrt{\alpha/n}$ |
| CLT CI half-width | $s\,Q^{-1}(\alpha/2)/\sqrt{n}$ |

---

Descriptive statistics is the disciplined summarization of data: from raw observations, we form graphical displays (dot diagrams, histograms, stem-and-leaf, ogives, Pareto diagrams, boxplots) to expose shape, and we compute numerical measures (mean, median, variance, standard deviation, range, IQR, quantiles, percentiles) to summarize location and spread. The empirical cdf generalizes the data to a step function that estimates the population cdf pointwise and uniformly. Multivariate descriptive methods—sample covariance, sample correlation, sample covariance matrix, PCA, and whitening—extend the same ideas to several features at once. When the data are modeled as iid realizations of a random variable, these sample quantities are unbiased and consistent estimators of their population counterparts, and they form the building blocks of formal inference through confidence intervals and beyond.
