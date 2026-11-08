# Anthemis Janvier 2018: structured product pricing

Monte Carlo valuation of the structured note **Anthemis Janvier 2018 (10Y, EUR)**, issued by Morgan Stanley & Co International Plc on the EURO STOXX 50. The note is priced as of 8 June 2021, mid-life, under two models:

1. Black-Scholes (geometric Brownian motion with a flat volatility).
2. Heston stochastic volatility.

The repository also computes finite-difference sensitivities (delta, gamma, vega under Black-Scholes; sensitivities to the Heston parameters $\rho$ and $\eta$).

## The product

Terms are taken from the final terms and conditions in `docs/term_sheet_anthemis_2018.pdf`.

| Item | Value |
| :--- | :--- |
| ISIN | FR0013265519 |
| Issuer | Morgan Stanley & Co International Plc (Moody's A1) |
| Underlying | EURO STOXX 50 Index (SX5E, ISIN EU0009658145) |
| Issue date / issue price | 8 September 2017 / 99.59% of the denomination |
| Strike fixing, $S_0$ | 3,620.91 on 18 January 2018 |
| Observation dates | 10 annual dates, from 11 January 2019 to 11 January 2028 |
| Final determination date / maturity | 11 January 2028 / 18 January 2028 |
| Bonus barrier | 70% of $S_0$ = 2,534.64 |
| Capital barrier | 60% of $S_0$ = 2,172.55 (European, observed at the end only) |

There is no early redemption. Everything is paid at maturity.

**Bonus.** On each observation date $t_i$ the note earns a bonus of 5.50% of the nominal $N$ if the index closes at or above the bonus barrier:

$$
\text{Bonus}_i = 0.055 x N \cdot \mathbf{1}_{\{ S_{t_i} \ge 0.70 \, S_0 \}}, \qquad i = 1, \dots, 10
$$

**Redemption.** At maturity the capital is repaid in full unless the index finished below the capital barrier, in which case the investor bears the full fall of the index:

$$
R =
\begin{cases}
N & \text{if } S_T \ge 0.60 \, S_0 \\
N \cdot \dfrac{S_T}{S_0} & \text{if } S_T < 0.60 \, S_0
\end{cases}
$$

**Status at the valuation date (8 June 2021).** The index is at 4,096.01. The first three observations (2019, 2020, 2021) were all above the bonus barrier, so 3 bonuses are already locked in. Seven observations remain.

With $N = 100$, $k = 3$ locked bonuses and $F$ the set of the 7 remaining observation dates, the value computed by the code is

$$
V_0 = P(0, T) \; \mathbb{E}^{\mathbb{Q}} \left[ 5.5 \left( k + \sum_{i \in F} \mathbf{1}_{\{ S_{t_i} \ge 0.70 \, S_0 \}} \right) + R \right]
$$

where the expectation is estimated by Monte Carlo with 10,000 paths.

## Method

### Discounting

Zero rates (EONIA and EURIBOR curve, retrieved from Bloomberg on 11 June 2021) are linearly interpolated at each payment time $\tau_i$ (the notebook labels this interpolation "Taylor-Young"). With $r_i$ the interpolated rate at $\tau_i$ and $\tau_0 = 0$, the discount factors are

$$
P(0, \tau_i) = \prod_{k=1}^{i} (1 + r_k)^{-(\tau_k - \tau_{k-1})}
$$

Rates are negative over most of the curve, so some discount factors are slightly above 1. Only the factor at maturity is used, since all cash flows are paid then.

### Black-Scholes

Under the risk-neutral measure $\mathbb{Q}$:

$$
dS_t = (r_t - q) \, S_t \, dt + \sigma \, S_t \, dW_t
$$

Paths are simulated exactly on the observation dates:

$$
S_{t_j} = S_{t_{j-1}} \exp \left( \left( r_j - q - \frac{1}{2} \sigma^2 \right) \Delta t_j + \sigma \sqrt{\Delta t_j} \, Z_j \right), \qquad Z_j \sim \mathcal{N}(0, 1)
$$

Inputs: $\sigma$ = 19.03% (the 260-day volatility of the index on 8 June 2021, from the data file), dividend yield $q$ = 2.67% (projected 12-month yield from Bloomberg), and $r_j$ the interpolated zero rate at $t_j$.

### Heston

Under $\mathbb{Q}$:

$$
dS_t = (r_t - q) \, S_t \, dt + \sqrt{v_t} \, S_t \, dW^S_t
$$

$$
dv_t = \kappa \, (\theta - v_t) \, dt + \eta \sqrt{v_t} \, dW^v_t, \qquad d\langle W^S, W^v \rangle_t = \rho \, dt
$$

Parameters used in the notebook:

| Parameter | Value | Meaning |
| :--- | :--- | :--- |
| $v_0$ | 0.0362 | initial variance, the square of 0.1903 |
| $\theta$ | 0.0362 | long-run variance, set equal to $v_0$ |
| $\kappa$ | 2 | speed of mean reversion |
| $\eta$ | 1.5 | volatility of variance |
| $\rho$ | -0.85 | correlation between spot and variance shocks |

These values are chosen by hand. They are not calibrated to an option surface. The Feller condition $2 \kappa \theta \ge \eta^2$ does not hold ($0.145 < 2.25$), so the variance can reach zero.

**Discretisation.** The time grid has a step of 0.01 years, plus the observation dates. On each step $\Delta t$, with correlated shocks $Z^v = \rho \, Z^S + \sqrt{1 - \rho^2} \, Z^{\perp}$:

$$
S_{k+1} = S_k \exp \left( \left( r_k - q - \frac{1}{2} v_k \right) \Delta t + \sqrt{v_k \, \Delta t} \; Z^S_k \right)
$$

$$
v_{k+1} = v_k + \kappa \, (\theta - v_k) \, \Delta t + \eta \sqrt{v_k \, \Delta t} \; Z^v_k
$$

If the new variance is not positive, the same update is recomputed with the sign of the variance shock flipped, $-Z^v_k$ (a reflection of the noise term). Because the drift part is positive for this step size, the flipped update is always positive.

## Results

All numbers below come from the notebook with the fixed seeds described in the next section. Prices are in % of the nominal. The standard error is that of the Monte Carlo mean over 10,000 paths.

| Model | Price | Standard error |
| :--- | :--- | :--- |
| Black-Scholes | 136.91 | 0.33 |
| Heston | 103.70 | 0.52 |

For reference, the issue price in September 2017 was 99.59%. This is the price at launch, not a quote for June 2021.

The two models disagree by about 33 points, far more than the Monte Carlo error. As a consistency check, setting $\eta = 0$ in the Heston code removes the stochastic volatility and gives 137.20, within Monte Carlo error of Black-Scholes. So the gap comes from the Heston parameters, not from the discretisation. A negative $\rho$ and a high $\eta$ put more probability on large falls of the index, which matters for a note that loses capital below the 60% barrier. Because the parameters are not calibrated, the Heston price should be read as an illustration of model dependence, not as a fair value.

### Sensitivities

| Quantity | Model | Value | Definition |
| :--- | :--- | :--- | :--- |
| Delta | Black-Scholes | 63.44 | central difference with the spot bumped up and down by 5% of its value, per unit of relative spot move (about 0.63 price points per +1% on the index) |
| $\partial V / \partial \rho$ | Heston | -8.48 | central difference, $\varepsilon = 0.05$ |
| $\partial V / \partial \eta$ | Heston | -28.56 | central difference, $\varepsilon = 0.1$ |

Delta, gamma and vega are also computed as functions of the initial spot, from 20% to 200% of the strike in 1% steps, and plotted in the notebook. Gamma is the plain second difference with a step of 5% of the strike, not divided by the squared step. Vega is the price change per volatility point (bump of $\pm 0.01$ on $\sigma$). Bumped and unbumped runs use the same random numbers.

The sensitivity to $\rho$ is the noisiest of the three. Earlier runs without a fixed seed gave -10.2 and -12.1 for it, against -8.5 here.

## Reproducibility

The random numbers are drawn with `numpy.random.seed` set before each random block of the notebook:

| Notebook cell | Seed | Draws |
| :--- | :--- | :--- |
| BS Diffusion, random matrix | 42 | Gaussian draws reused for the Black-Scholes Greeks |
| BS Diffusion, price | 43 | Gaussian draws for the Black-Scholes price |
| Heston, random matrices | 44 | spot and variance shocks for all Heston runs |

`src/strategy.py` itself draws no random numbers; it receives the shocks as arguments. Two independent runs of the notebook, in separate processes, gave identical outputs and identical plots.

Tested with Python 3.13, numpy 2.5 and pandas 2.3. `requirements.txt` restricts pandas to versions below 3, because `strategy.py` uses `DataFrame.applymap`, which pandas 3 removed.

## Repository structure

```text
structured-product-anthemis-engine/
  README.md
  LICENSE
  requirements.txt
  pytest.ini
  .gitignore
  data/
    historic_data_sx5e.xlsx          SX5E close and 260-day volatility, Bloomberg
  docs/
    term_sheet_anthemis_2018.pdf     Morgan Stanley final terms and conditions
  src/
    __init__.py
    strategy.py                      BS and Heston path generators, payoff and pricing
  notebooks/
    Anthemis_Pricing_Walkthrough.ipynb
  tests/
    test_pricing.py
```

The data file has 868 daily observations from 18 January 2018 to 8 June 2021, with columns `PX_LAST` and `VOLATILITY_260D`.

## Usage

```bash
git clone https://github.com/bahakh19/structured-product-anthemis-engine.git
cd structured-product-anthemis-engine

python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

pytest
```

The notebook was written in Google Colab. It reads `/content/historic_data_sx5e.xlsx` and imports `strategy` from its own folder. To run it elsewhere, copy `data/historic_data_sx5e.xlsx` and `src/strategy.py` next to the notebook and change the path in the data-loading cell.

## Limitations

- The Heston parameters are not calibrated, and the Black-Scholes volatility is a historical one, not an implied one.
- Discounting uses the interpolated zero curve with a zero spread: no issuer credit or funding spread is included.
- Prices are mid values from 10,000 paths, with no bid-offer, fees or taxes.

## Author

Khaled Baha, Magistère BFA (Banque, Finance, Assurance), Université Paris-Dauphine.
GitHub: [bahakh19](https://github.com/bahakh19)

## License

MIT, see `LICENSE`.
