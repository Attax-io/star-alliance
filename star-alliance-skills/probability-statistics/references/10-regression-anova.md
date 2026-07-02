---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Relationships Among Variables: Regression, Correlation, ANOVA, and Experimental Design

This reference covers the statistical methods for studying relationships between variables, from the foundational concepts of causation and experimental design through simple and multiple linear regression, correlation analysis, the full family of analysis of variance techniques (one-way, randomized blocks, two-factor, multifactor, factorial designs), analysis of covariance, and logistic regression for binary responses. Both the classical (frequentist) and Bayesian perspectives are included, and the material integrates rigorous derivations, computational formulas, practical implementation notes, and diagnostic procedures for model checking.

## 1. Foundations: Variables, Causation, and Design of Experiments

### 1.1 Related Variables

Two variables X and Y are **related** if the conditional distribution of one given the other changes as the value of the conditioning variable changes. Formally, X and Y are related if and only if there exist values x₁, x₂ such that f_{Y|X}(·|x₁) ≠ f_{Y|X}(·|x₂). For discrete variables, this is equivalent to independence. For continuous variables, related does not always equal uncorrelated (zero correlation).

### 1.2 Confounding and Lurking Variables

A **confounding variable** Z is a third variable that influences both X and Y, making the observed X–Y relationship ambiguous. A **lurking variable** is a hidden confounder. Conditioning on Z (i.e., examining f_{Y|X,Z}) can rescue causal interpretation, but in practice we never condition on all possible confounders.

**Example.** GPA differences observed between male and female students may be confounded with part-time work status; if most female students hold part-time jobs and most male students do not, the GPA–gender relationship may actually be a GPA–work relationship.

### 1.3 Hierarchy of Studies

Studies form a hierarchy of inferential strength:
1. **Observational studies** (bottom): subject to both selection effects and confounding; no causal claims possible.
2. **Sampling studies** (middle): random sample eliminates selection effects, but confounding may remain.
3. **Experiments** (top): random sample + researcher assigns values of X to units + random allocation of treatments → causal claims possible.

### 1.4 Conditions for Cause–Effect Inference

To support a cause–effect claim about X and Y:
1. Random sample from the target population.
2. Researcher must be able to assign any value of X to any sampled unit.
3. Random allocation of X-values to units.

When all three are met, the data come from an **experiment** and causal claims are warranted.

### 1.5 Design Concepts

| Term | Definition |
|------|------------|
| Experimental unit | The entity to which a treatment is applied |
| Factor | A predictor variable under experimental control |
| Level | A specific value of a factor |
| Treatment | A specific combination of factor levels applied to a unit |
| Replication | Independent repetition of the same treatment |
| Balance | Equal sample size nᵢ at each level |
| Control treatment | A baseline level (e.g., zero dose) for comparison |
| Blocking variable | A nuisance variable whose levels are held fixed within blocks but vary between blocks |
| Confounded | Two effects cannot be statistically separated |
| Blinding | Subjects unaware of treatment identity; **double-blind** means experimenters are also unaware |
| Placebo effect | Improvement in subjects receiving any treatment, including inert ones |
| Lurking variable | An uncontrolled confounder |

### 1.6 Interactions

When two predictors X and W are involved, the conditional distribution f_{Y|X,W} may change with X in different ways depending on W. When this happens, X and W **interact**. The design in which every X-level is paired with every W-level is called **completely crossed**.

---

## 2. Simple Linear Regression

### 2.1 Model and Assumptions

**Statistical model:**
$$Y_i = \alpha + \beta x_i + \varepsilon_i, \quad i=1,\ldots,n$$

where the εᵢ are independent, normally distributed with mean 0 and common variance σ². The xᵢ are fixed (non-random) and known without error.

**Decomposition:** yᵢ = ŷᵢ + eᵢ, where ŷᵢ = ˆα + ˆβxᵢ and eᵢ = yᵢ − ŷᵢ are **residuals**.

### 2.2 Sums of Squares

$$S_{xx} = \sum_{i=1}^n (x_i - \bar{x})^2 = \sum x_i^2 - \frac{(\sum x_i)^2}{n}$$

$$S_{yy} = \sum_{i=1}^n (y_i - \bar{y})^2 = \sum y_i^2 - \frac{(\sum y_i)^2}{n}$$

$$S_{xy} = \sum_{i=1}^n (x_i - \bar{x})(y_i - \bar{y}) = \sum x_i y_i - \frac{(\sum x_i)(\sum y_i)}{n}$$

The first forms are preferred for accuracy; the second are convenient for calculators.

### 2.3 Least Squares Estimates

Choose ˆα, ˆβ to minimize S(a,b) = Σ[yᵢ − (a + bxᵢ)]².

$$\hat{\beta} = \frac{S_{xy}}{S_{xx}}, \qquad \hat{\alpha} = \bar{y} - \hat{\beta}\bar{x}$$

**Fitted regression line:** ŷ = ˆα + ˆβx.

**Gauss–Markov theorem:** Among all unbiased estimators of α and β that are linear in the Yᵢ, the least-squares estimators have minimum variance.

### 2.4 Residual Sum of Squares

$$SSE = \sum_{i=1}^n (y_i - \hat{\alpha} - \hat{\beta} x_i)^2 = S_{yy} - \frac{S_{xy}^2}{S_{xx}}$$

**Estimate of σ²:**
$$s_e^2 = \frac{SSE}{n-2}, \qquad s_e = \sqrt{s_e^2}$$

The standard error sₑ has n − 2 degrees of freedom. The "loss" of 2 df reflects estimation of α and β.

### 2.5 Normal Equations

Setting partial derivatives of S(a,b) to zero yields:

$$\sum y_i = n a + b \sum x_i$$
$$\sum x_i y_i = a \sum x_i + b \sum x_i^2$$

Equivalent to: the least-squares line passes through (x̄, ȳ) and minimizes Σ residuals².

### 2.6 Sampling Distributions

**Theorem 2.1 (Inference about β):** Under the model assumptions,
$$T = \frac{\hat{\beta} - \beta}{s_e / \sqrt{S_{xx}}} \sim t_{n-2}$$

**Theorem 2.2 (Inference about α):**
$$T = \frac{\hat{\alpha} - \alpha}{s_e \sqrt{\frac{1}{n} + \frac{\bar{x}^2}{S_{xx}}}} \sim t_{n-2}$$

### 2.7 Confidence Intervals

**Slope β:** $\hat{\beta} \pm t_{\alpha/2, n-2} \cdot \dfrac{s_e}{\sqrt{S_{xx}}}$

**Intercept α:** $\hat{\alpha} \pm t_{\alpha/2, n-2} \cdot s_e \sqrt{\dfrac{1}{n} + \dfrac{\bar{x}^2}{S_{xx}}}$

**Mean response at x₀ (α + βx₀):**
$$\hat{\alpha} + \hat{\beta} x_0 \pm t_{\alpha/2, n-2} \cdot s_e \sqrt{\frac{1}{n} + \frac{(x_0 - \bar{x})^2}{S_{xx}}}$$

**Prediction interval for a future Y at x₀:**
$$\hat{\alpha} + \hat{\beta} x_0 \pm t_{\alpha/2, n-2} \cdot s_e \sqrt{1 + \frac{1}{n} + \frac{(x_0 - \bar{x})^2}{S_{xx}}}$$

The width of the prediction interval does not shrink to zero as n → ∞; it depends on sₑ. Extrapolation (x₀ far from x̄) widens both intervals.

### 2.8 Test of Significance for the Slope

Hypotheses: H₀: β = 0 versus H₁: β ≠ 0 (or one-sided alternatives). Test statistic:
$$t = \frac{\hat{\beta}}{s_e / \sqrt{S_{xx}}}$$
Reject H₀ when |t| > t_{α/2, n−2}. The test is equivalent to the ANOVA F-test (F = t²).

### 2.9 Coefficient of Determination and Decomposition of Variability

**Total sum of squares:** $S_{yy} = \dfrac{S_{xy}^2}{S_{xx}} + SSE$

**R² (coefficient of determination):**
$$R^2 = \frac{\text{Regression SS}}{\text{Total SS}} = \frac{S_{xy}^2/S_{xx}}{S_{yy}} = r^2$$

R² is the proportion of y-variability explained by the linear relation; 0 ≤ R² ≤ 1.

### 2.10 Model Diagnostics

Compute residuals eᵢ = yᵢ − ŷᵢ. Plot:
- **Residuals vs. predicted values ŷᵢ**: detects non-constant variance (fan shape) and model inadequacy (systematic pattern).
- **Residuals vs. x**: detects nonlinearity and lurking variables.
- **Residuals vs. time/order**: detects temporal trends and autocorrelation.
- **Normal-scores (Q-Q) plot of residuals**: checks normality assumption; serious outliers are critical.

If diagnostics fail, consider transformations of Y (log, reciprocal, power) or X (polynomial).

### 2.11 Regression Through the Origin (No Intercept)

When the model is y = βx, the least-squares estimate is:
$$\hat{\beta} = \frac{\sum x_i y_i}{\sum x_i^2}$$

---

## 3. Multiple Linear Regression

### 3.1 Model

$$Y_i = \beta_0 + \beta_1 x_{i1} + \cdots + \beta_k x_{ik} + \varepsilon_i$$

In matrix form: **Y** = **Xβ** + **ε**, with ε ∼ N(**0**, σ²**I**).

### 3.2 Design Matrix

$$\mathbf{X} = \begin{pmatrix} 1 & x_{11} & \cdots & x_{1k} \\ 1 & x_{21} & \cdots & x_{2k} \\ \vdots & \vdots & \ddots & \vdots \\ 1 & x_{n1} & \cdots & x_{nk} \end{pmatrix}$$

The first column of 1's accommodates the intercept β₀.

### 3.3 Least-Squares Solution

Minimize (y − **Xβ**)′(y − **Xβ**):

$$\hat{\boldsymbol{\beta}} = (\mathbf{X}'\mathbf{X})^{-1}\mathbf{X}'\mathbf{y}$$

provided (**X**′**X**) is nonsingular. The fitted values are **ŷ** = **X̂β** and residuals are **e** = **y** − **ŷ**.

### 3.4 Normal Equations

Setting ∂SSE/∂β = 0 gives the system **X**′**X̂β** = **X**′**y**.

For two predictors (r = 2):
$$\sum y = nb_0 + b_1 \sum x_1 + b_2 \sum x_2$$
$$\sum x_1 y = b_0 \sum x_1 + b_1 \sum x_1^2 + b_2 \sum x_1 x_2$$
$$\sum x_2 y = b_0 \sum x_2 + b_1 \sum x_1 x_2 + b_2 \sum x_2^2$$

### 3.5 Estimation of σ²

$$s_e^2 = \frac{SSE}{n - k - 1} = \frac{(\mathbf{y} - \mathbf{X}\hat{\boldsymbol{\beta}})'(\mathbf{y} - \mathbf{X}\hat{\boldsymbol{\beta}})}{n - k - 1}$$

The variance/covariance matrix of β̂:
$$\widehat{\text{Cov}}(\hat{\boldsymbol{\beta}}) = s_e^2 (\mathbf{X}'\mathbf{X})^{-1}$$

The diagonal entries give Var(β̂ᵢ); the off-diagonals give covariances.

### 3.6 Inferences

Under normality:
- $\hat{\beta}_i \sim N(\beta_i, \sigma^2 c_{ii})$ where cᵢᵢ is the (i,i) entry of (X′X)⁻¹.
- $\dfrac{\hat{\beta}_i - \beta_i}{s_e \sqrt{c_{ii}}} \sim t_{n-k-1}$

**Confidence interval for βᵢ:** $\hat{\beta}_i \pm t_{\alpha/2, n-k-1} \cdot s_e \sqrt{c_{ii}}$

**Confidence interval for mean response** at x = (1, x₁, …, xₖ)′:
$$\hat{\boldsymbol{\beta}}'\mathbf{x} \pm t_{\alpha/2, n-k-1} \cdot s_e \sqrt{\mathbf{x}'(\mathbf{X}'\mathbf{X})^{-1}\mathbf{x}}$$

### 3.7 Categorical Variables via Dummy Coding

For a categorical predictor with a levels, create a − 1 dummy variables:
- Set xᵢⱼ = 1 if unit is in level j, 0 otherwise.
- For 2 levels, one dummy suffices.
- For 3 levels, two dummies are needed; the third level is the reference.
- The coefficient of a dummy estimates the difference in mean response between that level and the reference.

### 3.8 Polynomial Regression

For E[Y|x] = β₀ + β₁x + β₂x² + … + βₚxᵖ, treat x, x², …, xᵖ as separate predictors in multiple regression. Normal equations become a (p+1)×(p+1) linear system. Higher-degree polynomials increase the danger of extrapolation.

### 3.9 Standardized Residuals (Multiple Regression)

$$e_i^* = \frac{y_i - \hat{y}_i}{s_e \sqrt{1 - d_{ii}}}$$

where dᵢᵢ is the (i,i) entry of the hat matrix **H** = **X**(**X**′**X**)⁻¹**X**′. Approximately N(0,1) under the model.

---

## 4. Correlation

### 4.1 Sample Correlation Coefficient

$$r = \frac{S_{xy}}{\sqrt{S_{xx} \cdot S_{yy}}}$$

Equivalently: r = 1/(n−1) · Σ[(xᵢ − x̄)/sₓ · (yᵢ − ȳ)/s_y]. Range: −1 ≤ r ≤ 1.

- |r| = 1: all points lie exactly on a line.
- r > 0: positive linear association (lower-left to upper-right).
- r < 0: negative linear association (upper-left to lower-right).
- r near 0: weak linear association; **nonlinear** relationships can still exist.

### 4.2 Relationship to Regression

$$r = \frac{S_{xy}}{\sqrt{S_{xx} S_{yy}}} = \hat{\beta} \sqrt{\frac{S_{xx}}{S_{yy}}}$$

So r and β̂ have the same sign. The proportion of y-variability explained by the regression line is r².

### 4.3 Population Correlation Coefficient

$$\rho = E\left[\left(\frac{X-\mu_1}{\sigma_1}\right)\left(\frac{Y-\mu_2}{\sigma_2}\right)\right] = \frac{\text{Cov}(X,Y)}{\sigma_1 \sigma_2}$$

### 4.4 Fisher Z-Transformation

For inference on ρ from a bivariate normal population:
$$Z = \frac{1}{2}\ln\frac{1+r}{1-r}$$

is approximately N(μ_Z, 1/(n−3)), where μ_Z = ½ ln[(1+ρ)/(1−ρ)].

**Test H₀: ρ = ρ₀:**
$$z = \sqrt{n-3}\left[\frac{1}{2}\ln\frac{1+r}{1-r} - \frac{1}{2}\ln\frac{1+\rho_0}{1-\rho_0}\right] \stackrel{\text{approx}}{\sim} N(0,1)$$

**Confidence interval for ρ:**
1. Convert r to Z, form CI for μ_Z: $Z \pm z_{\alpha/2}/\sqrt{n-3}$.
2. Convert back using r = (e^Z − e^{−Z})/(e^Z + e^{−Z}).

**Test H₀: ρ = 0:** z = √(n−3) · ½ ln[(1+r)/(1−r)] ~ N(0,1) approximately.

### 4.5 Bivariate Normal Distribution

$$f(x,y) = \frac{1}{2\pi\sigma_1\sigma_2\sqrt{1-\rho^2}} \exp\left\{-\frac{1}{2(1-\rho^2)}\left[\left(\frac{x-\mu_1}{\sigma_1}\right)^2 - 2\rho\frac{(x-\mu_1)(y-\mu_2)}{\sigma_1\sigma_2} + \left(\frac{y-\mu_2}{\sigma_2}\right)^2\right]\right\}$$

Properties: ρ = 0 if and only if X and Y are independent. ρ = ±1 corresponds to a perfect linear relationship.

### 4.6 Multiple Correlation Coefficient

In multiple regression, R² is the square of the multiple correlation, the simple correlation between observed y and predicted ŷ. Range: 0 ≤ R ≤ 1.

---

## 5. Curvilinear Regression

### 5.1 Strategy

When the relationship between Y and x is nonlinear:
1. **Transform** to linearize (exponential, reciprocal, power).
2. **Polynomial regression** in x.

Then apply least squares to the transformed/polynomial model.

### 5.2 Common Transformations

| Original form | Transformation | Linearized form |
|---------------|----------------|-----------------|
| y = α · βˣ | log y vs. x | log y = log α + (log β) x |
| y = α · xᵝ | log y vs. log x | log y = log α + β log x |
| y = 1/(α + βx) | 1/y vs. x | 1/y = α + βx |
| y = exp(α + βx) | ln y vs. x | ln y = α + βx |

Apply least squares to the transformed variables, then back-transform estimates. Be cautious: back-transformation is for the mean of log y, not log of mean y (Jensen's inequality).

### 5.3 Polynomial Regression

For degree p: minimize Σ[yᵢ − (β₀ + β₁xᵢ + … + βₚxᵢᵖ)]². Normal equations are a (p+1)×(p+1) linear system. Choose p by sequential F-tests or by examining residual patterns; never choose p ≥ n−1 (interpolates data exactly).

### 5.4 Gompertz, Logistic, and Other Curves

Curves of the form y = exp(α + βx) (Gompertz) or y = 1/(1 + exp(−(α+βx))) (logistic) can be fit by transforming to linearity.

---

## 6. One-Way Analysis of Variance (Completely Randomized Design)

### 6.1 Model

k independent samples from populations with means μ₁, …, μₖ and common variance σ²:
$$Y_{ij} = \mu + \alpha_i + \varepsilon_{ij}, \quad i=1,\ldots,k;\ j=1,\ldots,n_i$$

where Σαᵢ = 0 (with weights nᵢ) and εᵢⱼ ~ N(0, σ²) independently.

### 6.2 Null Hypothesis

H₀: α₁ = α₂ = … = αₖ = 0 (all means equal).
H₁: at least one αᵢ ≠ 0.

### 6.3 Notation

- N = Σnᵢ (total sample size)
- ȳᵢ = sample mean for treatment i
- ȳ = grand mean = Σnᵢȳᵢ / N
- Tᵢ = Σ yᵢⱼ (treatment total); T· = ΣTᵢ (grand total)
- C = T·²/N (correction term for the mean)

### 6.4 Sums of Squares

**Total sum of squares:**
$$SST = \sum_{i,j} y_{ij}^2 - C = \sum_{i,j} (y_{ij} - \bar{y})^2$$

**Treatment sum of squares (between-samples):**
$$SS(\text{Tr}) = \sum_i \frac{T_i^2}{n_i} - C = \sum_i n_i (\bar{y}_i - \bar{y})^2$$

**Error sum of squares (within-samples):**
$$SSE = SST - SS(\text{Tr}) = \sum_{i,j} (y_{ij} - \bar{y}_i)^2$$

### 6.5 Degrees of Freedom

| Source | df |
|--------|-----|
| Treatments | k − 1 |
| Error | N − k |
| Total | N − 1 |

### 6.6 ANOVA Table

| Source | df | SS | MS | F |
|--------|----|----|-----|---|
| Treatments | k−1 | SS(Tr) | MS(Tr) = SS(Tr)/(k−1) | MS(Tr)/MSE |
| Error | N−k | SSE | MSE = SSE/(N−k) | |
| Total | N−1 | SST | | |

**F statistic:** F = MS(Tr)/MSE ~ F_{k−1, N−k} under H₀. Reject H₀ when F > F_{α, k−1, N−k}.

### 6.7 Estimates

- ˆμ = ȳ
- ˆαᵢ = ȳᵢ − ȳ
- ˆμᵢ = ȳᵢ

### 6.8 Confidence Intervals for Differences of Means

For μᵢ − μₗ:
$$\bar{y}_i - \bar{y}_\ell \pm t_{\alpha/2, N-k} \cdot s_e\sqrt{\frac{1}{n_i} + \frac{1}{n_\ell}}$$

where sₑ = √MSE.

### 6.9 Robustness

ANOVA F-test is fairly robust to mild violations of normality and equal variance assumptions, especially for balanced designs and moderate sample sizes.

### 6.10 One-Way ANOVA Equals Two-Sample t-Test

When k = 2, F(1, ν) = t²(ν), so the ANOVA F-test is algebraically identical to the two-sample t-test.

---

## 7. Randomized Block Designs

### 7.1 Setup

a treatments, b blocks, one observation per cell. The block is a nuisance variable (e.g., day, machine, plot) held constant within each block.

**Model:** Yᵢⱼ = μ + αᵢ + βⱼ + εᵢⱼ with Σαᵢ = Σβⱼ = 0, εᵢⱼ ~ N(0, σ²) independent.

### 7.2 Sums of Squares

Let yᵢ· = row (treatment) mean, y·ⱼ = column (block) mean, y·· = grand mean.

**Treatment SS:** $SS(\text{Tr}) = b \sum_i (y_{i\cdot} - y_{\cdot\cdot})^2$

**Block SS:** $SS(\text{Bl}) = a \sum_j (y_{\cdot j} - y_{\cdot\cdot})^2$

**Error SS:** $SSE = \sum_{i,j}(y_{ij} - y_{i\cdot} - y_{\cdot j} + y_{\cdot\cdot})^2 = SST - SS(\text{Tr}) - SS(\text{Bl})$

### 7.3 Degrees of Freedom

| Source | df |
|--------|-----|
| Treatments | a − 1 |
| Blocks | b − 1 |
| Error | (a−1)(b−1) |
| Total | ab − 1 |

### 7.4 ANOVA Table and F-Tests

| Source | df | SS | MS | F |
|--------|----|----|-----|---|
| Treatments | a−1 | SS(Tr) | MS(Tr) | MS(Tr)/MSE |
| Blocks | b−1 | SS(Bl) | MS(Bl) | MS(Bl)/MSE |
| Error | (a−1)(b−1) | SSE | MSE | |
| Total | ab−1 | SST | | |

Reject H₀: α₁ = … = αₐ if F > F_{α, a−1, (a−1)(b−1)}.

**Why block?** Blocking reduces error variance by removing variability due to βⱼ, increasing the power to detect treatment effects. Only worthwhile if block effect is large.

### 7.5 Alternative Formulas

Let Tᵢ· = Σⱼ yᵢⱼ (row total), T·ⱼ = Σᵢ yᵢⱼ (column total), T·· = Σᵢⱼ yᵢⱼ.
- C = T··²/(ab)
- SST = Σyᵢⱼ² − C
- SS(Tr) = Σ Tᵢ·²/b − C
- SS(Bl) = Σ T·ⱼ²/a − C
- SSE = SST − SS(Tr) − SS(Bl)

### 7.6 Repeated Measures / Paired Comparisons

When each subject (block) provides measurements under k conditions, the paired t-test or repeated-measures ANOVA applies. For k = 2: use paired t on differences dᵢ = yᵢ₁ − yᵢ₂. Var(d) incorporates positive correlation: Var(Y₁−Y₂) = Var(Y₁) + Var(Y₂) − 2Cov(Y₁,Y₂), which is smaller than the independent-sample variance.

**Assumption:** Differences are approximately normal.

---

## 8. Two-Factor and Multifactor Experiments

### 8.1 Two-Factor Model

**Model with interaction:**
$$Y_{ijk} = \mu + \alpha_i + \beta_j + (\alpha\beta)_{ij} + \varepsilon_{ijk}$$

where i = 1,…,a; j = 1,…,b; k = 1,…,r (replicates). Restrictions: Σαᵢ = 0, Σβⱼ = 0, Σᵢ(αβ)ᵢⱼ = 0 for each j, Σⱼ(αβ)ᵢⱼ = 0 for each i.

### 8.2 Sums of Squares

- SSA = br Σᵢ(yᵢ·· − y···)² with a − 1 df
- SSB = ar Σⱼ(y·ⱼ· − y···)² with b − 1 df
- SS(AB) = r Σᵢⱼ(yᵢⱼ· − yᵢ·· − y·ⱼ· + y···)² with (a−1)(b−1) df
- SSE = Σᵢⱼₖ(yᵢⱼₖ − yᵢⱼ·)² with ab(r−1) df
- SST = Σᵢⱼₖ(yᵢⱼₖ − y···)² with abr − 1 df

Identity: SST = SSA + SSB + SS(AB) + SSE.

### 8.3 ANOVA Table for Two-Factor Design

| Source | df | MS | F |
|--------|----|----|---|
| Factor A | a−1 | MSA | MSA/MSE |
| Factor B | b−1 | MSB | MSB/MSE |
| A×B interaction | (a−1)(b−1) | MS(AB) | MS(AB)/MSE |
| Error | ab(r−1) | MSE | |
| Total | abr−1 | | |

### 8.4 Testing Strategy

1. **Test interaction first**: H₀: all (αβ)ᵢⱼ = 0. If significant, main effects cannot be interpreted in isolation; report the two-way table of cell means.
2. If no significant interaction, test main effects H₀: αᵢ = 0 and H₀: βⱼ = 0 separately.

### 8.5 Effect of Ignoring Interaction

If interaction exists but is ignored, F-tests for main effects lose power and may mislead. Always inspect the interaction plot (means plotted against one factor's levels for each level of the other).

### 8.6 Three-Factor Model

Extends to αᵢ, βⱼ, γₖ, (αβ)ᵢⱼ, (αγ)ᵢₖ, (βγ)ⱼₖ, (αβγ)ᵢⱼₖ. Interaction (αβγ) has (a−1)(b−1)(c−1) df. Test three-factor interaction first; if non-significant, drop and proceed.

### 8.7 Multifactor (Factorial) Designs

A **complete factorial design** runs all a·b·c… combinations. Advantages: efficient, allows estimation of interactions. df: total = N−1, factor A = a−1, factor B = b−1, etc., two-way interactions = product of df, three-way = product, etc., error = N − (number of parameters).

---

## 9. Analysis of Covariance (ANCOVA)

### 9.1 Purpose

Combine regression and ANOVA to adjust treatment comparisons for a quantitative **covariate** x whose values cannot be held constant but can be measured.

### 9.2 Model

$$Y_{ij} = \mu + \alpha_i + \beta x_{ij} + \varepsilon_{ij}, \quad i=1,\ldots,k;\ j=1,\ldots,n$$

with Σαᵢ = 0 and εᵢⱼ ~ N(0, σ²) independent. Common slope β across all treatments; expected response lines are **parallel** in x.

### 9.3 Sums of Squares Error

Three nested models:
- **Full model:** SSE_{Tr,x} = Σ(yᵢⱼ − ŷᵢⱼ)² with nk − k − 1 df
- **Treatment only:** SSE_{Tr} = one-way ANOVA error = nk − k df
- **Regression only:** SSE_x = regression error with nk − 2 df

Decomposition:
$$SSE_{Tr} = SSE_{x} + SS(\text{Tr} | x), \quad \text{df: } nk-k = (nk-2) + (k-1)$$
$$SSE_{Tr} = SSE_{Tr,x} + SS(x | \text{Tr}), \quad \text{df: } nk-k = (nk-k-1) + 1$$

So:
- SS(Tr | x) = SSE_x − SSE_{Tr,x} with k − 1 df
- SS(x | Tr) = SSE_{Tr} − SSE_{Tr,x} with 1 df

### 9.4 F-Tests

- **Treatment effect adjusted for x:** F = MS(Tr|x)/MSE_{full} ~ F_{k−1, nk−k−1}
- **Slope effect adjusted for treatment:** F = MS(x|Tr)/MSE_{full} ~ F_{1, nk−k−1}

### 9.5 Practical Note

The covariate must be measured before treatment (or unaffected by it) for valid inference. The parallel-slopes assumption can be checked by testing treatment × covariate interaction; if violated, fit separate slopes per treatment.

---

## 10. Factorial Designs: 2² and 2³

### 10.1 Why Vary Factors Simultaneously

Changing one factor at a time can produce a **false location** for an optimum (e.g., ridge in the response surface missed). Factorial designs with all combinations of factor levels reveal interactions and locate optima efficiently.

### 10.2 The 2² Design

Two factors, each at two coded levels: −1 (low) and +1 (high). The four runs form a square.

| Run | x₁ | x₂ | Mean response |
|-----|----|----|---------------|
| 1 | −1 | −1 | ȳ₁ |
| 2 | +1 | −1 | ȳ₂ |
| 3 | −1 | +1 | ȳ₃ |
| 4 | +1 | +1 | ȳ₄ |

**Estimates of effects:**
- Main A = [(ȳ₂ − ȳ₁) + (ȳ₄ − ȳ₃)]/2 = (−ȳ₁ + ȳ₂ − ȳ₃ + ȳ₄)/2
- Main B = [(ȳ₃ − ȳ₁) + (ȳ₄ − ȳ₂)]/2 = (−ȳ₁ − ȳ₂ + ȳ₃ + ȳ₄)/2
- AB interaction = [(ȳ₄ − ȳ₃) − (ȳ₂ − ȳ₁)]/2 = (ȳ₁ − ȳ₂ − ȳ₃ + ȳ₄)/2

In general, the effect estimate is the dot product of the contrast column with the means, divided by 2^{k−1}.

### 10.3 The 2³ Design

Three factors, 8 runs. Standard order is a 2×2×2 cube.

| Run | x₁ | x₂ | x₃ | x₁x₂ | x₁x₃ | x₂x₃ | x₁x₂x₃ |
|-----|----|----|----|------|------|------|---------|
| 1 | − | − | − | + | + | + | − |
| 2 | + | − | − | − | − | + | + |
| 3 | − | + | − | − | + | − | + |
| 4 | + | + | − | + | − | − | − |
| 5 | − | − | + | + | − | − | + |
| 6 | + | − | + | − | + | − | − |
| 7 | − | + | + | − | − | + | − |
| 8 | + | + | + | + | + | + | + |

Each effect estimate = (1/4) · Σ(contrast column × mean).

### 10.4 Variances and Confidence Intervals

For 2² or 2³ designs with r replicates:
- All effect estimators are of the form (1/2^{k−1}) Σ(±ȳᵢ).
- Var(effect estimator) = σ²/r for 2², σ²/(2r) for 2³.

**Pooled estimate of σ²:**
$$s^2 = \frac{1}{2^k(r-1)} \sum_{i=1}^{2^k} \sum_{j=1}^r (y_{ij} - \bar{y}_i)^2$$

**95% CI for an effect** (2² design with r reps): effect ± t_{α/2, 4(r−1)} · √(s²/r)

For 2³ design: effect ± t_{α/2, 8(r−1)} · √(s²/(2r))

### 10.5 Blocking a 2³ Design in Two Blocks

When all 8 runs cannot be run in one homogeneous session, divide into two blocks of 4. Confound the three-factor interaction with blocks: in one block x₁x₂x₃ = +1, in the other x₁x₂x₃ = −1. All main effects and two-factor interactions remain estimable; the three-factor interaction is sacrificed. The ABC interaction is rarely important, so this is a small price for a more precise experiment.

### 10.6 Higher Factorials and Fractional Designs

3^k designs are common. When 2^k is too large, use **fractional factorial designs** (e.g., 2^{k−1} half-fractions), confounding some interactions with others.

---

## 11. Multiple Comparisons

After a significant omnibus ANOVA F-test, individual pairwise comparisons require multiple-comparisons corrections to control the **family-wise error rate** (probability of at least one false positive).

### 11.1 Bonferroni Method (Most General)

Replace α with α/m where m is the number of comparisons. Each confidence interval uses t_{α/(2m), N−k}.

**95% Bonferroni CI for all differences μᵢ − μₗ (i < ℓ):**
$$\bar{y}_i - \bar{y}_\ell \pm t_{\alpha/[k(k-1)], N-k} \cdot s_e \sqrt{\frac{1}{n_i} + \frac{1}{n_\ell}}$$

Conservative but works for unequal sample sizes and arbitrary patterns.

### 11.2 Tukey's Honest Significant Difference (HSD)

For equal sample sizes n, the simultaneous CI for μᵢ − μₗ is:
$$\bar{y}_i - \bar{y}_\ell \pm \frac{q_{\alpha, k, N-k}}{\sqrt{2}} \cdot s_e \sqrt{\frac{2}{n}} = \bar{y}_i - \bar{y}_\ell \pm q_{\alpha}/\sqrt{2} \cdot \sqrt{2 s_e^2/n}$$

where q_{α, k, ν} is the upper-α quantile of the studentized range distribution. Tukey is exact (not just Bonferroni-type) for equal n. For unequal n, an approximation replaces √(2/n) with √(1/nᵢ + 1/nₗ).

### 11.3 Bonferroni Inequality

$P(\bigcap_i C_i) \geq 1 - \sum_i P(C_i^c)$

So if each interval has coverage at least 1 − α/m, the simultaneous coverage is at least 1 − α.

### 11.4 Strategy

1. Omnibus F-test first to establish at least one difference.
2. Bonferroni for general (unequal n) or Tukey HSD for equal n.
3. Always report family-wise confidence levels.

---

## 12. Chi-Squared Tests for Categorical Variables

### 12.1 Random Predictor (X and Y Both Random)

Counts fᵢⱼ in an a × b table, fᵢⱼ ~ Multinomial(n; πᵢⱼ) under H₀ of independence. MLEs: π̂ᵢⱼ = fᵢⱼ/n, π̂ᵢπ̂ⱼ under H₀.

**Test statistic:**
$$X^2 = \sum_{i,j} \frac{(f_{ij} - n\hat{\pi}_i\hat{\pi}_j)^2}{n\hat{\pi}_i\hat{\pi}_j} \stackrel{\text{approx}}{\sim} \chi^2_{(a-1)(b-1)}$$

**Degrees of freedom:** (a−1)(b−1) (one less per row and column due to constraints).

### 12.2 Deterministic Predictor (X Assigned)

Sample sizes nᵢ fixed. Conditional on X = i, Y values are iid from Multinomial(nᵢ; πᵢ₁,…,πᵢᵦ). MLEs: π̂ⱼ = f·ⱼ/n under H₀ of equal distributions.

**Test statistic:**
$$X^2 = \sum_{i,j} \frac{(f_{ij} - n_i \hat{\pi}_j)^2}{n_i \hat{\pi}_j} \stackrel{\text{approx}}{\sim} \chi^2_{(a-1)(b-1)}$$

### 12.3 Standardized Residuals

$$r_{ij} = \frac{f_{ij} - e_{ij}}{\sqrt{e_{ij}(1-\hat{\pi}_i)(1-\hat{\pi}_j)}}$$

Large |rᵢⱼ| (> 2 or 3) flag cells that contribute most to the χ² statistic. Use to identify the form of the relationship.

### 12.4 Goodness-of-Fit Tests

Compare observed fᵢ to expected n·πᵢ⁰ under a specified distribution π⁰:
$$X^2 = \sum_i \frac{(f_i - n\pi_i^0)^2}{n\pi_i^0} \sim \chi^2_{k-1}$$

For example, test Poisson(λ̂) fit: eᵢ = n · P(X = i | λ̂), with k = number of cells.

### 12.5 2×2 Tables

Independence ⇔ cross-ratio (π₁₁π₂₂)/(π₁₂π₂₁) = 1. With cell counts a, b, c, d, the test is:
$$\chi^2 = \frac{n(ad - bc)^2}{(a+b)(c+d)(a+c)(b+d)}$$

For small expected counts, use Fisher's exact test.

### 12.6 Bayesian Formulation

Place Dirichlet(α₁₁, …, α_ab) prior on cell probabilities. The posterior is Dirichlet(f₁₁ + α₁₁, …, f_ab + α_ab). For deterministic predictor, place independent Dirichlet priors on each row's probabilities. To generate from Dirichlet(α₁,…,α_k): generate sequentially from beta distributions (see Section 12.3 algorithm in source).

---

## 13. Logistic Regression

### 13.1 Setting

Binary response Y ∈ {0, 1} with quantitative predictors X₁, …, X_k. Use a link function ℓ: [0,1] → ℝ to express:
$$\ell[P(Y=1 | \mathbf{x})] = \beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k$$

### 13.2 The Logistic Link

ℓ(p) = ln(p/(1−p)) (logit / log odds). The inverse:
$$P(Y=1 | \mathbf{x}) = \frac{\exp(\beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k)}{1 + \exp(\beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k)}$$

The variance of Y given x is p(x)(1−p(x)), which depends on the predictors. Not strictly a regression model, but called **logistic regression**.

### 13.3 Other Links

- **Probit:** ℓ⁻¹ = Φ⁻¹ (inverse standard normal cdf).
- **Log-log:** ℓ(p) = ln(−ln(1−p)).
- **Complementary log-log:** ℓ(p) = ln(−ln(p)).

Any inverse cdf of a continuous distribution serves as a link.

### 13.4 Inference via Maximum Likelihood

Conditional likelihood:
$$L = \prod_i \left[\frac{e^{\boldsymbol{\beta}'\mathbf{x}_i}}{1+e^{\boldsymbol{\beta}'\mathbf{x}_i}}\right]^{y_i} \left[\frac{1}{1+e^{\boldsymbol{\beta}'\mathbf{x}_i}}\right]^{1-y_i}$$

No closed form; use iterative numerical methods (Newton–Raphson, IRLS). For inference, use large-sample (Wald) tests: β̂ᵢ / SE(β̂ᵢ) ~ N(0,1) approximately.

**Wald 95% CI for βᵢ:** $\hat{\beta}_i \pm z_{\alpha/2} \cdot SE(\hat{\beta}_i)$

### 13.5 Goodness of Fit (Hosmer–Lemeshow Type)

For grouped data (binary counts per cell), Pearson statistic:
$$X^2 = \sum_{\text{cells}} \frac{(s_j - m_j \hat{p}_j)^2}{m_j \hat{p}_j (1 - \hat{p}_j)}$$

where sⱼ = successes, mⱼ = trials, p̂ⱼ = fitted probability at cell j. Under the model, X² ~ χ²_{J−(k+1)} (J = number of cells, k+1 = number of estimated parameters).

### 13.6 Interpretation

The odds of Y = 1 at x vs. reference: odds ratio = exp(βᵢ Δxᵢ). For unit increase in xᵢ, odds multiply by e^{βᵢ}.

---

## 14. Matrix Formulation of Linear Regression (Reference)

### 14.1 Hat Matrix

$\mathbf{H} = \mathbf{X}(\mathbf{X}'\mathbf{X})^{-1}\mathbf{X}'$

Properties: symmetric, idempotent (H² = H), rank k+1. Fitted values: ŷ = Hy. Residuals: e = (I − H)y.

### 14.2 Residual Properties

- E(e) = 0
- Cov(e) = σ²(I − H)
- Trace(I − H) = n − k − 1 = df of error
- The leverage of observation i is hᵢᵢ (diagonal of H).

### 14.3 ANOVA via Matrices

- SS_{regression} = ŷ′ŷ − nȳ² = y′Hy − nȳ²
- SS_{total} = y′y − nȳ²
- SS_{error} = y′y − y′Hy = y′(I − H)y

---

## 15. Diagnostic Summary

| Plot | Detects |
|------|---------|
| Residuals vs. fitted | Non-constant variance, nonlinearity, model inadequacy |
| Residuals vs. predictor | Lurking variables, wrong functional form |
| Residuals vs. time/order | Time trends, autocorrelation |
| Residuals vs. other predictors | Cross-effects not in model |
| Normal Q-Q plot of residuals | Departures from normality, outliers |
| Scale-location plot (√|residuals| vs. fitted) | Heteroscedasticity |
| Leverage vs. residuals | Influential observations |
| Added-variable plot | Effect of adding one predictor |

**Influential points:** Large Cook's distance Dᵢ = eᵢ²/(k+1) · hᵢᵢ/[s²(1−hᵢᵢ)²] flags observations whose removal substantially changes the fit.

**Outliers:** Studentized residual |tᵢ| > 3 (or Bonferroni-adjusted threshold) flags outliers.

---

## 16. Key Distribution Theory

### 16.1 Standard Normal (Z)

P(Z ≤ z) for z ∈ ℝ; 1.96 for 95% two-sided.

### 16.2 t-Distribution (Student's t)

t_{ν} with ν df. Used for: one-sample, two-sample, paired t; regression coefficients; ANOVA contrasts.

### 16.3 Chi-Squared (χ²)

χ²_{ν} with ν df. Sum of squares of ν standard normals. Used for: goodness-of-fit, contingency tables, (n−2)s²ₑ/σ² ~ χ²_{n−2}.

### 16.4 F-Distribution

F_{ν₁,ν₂} = (χ²_{ν₁}/ν₁)/(χ²_{ν₂}/ν₂). Used for: ANOVA F-tests, F-test for regression.

### 16.5 Key Sampling Results for Regression

Under the linear regression model with normal errors:
- β̂ᵢ ~ N(βᵢ, σ²cᵢᵢ)
- (n − k − 1)s²ₑ/σ² ~ χ²_{n−k−1} independent of β̂
- (β̂ᵢ − βᵢ)/(sₑ√cᵢᵢ) ~ t_{n−k−1}
- F = (SS(Tr)/(k−1))/(SSE/(N−k)) ~ F_{k−1, N−k} under H₀ of equal means

---

## 17. Practical Implementation Notes

### 17.1 Sample Size for Detecting Differences

For two-sample comparison with common σ, to detect a difference δ with power 1−β:
$$n = \frac{2\sigma^2 (z_{\alpha/2} + z_\beta)^2}{\delta^2}$$

For ANOVA with k groups, similar formulas use the range of means or specific contrasts.

### 17.2 When to Use Each Procedure

| Goal | Procedure |
|------|-----------|
| Predict Y from X (quantitative) | Simple/multiple linear regression |
| Compare means of k groups | One-way ANOVA |
| Compare k groups with nuisance factor | Randomized block design |
| Study effects of two factors | Two-factor ANOVA |
| Adjust comparisons for covariate | ANCOVA |
| Binary response, quantitative predictors | Logistic regression |
| Two categorical variables | Chi-squared test of independence |
| Several means pairwise | Tukey HSD (equal n) or Bonferroni |

### 17.3 Common Pitfalls

- **Don't** extrapolate beyond the range of x.
- **Don't** confuse correlation with causation.
- **Don't** test main effects when interaction is significant.
- **Don't** use regression without checking residual plots.
- **Don't** apply regression when assumptions fail without transformation or alternative method.
- **Don't** ignore the family-wise error rate when making multiple comparisons.
- **Don't** apply ANOVA to non-normal data with very different variances without checking robustness.

---

## 18. Summary of Key Formulas

| Quantity | Formula |
|----------|---------|
| Sample mean | $\bar{x} = \sum x_i/n$ |
| Sample variance | $s^2 = \sum(x_i - \bar{x})^2/(n-1)$ |
| Sum of squares | $S_{xx} = \sum(x_i - \bar{x})^2$ |
| Covariance | $S_{xy} = \sum(x_i-\bar{x})(y_i-\bar{y})$ |
| Correlation | $r = S_{xy}/\sqrt{S_{xx}S_{yy}}$ |
| Slope (regression) | $\hat{\beta} = S_{xy}/S_{xx}$ |
| Intercept | $\hat{\alpha} = \bar{y} - \hat{\beta}\bar{x}$ |
| Residual SS | $SSE = S_{yy} - S_{xy}^2/S_{xx}$ |
| Estimate of σ² | $s_e^2 = SSE/(n-2)$ |
| Slope SE | $SE(\hat{\beta}) = s_e/\sqrt{S_{xx}}$ |
| Mean response SE at x₀ | $s_e\sqrt{1/n + (x_0-\bar{x})^2/S_{xx}}$ |
| Prediction SE at x₀ | $s_e\sqrt{1 + 1/n + (x_0-\bar{x})^2/S_{xx}}$ |
| R² | $S_{xy}^2/(S_{xx}S_{yy}) = r^2$ |
| F-statistic (regression) | $(\hat{\beta}^2 S_{xx})/s_e^2$ |
| ANOVA F (one-way) | MS(Tr)/MSE |
| Bonferroni CI | uses $t_{\alpha/[2k(k-1)], N-k}$ |
| Tukey HSD | uses $q_{\alpha, k, N-k}/\sqrt{2}$ |
| Fisher Z | $Z = \frac{1}{2}\ln[(1+r)/(1-r)]$ |

---

## 19. Closing Notes

The material in this reference file integrates the full toolkit for studying relationships among variables: from foundational concepts of causation and experimental design, through the rich family of regression techniques, the analysis of variance for designed experiments, multiple comparisons, the analysis of covariance, and specialized methods for categorical responses. Mastery of these techniques requires both the mathematical derivations summarized here and the practical wisdom gained from careful model checking and respect for the assumptions underlying each method. The same data set can often be analyzed by several methods; the choice depends on the research question, the data structure, and the validity of the assumptions in the specific application.
