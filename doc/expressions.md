# Expressions


Basics
------

The basic concept is to load one (`nw(name)`) or multiple (`nws()`) networks, get a specific S-parameter (`s(i,j)`), and plot it (`plot()`):

```python
    nws("*amp.s2p").s(2,1).plot("IL")
```

Which could be re-written as:

```python
    n = nws("*amp.s2p")  # type: Networks
    s = n.s(2,1)         # type: SParams
    s.plot("IL")
```

However, there is also a quicker way if you don't need full control:

```python
    quick(21)
```

The expressions use [Python](https://docs.python.org/3/) syntax. You have access to:
- The global functions described in the section below;
- The classes `Networks` and `SParams`, described in the sections below;
- The libraries `math` ([math](https://docs.python.org/3/library/math.html)) and `np` ([NumPy](https://numpy.org/doc/)).


Global Functions
----------------

### quick()

```python
quick(*parameters)
```

Quick plotting of some parameters, indicated either as an integer (e.g. `21` for S21), a string (e.g. `"21"` or `"2,1"` for S21), or by a tuple (e.g. `(2,1)` for S21.).

Examples:
```python
quick(21)           # plot S21
quick(21, 22)       # plot S21 and S22
quick((1,3), "33")  # plot S13 and S33
```


### nws()

```python
nws(pattern=None)
```

If no pattern is provided, returns a `Networks` object that contains all networks.

If a pattern is provided, returns a `Networks` object that contains all networks that match the given pattern, e.g. `'*.s2p'`. Note that this returns an empty `Networks` object if the pattern does not match anything (instead of raising an error).

### sel_nws()

```python
sel_nws(pattern=None)
```

Same as `nws()`, except that it only matches networks that are currently selected.


### nw()

```python
nw(pattern=None)
```

Same as `nws()`, except that it is intended to select exactly one network. Throws an error if zero or more than one network is matched.


Classes
-------

- `Networks`: a container for one or more RF networks.
- `SParams`: a container for one or more S-parameters, or X-/Y-data in general.


### Networks

A container for one or more S-parameter networks.

To get a `Networks` object, call the global functions `nws()`, `sel_nws()` or `nw()`.

Note that any operation on the object may, by design, fail silently. For example, if an object contains a 1-port and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports), the 1-port will silently be dropped. This is to avoid excessive errors when applying general expressions on a large set of networks.

#### Methods


##### plot_sel_params()

```python
plot_sel_params()
```

Plots the parameters of the networks, in the same way it would be plotted if expressions were not used.

##### s(), z(), y(), abcd(), t()

```python
s(ports = None, *, rl_only=False, il_only=False, fwd_il_only=False, rev_il_only=False, name=None) → SParams
s(egress_port=None, ingress_port=None, *, rl_only=False, il_only=False, fwd_il_only=False, rev_il_only=False, name=None) → SParams
z(...)
y(...)
abcd(...)
t(...)
```

`s()` returns S-parameters (an `SParams` object) of a network. Analogously,
- `z()` returns the Z-matrix parameters,
- `y()` returns the Y-matrix parameters,
- `abcd()` returns the ABCD-matrix parameters,
- `t()` returns the T-matrix (scattering transfer) parameters,

There are two variants with different positional arguments, and the same keyword arguments. The positional arguments can be:
- `ports` is an integer: e.g. `s(21)` for S21.
    - Only valid for `11` to `99`.
- `ports` is a string: e.g. `s("21")` or `s("2,1")` for S21.
    - You may also use e.g. `'dd21'` or `'cd4,3'` for a mixed-mode network. The mixed-mode network must have port order <diff1, diff2, ..., comm1, comm2, ...>.
- `egress_port` and `ingress_port` are integers: e.g. `s(2,1)` for S21.
    - You may use `any` as a wildcard, e.g. `s(2,any)` for S21, S22, S23, ...
- No positional argument: everything (i.e. `s()`).

In any case, further filtering is possible with the keyword arguments:
- `rl_only=True`: only S11, S22, S33, ...
- `il_only=True`: only S21, S12, S31, ...
- `fwd_il_only=True`: only S21, S31, S32, ...
- `rev_il_only=True`: only S12, S13, S23, ...

Additionally, a name (which is shown in the plot legend) can be provided. If no explicit name is provided, a reasonable name is selected, e.g. `'S21'`.


Examples:
```python
s(2,1)                 # S21
s(21)                  # S21
s('21')                # S21
s('2,1')               # S21
s('dd21')              # SDD21
s(rl_only=True)        # S11, S22, S33, ...
s(any, 1)              # S11, S21, S31, ...
s(3,any,il_only=True)  # S31, S32, ...
```

##### invert()

```python
invert() → Networks
```

Inverts the network (e.g. for de-embedding).

##### flip()

```python
flip() → Networks
```

Flips the ports (e.g. to use it in reverse direction).

##### half()

```python
half(method='IEEE370NZC', side=1) → Networks
```

Chops the network in half (e.g. for 2xTHRU de-embedding).

Allowed methods are `'IEEE370NZC'` (IEEE-370, no Z-compensation), or 'ChopInHalf'. For IEEE-370, an additional argument `side` may be provided, to return the left side (`1`) or the right side (`2`).

##### k()

```python
k() → SParams
```

Returns the K (Rollet) stability factor. For a stable network, this should be >1 (or >0 dB).

##### mu()

```python
mu(mu=1) → SParams
```

Returns the µ (mu=1, default) or µ' (mu=2) method stability factor (Edwards-Sinsky). For a stable network, this should be >1 (or >0 dB).

##### losslessness()

```python
losslessness(egress_port_or_kind,ingress_port=None) → SParams
```

Checks a network for losslessness. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T \cdot S^* = U$ (wher $U$ is the unit matrix). This function calculates, for each frequency, $|S^T \cdot S^* - U|$, and returns the highest value of that matrix.


##### passivity()

```python
passivity() → SParams
```

Checks a network for passivity. For a reciprocal network, the result should be 0.

For a passive network, all eigenvalues $\lambda$ of the matrix $S^{T*} \cdot S$ should be $\lambda \le 1$. This function calculates, for each frequency, the eigenvalues, finds the highest eigenvalue $\lambda'$, and returns $max(0, \lambda'-1)$.


##### reciprocity()

```python
reciprocity() → SParams
```

Checks a network for reciprocity. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T = S$. This function calculates, for each frequency, $|S^T - S|$, and returns the highest value of that matrix.


##### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → Networks
```

Returns the same network, but with a reduced frequency range


##### add_sr()

```python
add_sr(resistance, port=]) → Networks
```

Returns a network with a series resistance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_sl()

```python
add_sl(inductance, port=1) → Networks
```

Returns a network with a series inductance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_sc()

```python
add_sc(capacitance, port=1) → Networks
```

Returns a network with a series inductance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_pr()

```python
add_pr(resistance, port=1) → Networks
```

Returns a network with a parallel resistance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_pl()

```python
add_pl(inductance, port=1) → Networks
```

Returns a network with a parallel inductance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_pc()

```python
add_pc(capacitance, port=1) → Networks
```
Returns a network with a parallel inductance attached to the specified port. Works only for 1-ports and 2-ports.


##### add_tl()

```python
add_tl(degrees, frequency_hz=1e9, z0=None, loss_db=0, port=1]) → Networks
```

Returns a network with anideal transmission line attached to the specified port. Works only for 1-ports and 2-ports.

The length is specified in degrees at the given frequency.

The loss is the real part of the propagation constant, and is constant over frequency.

If `z0` is not provided, the reference impedance of the corresponding port is used.


##### add_ltl()

```python
add_ltl(degrees, len_m, eps_r, db_m_mhz=0, db_m_sqmhz=0, port=1) → Networks
```

Returns a network with a lossy transmission line attached to the specified port. Works only for 1-ports and 2-ports.

The length is specified in meters, and the dielectric constant must be provided as well.

The loss is specified in two terms, one in dB/(m⋅Hz), one in dB/(m⋅√Hz).

If `z0` is not provided, the reference impedance of the corresponding port is used.


##### rl_avg()

```python
rl_avg(f_integrate_start_hz=-inf, f_integrate_stop_hz=+inf, f_target_start_hz=-inf, f_target_stop_hz=+inf) → SParams
```

Does the same as the [Return Loss Integrator](tools.md): integrates the return loss over the given integration frequency range, then calculates the achievable RL over the target range.



##### plot_stab()

```python
plot_stab(frequency_hz, port=2, n_points=101, label=None, style='-')
```

Plots the stability circle at the given frequency.

Set `port=1` if you want to calculate the stability at the input, otherwise the output is calculated.

It adds "s.i." (stable inside circle) or "s.o." (stable outside of the circle) to the plot name.


##### s2m()

```python
s2m(ports):
```

Single-ended to mixed-mode conversion.

The expected port order for the single-ended network is <pos1, neg1, pos2, neg2, ...>.

You may define your own mapping with <inp>; e.g. if your data is <pos1, pos2, neg1, neg2>, you can provide <inp=['p1','p2','n1','n2']>.

The generated mixed-mode network has port order <diff1, diff2, ..., comm1, comm2, ...>.

##### m2s()

```python
m2s([inp=<ports>][, outp=<ports>]):
```

Mixed-mode to single-ended conversion.

The expected port order for the single-ended network is <diff1, diff2, ..., comm1, comm_2, ..>.

You may define your own mapping with <inp>; e.g. if your data is <diff1, diff2, comm1, comm2>, you can provide <inp=['d1','d2','c1','c2']>.

The generated mixed-mode network has port order <pos1, neg1, pos2, neg2, ...>.


##### renorm()

```python
renorm(z)
```

Renormalize to a specific reference impedance. <z> can be a scalar, or a list of scalars (one per port).


##### rewire()

```python
rewire(ports: list[int])
```

Re-wires a network. The argument is the list of ports to keep.

Examples:
```python
# swap ports of a 2-port
nw('amp').rewire([2,1]).plot()

# only keep port 2
nw('multiport').rewire([2]).plot()

# remove (i.e. terminate) 3rd port
nw('coupler').rewire([1,2,4]).plot()
```


##### quick()

```python
quick(quick(parameter[, parameter...]))
```

Does the same as the global `quick()` function, see section above.


#### Unary Operators

##### Inversion

```python
~
```

Same as `invert()`.


#### Binary Operators

##### Cascade

```python
**
```

Cascades two networks. Frequency grids are interpolated accordingly.


### SParams

A container for one or more S-parameters, or X-/Y-data in general.

To get an `SParams` object, call `s()` on a `Networks` object.

#### Methods


##### plot()

```python
plot(label=None, style='-', color=None, width=None, opacity=None)
```

Plots the data. `label` is any string. The placeholder `'$NAME'` is replaced with the name of the parameter.

`style` is a [matplotlib](https://matplotlib.org/stable/users)-compatible format (e.g. `'-'`, `':'`, `'--'`, `'o-'`).

`color` is a [matplotlib](https://matplotlib.org/stable/users)-compatible color (e.g. `'red'`, `'#FF0000'`, `'F00'`).

`width` is the line width, `opacity` is the line opacity (where 0 means fully invisible, and 1 means fully visible).


##### db()

```python
db() → SParams
```

Returns $20 \cdot \log_{10} S$.

Plot this on a linear scale (otherwise the logarithm is applied *twice*).

##### db20()

```python
db20() → SParams
```

Same as `db20()`.

Plot this on a linear scale (otherwise the logarithm is applied *twice*).

##### db10()

```python
db10() → SParams
```

Returns $10 \cdot \log_{10}S$.

Plot this on a linear scale (otherwise the logarithm is applied *twice*).


##### ml()

```python
ml() → SParams
```

Mismatch loss: returns $1-|S²|$.

Plot this on a dB-scale, or use the `db()` function.


##### vswr()

```python
vswr() → SParams
```

Voltage Standing Wave Ratio: returns $(1+|S²|)/(1-|S²|)$.

Plot this on a linear scale.



##### abs()

```python
abs() → SParams
```

Returns $|S|$.


##### phase()

```python
phase(processing=None) → SParams
```

Returns the phase.

`processing` can be `None`, `'unwrap'` (unwrap phase), or `'remove_linear'` (unwrap, then remove linear phase).

Plot this on a linear scale.


##### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → SParams.
```

Returns the same S-Param, but with a reduced frequency range.


##### mean()

```python
mean() → SParams.
```

Returns the arithmetic mean of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.


##### median()

```python
median() → SParams.
```

Returns the median of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.


##### sdev()

```python
sdev(ddof=1) → SParams.
```

Returns the standard deviation of multiple S-parameters. The paraemter `ddof` is the delta degrees of freedom which is handed into NumPy's `std()` function. Applies `interpolate()` first, to get a common frequency grid.


##### interpolate()

```python
interpolate(n: int = None) → SParams.
```

Interpolates all S-parameters to have the same, equidistant frequency grid.

The lowest and highest frequency of all S-parameters is taken as the new range, and the aveage number of points is used for the new frequency grid, unless `n` is explicitly given.


##### interpolate_lin()

```python
interpolate_lin(f_start: float, f_end: float, n: int) → SParams.
```

Interpolates all S-parameters to have the same, equidistant frequency grid.


##### interpolate_lin()

```python
interpolate_lin(f_start: float, f_end: float, n: int) → SParams.
```

Interpolates all S-parameters to have the same, logarithmic frequency grid.


##### map()

```python
map(fn: callable) → SParams.
```

Applies an arbitrary function to each S-parameter. The function `fn` is called for each S-parameter (`numpy.ndarray`) individually.

Example:

```python
sel_nws().s(1,1).map(lambda s: s**2).plot()  # squares the linear S-parameters
```


##### rename()

```python
rename(name: str=None, prefix: str=None, suffix: str=None, pattern: str=None, subs: str=None) → SParams.
```

Renames S-parameters; parameters:
- `name`: if provided, replaces the whole name with `name`
- `prefix`: if provided, prepends the existing name with `prefix`
- `suffix`: if provided, appends `suffix` to the existing name
- `pattern` and `subs`: if provided, the regex `pattern` is replaced with `subs`

Example:

```python
sel_nws().s(2,1).rename(prefix='Gain of').plot()
```


#### Unary Operators


##### Inversion

```python
~
```

Returns the inverse (i.e. $1/S$).

#### Binary Operators


```python
+ - * /
```
Applies the corresponding mathematical operator. Each operand can also be a numeric constant.


Examples
========

Basic
-----

```python
nws().s(1,1).plot("RL")              # plot S11 of all network
sel_nws().s(1,2).plot("Reverse IL")  # plot S12 of selected networks
nws("amp.s2p").s(2,1).plot("IL")     # plot S21 of a specific network
nw("amp.s2p").s(1,1).plot("RL",":")  # plot S11 of a specific network, dashed line
```

Formatting
--------

```python
sel_nws().s(il_only=True).plot(color='blue')   # plot insertion losses in blue
sel_nws().s(rl_only=True).plot(color='red')  # plot return losses in red
```

Advanced
--------

```python
# calculate directivity (S42/S32) of a directional coupler
# note that this example requires plotting in linear units, as the values are already converted to dB
(nw("coupler_4port.s4p").s(4,2).db() - nw("coupler_4port.s4p").s(3,2).db()).plot("Directivity")

# de-embed a 2xTHRU
(nw("thru.s2p").half(side=1).invert() ** nw("atty_10db.s2p") ** nw("thru.s2p").half(side=2).flip()).s(2,1).plot("De-embedded")

# crop frequency range; this can be handy e.g. if you want to see the Smith-chart only for a specific frequency range
nws("amp.s2p").crop_f(10e9,11e9).s(1,1).plot("RL",":")

# calculate stability factor
nws("amp.s2p").mu().plot("µ Stability Factor",":")

# add elements to a network (in this case, a parallel cap, followed by a short transmission line)
nws("amp.s2p").s(1,1).plot("Baseline",":")
nws("amp.s2p").add_pc(400e-15).add_tl(7,2e9,25).s(1,1).plot("Optimized","-")

# Compare S21 of all available networks to the currently selected one
(nws().s(2,1) / sel_nws().s(2,1)).plot()
```
