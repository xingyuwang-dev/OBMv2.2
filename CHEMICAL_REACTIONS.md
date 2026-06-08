# Core Chemical Reaction Equations

This file summarizes the core equations used by the OBM Python model. The detailed reaction lists live in the mechanism modules, especially `CB05/CB05_AllRxns.py` and the MCMv331 modules. The equations below describe how those mechanism reactions are assembled and evaluated by `core.InitializeChemistry`, `core.F0AM_ModelCore2`, and `core.jit_solver`.

## Species Concentration State

The model state vector is

$$
\mathbf{C}(t)=\left[C_1(t), C_2(t), \ldots, C_{N_s}(t)\right],
$$

where species concentrations are represented internally in molecules per cubic centimeter:

$$
[X]_{\text{molec}/\text{cm}^3}
= [X]_{\mathrm{ppb}} \times M \times 10^{-9}.
$$

Here \(M\) is air number density:

$$
M = \frac{P N_A}{R T}\times 10^{-6}.
$$

## Generic Reaction Rate

The mechanism is represented as reactions of the form

$$
\sum_i \alpha_{ri} X_i \longrightarrow \sum_i \beta_{ri} X_i,
$$

with net stoichiometric coefficient

$$
\nu_{ri} = \beta_{ri}-\alpha_{ri}.
$$

In code, \(\nu_{ri}\) is stored in the sparse stoichiometric matrix \(f\), where rows are reactions and columns are species.

For a bimolecular reaction,

$$
A + B \xrightarrow{k_r} \mathrm{products},
$$

the reaction rate is

$$
R_r = k_r [A][B].
$$

For a first-order reaction or photolysis reaction, the mechanism uses the placeholder species `ONE`:

$$
A + \mathrm{ONE} \xrightarrow{k_r \ \mathrm{or}\ J_r} \mathrm{products},
$$

with

$$
[\mathrm{ONE}] = 1,
$$

so that

$$
R_r = k_r[A] \quad \text{or} \quad R_r = J_r[A].
$$

The vectorized reaction-rate expression used by the solver is

$$
\mathbf{R}
= \mathbf{k}\odot
\left(\mathbf{C}_{iG_1}\odot \mathbf{C}_{iG_2}\right),
$$

where \(iG_1\) and \(iG_2\) are the two reactant-index columns from `iG`, and \(\odot\) is elementwise multiplication.

## ODE System

The concentration tendency for species \(i\) is

$$
\frac{dC_i}{dt}
= \sum_{r=1}^{N_r} \nu_{ri} R_r
- k_{\mathrm{dil}}\left(C_i-C_{i,\text{bkgd}}\right).
$$

In matrix form:

$$
\frac{d\mathbf{C}}{dt}
= \mathbf{R}^{\mathsf{T}}\mathbf{f}
- k_{\mathrm{dil}}\left(\mathbf{C}-\mathbf{C}_{\text{bkgd}}\right).
$$

For species marked as held species (`iHold`), the model sets

$$
\frac{dC_i}{dt}=0,\qquad i\in iHold.
$$

## RO2 Aggregate

The model keeps a special aggregate species `RO2`. It is updated from the configured RO2 species list:

$$
[\mathrm{RO2}]
= \sum_{j\in iRO2} [X_j].
$$

This aggregate is used for mechanism compatibility and diagnostic output.

## Photolysis Correction

Photolysis rates are initialized from the selected mechanism J function:

$$
J_r^{0}=J_r(\mathrm{SZA}, T, P, O_3^{\mathrm{col}}, \mathrm{albedo}, \ldots).
$$

If an observed or externally supplied photolysis rate is available, the correction factor is

$$
\gamma_r
= \frac{J_r^{\mathrm{obs}}}{J_r^{0}}.
$$

The corrected J value is then

$$
J_r = \gamma_r J_r^{0}.
$$

For nighttime or invalid zero-rate cases, the code avoids unstable divisions by forcing the correction factor to 1:

$$
\gamma_r = 1 \quad \text{when } \mathrm{SZA}\ge 90^\circ \text{ or } J_r^{0}=0.
$$

## NOx Constraint Option

When `FixNOx` is enabled, NO and NO2 are rescaled to preserve the prescribed total NOx while keeping the modeled partitioning:

$$
\mathbf{C}_{\text{NOx,new}}
= \mathbf{C}_{\text{NOx,model}}
\times
\frac{\sum \mathbf{C}_{\text{NOx,init}}}
{\sum \mathbf{C}_{\text{NOx,model}}}.
$$

This corresponds to the code path:

$$
\begin{aligned}
\left([\mathrm{NO}], [\mathrm{NO_2}]\right)_{\text{new}}
&=
\left([\mathrm{NO}], [\mathrm{NO_2}]\right)_{\text{model}}
\times
\frac{[\mathrm{NO}]_{\text{init}}+[\mathrm{NO_2}]_{\text{init}}}
{[\mathrm{NO}]_{\text{model}}+[\mathrm{NO_2}]_{\text{model}}}.
\end{aligned}
$$

## Ozone Production and Loss Diagnostics

`post_process.P_O3subNO` computes ozone production and loss diagnostics from CB05 species and rate constants. The main ozone production terms are:

$$
P_{\mathrm{HO_2+NO}}
= k_{\mathrm{HO_2+NO}}[\mathrm{HO_2}][\mathrm{NO}]M\Delta t.
$$

$$
\begin{aligned}
P_{\mathrm{RO_2+NO}}
&=
\Big(
k_{\mathrm{XO2+NO}}[\mathrm{XO2}]
+ k_{\mathrm{XO2N+NO}}[\mathrm{XO2N}] \\
&\quad
+ k_{\mathrm{MEO2+NO}}[\mathrm{MEO2}]
+ k_{\mathrm{TO2+NO}}[\mathrm{TO2}]
\Big)
[\mathrm{NO}]M\Delta t.
\end{aligned}
$$

Thus

$$
P(O_3)=P_{\mathrm{HO_2+NO}}+P_{\mathrm{RO_2+NO}}.
$$

The diagnostic ozone loss terms include:

$$
L_{\text{O}_3\text{ photolysis}}
= J_{\mathrm{O_3\rightarrow O(^1D)}}[\mathrm{O_3}]\Delta t.
$$

$$
L_{\mathrm{O_3+OH}}
= k_{\mathrm{O_3+OH}}[\mathrm{O_3}][\mathrm{OH}]M\Delta t.
$$

$$
L_{\mathrm{O_3+HO_2}}
= k_{\mathrm{O_3+HO_2}}[\mathrm{O_3}][\mathrm{HO_2}]M\Delta t.
$$

$$
L_{\mathrm{NO_2+OH}}
= k_{\mathrm{NO_2+OH}}[\mathrm{NO_2}][\mathrm{OH}]M\Delta t.
$$

and alkene ozonolysis:

$$
\begin{aligned}
L_{\mathrm{alkene+O_3}}
&=
\Big(
k_{\mathrm{IOLE+O_3}}[\mathrm{IOLE}]
+ k_{\mathrm{OLE+O_3}}[\mathrm{OLE}] \\
&\quad
+ k_{\mathrm{ETH+O_3}}[\mathrm{ETH}]
+ k_{\mathrm{ISOP+O_3}}[\mathrm{ISOP}]
+ k_{\mathrm{TERP+O_3}}[\mathrm{TERP}]
\Big)
[\mathrm{O_3}]M\Delta t.
\end{aligned}
$$

The net diagnostic ozone tendency is

$$
\Delta O_3 = P(O_3)-L(O_3).
$$

In the current RIR diagnostics, \(\Delta t=3600\ \mathrm{s}\).

## OH Reactivity

For a species group \(G\), OH reactivity is expressed as

$$
k_{\mathrm{OH},G}
= \sum_{i\in G} k_{\mathrm{OH}+X_i}[X_i]M.
$$

`post_process.P_O3subNO` groups OH reactivity into SO2, aromatics, alkanes, alkenes, NO2, HNO3, NO, PNA, HONO, HO2, CO, CH4, and OVOCs.

## RIR Definition

For a precursor group \(X\), relative incremental reactivity is computed from the change in ozone production after reducing \(X\). For a 10% reduction, the reduced case is written as \(0.9X\):

$$
\begin{aligned}
\mathrm{RIR}_X
&=
\frac{P(O_3)_{\mathrm{base}}-P(O_3)_{0.9X}}
{P(O_3)_{\mathrm{base}}}
\times 10.
\end{aligned}
$$

The code applies the same form to CO, NOx, VOCs, olefins, aromatics, and OVOCs.
