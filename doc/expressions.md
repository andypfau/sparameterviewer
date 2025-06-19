# Expressions


Basics
------

The basic concept is to load one (`nw(name)`) or multiple (`nws()`) networks, get a specific S-parameter (`s(i,j)`), and plot it (`plot()`):

```python
    nws("*amp.s2p").s(21).plot("IL")
```

Which could be re-written as:

```python
    n: Networks = nws("*amp.s2p")
    s: SParams = n.s(21)
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

If no pattern is provided, returns a `Networks` object that contains *all available* networks in the Filesystem Browser.

If a pattern is provided, returns a `Networks` object that contains all networks that match the given pattern, e.g. `'*.s2p'`. Note that this returns an empty `Networks` object if the pattern does not match anything (instead of raising an error).


### sel_nws()

```python
sel_nws(pattern=None)
```

Same as `nws()`, except that it only matches networks that are *currently selected* in the Filesystem Browser.


### nw()

```python
nw(pattern=None)
```

Same as `nws()`, except that it selects *exactly one* network. Throws an error if zero or more than one network is matched.


### saved_nw()

```python
saved_nw()
```

Returns a `Networks` object with the network that was saved from the Filesystem Browser's context menu.



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

Plots the parameters of the networks, according to the parameter selector in the main window.

Example:
```python
nw("amp.s2p").plot_sel_params()  # you can use the Parameter Selector to choose which parameters to plot
```


##### sel_params()

```python
sel_params()
```

Returns the S-parameters (an `SParams` object) of a network, according to the parameter selector in the main window.

Example:
```python
nw("amp.s2p").sel_params().plot(color="gray")  # you can use the Parameter Selector to choose which parameters to plot
```


##### s(), z(), y(), abcd(), t()

```python
s(ports = None, *, rl_only=False, il_only=False, fwd_il_only=False, rev_il_only=False, name=None) → SParams
s(egress_port=None, ingress_port=None, *, rl_only=False, il_only=False, fwd_il_only=False, rev_il_only=False, name=None) → SParams
```

Returns S-parameters (an `SParams` object) of a network.

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
sel_nws().s(2,1).plot()                 # S21
sel_nws().s(21).plot()                  # S21
sel_nws().s("21").plot()                # S21
sel_nws().s("2,1").plot()               # S21
sel_nws().s("dd21").plot()              # SDD21; only works on mixed-mode file
sel_nws().s(rl_only=True).plot()        # S11, S22, S33, ...
sel_nws().s(any, 1).plot()              # S11, S21, S31, ...
sel_nws().s(3,any,il_only=True).plot()  # S31, S32, ...
```

##### z(), y(), abcd(), t()

Similar as `s()`, but instead of S-parameters:
- `z()` returns the Z-matrix parameters,
- `y()` returns the Y-matrix parameters,
- `abcd()` returns the ABCD-matrix parameters,
- `t()` returns the T-matrix (scattering transfer) parameters,

Examples:
```python
sel_nws().z(2,1).plot()
```


##### invert()

```python
invert() → Networks
```

Inverts the network. Useful for de-embedding.

Example:
```python
lpf, bpf = nw("lpf.s2p"), nw("bpf.s2p")
casc = lpf ** bpf  # create a cascade of lpf and bpf
deemb = lpf.invert() ** casc  # now de-embed the lpf from the cascade; now deemb should equal bpf

bpf.s(21).plot("Original", style=':')
casc.s(21).plot("Cascade")
deemb.s(21).plot("De-Embedded", style='--')
```

An alternative to `invert()` is the `~` operator.


##### flip()

```python
flip() → Networks
```

Flips the ports (e.g. to use it in reverse direction).

Example:
```python
nw("amp.s2p").flip().s(21).plot()
```


##### half()

```python
half(method='IEEE370NZC', side=1) → Networks
```

Chops the network in half; intended for 2xTHRU de-embedding.

Allowed methods are `'IEEE370NZC'` (IEEE-370, no Z-compensation), or 'ChopInHalf'. For IEEE-370, an additional argument `side` may be provided, to return the left side (`1`) or the right side (`2`).

Example:
```python
thru, dut = nw("thru.s2p"), nw("thru.s2p")

# create a 2xTHRU fixture
thru_thru = thru ** (thru.flip())
thru1, thru2 = thru_thru.half(side=1), thru_thru.half(side=2)

# create a thru-DUT-thur fixture, then de-embed it again
thru_dut_thru = thru ** dut ** (thru.flip())
deemb = (~thru1) ** thru_dut_thru ** (~thru2)

dut.s(21).plot("DUT", style=':')
thru_dut_thru.s(21).plot("Thru-DUT-Thru")
deemb.s(21).plot("De-Embedded DUT", style='--')
```


##### k()

```python
k() → SParams
```

Returns the K (Rollet) stability factor. For a stable network, this should be >1 (or >0 dB).

Example:
```python
nw("amp.s2p").k().plot()
```

##### mu()

```python
mu(mu=1) → SParams
```

Returns the µ (mu=1, default) or µ' (mu=2) method stability factor (Edwards-Sinsky). For a stable network, this should be >1 (or >0 dB).

Example:
```python
nw("amp.s2p").mu(1).plot("µ")
nw("amp.s2p").mu(2).plot("µ'")
```


##### losslessness()

```python
losslessness(egress_port_or_kind,ingress_port=None) → SParams
```

Checks a network for losslessness. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T \cdot S^* = U$ (wher $U$ is the unit matrix). This function calculates, for each frequency, $|S^T \cdot S^* - U|$, and returns the highest value of that matrix.

Example:
```python
nw("lpf.s2p").losslessness().plot()
```


##### passivity()

```python
passivity() → SParams
```

Checks a network for passivity. For a reciprocal network, the result should be 0.

For a passive network, all eigenvalues $\lambda$ of the matrix $S^{T*} \cdot S$ should be $\lambda \le 1$. This function calculates, for each frequency, the eigenvalues, finds the highest eigenvalue $\lambda'$, and returns $max(0, \lambda'-1)$.

Example:
```python
nw("lpf.s2p").passivity().plot()
```

##### reciprocity()

```python
reciprocity() → SParams
```

Checks a network for reciprocity. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T = S$. This function calculates, for each frequency, $|S^T - S|$, and returns the highest value of that matrix.

Example:
```python
nw("lpf.s2p").reciprocity().plot()
```

##### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → Networks
```

Returns the same network, but with a reduced frequency range

Example:
```python
nw("lpf.s2p").crop_f(f_end=5e9).plot_sel_params()
```

##### add_sr()

```python
add_sr(resistance, port=1) → Networks
```

Returns a network with a series resistance attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_sr(10).plot_sel_params()  # add a 10 Ω series resistor on port 1
```

##### add_sl()

```python
add_sl(inductance, port=1) → Networks
```

Returns a network with a series inductance attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_sl(1e-9).plot_sel_params()  # add a 1 nH series inductor on port 1
```

##### add_sc()

```python
add_sc(capacitance, port=1) → Networks
```

Returns a network with a series inductance attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_sc(100e-9).plot_sel_params()  # add a 100 nF series capacitor on port 1
```

##### add_pr()

```python
add_pr(resistance, port=1) → Networks
```

Returns a network with a parallel resistance to GND (shunt), attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_pr(1e3).plot_sel_params()  # add a 1 kΩ shunt resistor on port 1
```

##### add_pl()

```python
add_pl(inductance, port=1) → Networks
```

Returns a network with a parallel inductance attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_pl(1e-6).plot_sel_params()  # add a 1 µH shunt inductor on port 1
```

##### add_pc()

```python
add_pc(capacitance, port=1) → Networks
```
Returns a network with a parallel inductance attached to the specified port. Works only for 1-ports and 2-ports.

Example:
```python
nw("lpf.s2p").add_pc(1e-12).plot_sel_params()  # add a 1 pF shunt capacitor on port 1
```

##### add_tl()

```python
add_tl(degrees, frequency_hz=1e9, z0=None, loss_db=0, port=1]) → Networks
```

Returns a network with anideal transmission line attached to the specified port. Works only for 1-ports and 2-ports.

The length is specified in degrees at the given frequency.

The loss is the real part of the propagation constant, and is constant over frequency.

If `z0` is not provided, the reference impedance of the corresponding port is used.

Example:
```python
nw("lpf.s2p").add_tl(360).plot_sel_params()  # add a 360° line on port 1
```

##### add_ltl()

```python
add_ltl(len_m, eps_r, db_m_mhz=0, db_m_sqmhz=0, port=1) → Networks
```

Returns a network with a lossy transmission line attached to the specified port. Works only for 1-ports and 2-ports.

The length is specified in meters, and the dielectric constant must be provided as well.

The loss is specified in two terms, one in dB/(m⋅Hz), one in dB/(m⋅√Hz).

If `z0` is not provided, the reference impedance of the corresponding port is used.

Example:
```python
nw("lpf.s2p").add_ltl(0.2, 4, 1e-3, 1e-3).plot_sel_params()  # add a 20 cm line on port 1
```


##### plot_stab()

```python
plot_stab(frequency_hz, port=2, n_points=101, label=None, style='-')
```

Plots the stability circle at the given frequency.

Set `port=1` if you want to calculate the stability at the input, otherwise the output is calculated.

It adds "s.i." (stable inside circle) or "s.o." (stable outside of the circle) to the plot name.

Example:
```python
nw("amp.s2p").plot_stab(10e9)  # use the Smith chart to plot this!
```

##### s2m()

```python
s2m(ports):
```

Single-ended to mixed-mode conversion.

The expected port order for the single-ended network is <pos1, neg1, pos2, neg2, ...>.

You may define your own mapping; e.g. if your data is <pos1, pos2, neg1, neg2>, you can provide the argument `["p1","p2","n1","n2"]`. Alternatively, you can provide the argument as a single string `"p1,p2,n1,n2"`.

The generated mixed-mode network has port order <diff1, diff2, ..., comm1, comm2, ...>.

Example:
```python
amp_se = nw("diff_amp.s4p")
amp_mx = amp_se.s2m("P1,P2,N1,N2")  # the single-ended ports are: positive 1, positive 2, negative 1, positive 2
amp_mx.s("DD21").plot()  # plot SDD21
```


##### m2s()

```python
m2s([inp=<ports>][, outp=<ports>]):
```

Mixed-mode to single-ended conversion.

The expected port order for the single-ended network is <diff1, diff2, ..., comm1, comm_2, ..>.

You may define your own mapping; e.g. if your data is <diff1, diff2, comm1, comm2>, you can provide the argument `["d1","d2","c1","c2"]`. Alternatively, you can provide the argument as a single string `"d1,d2,c1,c2"`.

The generated mixed-mode network has port order <pos1, neg1, pos2, neg2, ...>.

Example:
```python
amp_se = nw("diff_amp.s4p")
amp_mx = amp_se.s2m("P1,P2,N1,N2")  # see example of s2m()
amp_se2 = amp_mx.m2s("D1,D2,C1,C2")  # he diff. ports are: diff. 1, diff. 2, CM 1, CM 2
amp_se2.s(21).plot()  # plot SDD21
```


##### renorm()

```python
renorm(z)
```

Renormalize to a specific reference impedance. <z> can be a scalar, or a list of scalars (one per port).

Example:
```python
balun = nw("balun21.s4p")
balun = balun.renorm([50,50,100,100])
balun.plot_sel_params()
```

##### rewire()

```python
rewire(ports: list[int])
```

Re-wires a network. The argument is the list of ports to keep.

Examples:
```python
nw('amp.s2p').rewire([2,1]).plot_sel_params()  # swap ports of a 2-port
nw('bpf.s2p').rewire([1]).plot_sel_params()  # only keep port 1 (port 2 is terminated)
```


##### quick()

```python
quick(quick(parameter[, parameter...]))
```

Does the same as the global `quick()` function, see section above.

Example:
```python
nw('bpf.s2p').quick(21)
```

#### Unary Operators

##### Inversion

```python
~
```

Inverts the network. Useful for de-embedding.

Example:
```python
lpf, bpf = nw("lpf.s2p"), nw("bpf.s2p")
casc = lpf ** bpf  # create a cascade of lpf and bpf
deemb = (~lpf) ** casc  # now de-embed the lpf from the cascade; now deemb should equal bpf

bpf.s(21).plot("Original", style=':')
casc.s(21).plot("Cascade")
deemb.s(21).plot("De-Embedded", style='--')
```

An alternative to the `~` operator is the `invert()` method.


#### Binary Operators

##### Addition, Subtraction, Multiplication, Division

```python
+ - * /
```

Applies the operation on the parameters of two networks.

Example:
```python
(sel_nws() / nw("thru.s2p")).s().plot()  # normalize all networks to thru.s2p, then plot S-parameters
```

**Note**: a division is *not* the same as de-embedding! To de-embed `thru.s2p`, use `sel_nws() ** (~nw("thru.s2p"))`.



##### Cascade

```python
**
```

Cascades two networks. Frequency grids are interpolated accordingly.

Example:
```python
(sel_nws() ** nw("thru.s2p")).plot_sel_params()  # cascade thru.s2p to selected networks, then plot S-parameters
```


### SParams

A container for one or more S-parameters, or X-/Y-data in general.

To get an `SParams` object, call `s()` on a `Networks` object.

Just like with the `Networks` class, any operation on the object may, by design, fail silently.


#### Methods


##### plot()

```python
plot(label=None, style='-', color=None, width=None, opacity=None)
```

Plots the data. `label` is any string. The placeholder `"$NAME"` is replaced with the name of the parameter.

`style` is a [matplotlib](https://matplotlib.org/stable/users)-compatible format (e.g. `"-"`, `":"`, `"--"`, `"o-"`).

`color` is a [matplotlib](https://matplotlib.org/stable/users)-compatible color (e.g. `"red"`, `"#FF0000"`, `"F00"`).

`width` is the line width, `opacity` is the line opacity (where 0 means fully invisible, and 1 means fully visible).

Example:
```python
sel_nws().s().plot(label="$NAME Plot")
```

##### db()

```python
db() → SParams
```

Returns $20 \cdot \log_{10} S$.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db().plot()
```


##### db20()

```python
db20() → SParams
```

Same as `db20()`.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db20().plot()
```


##### db10()

```python
db10() → SParams
```

Returns $10 \cdot \log_{10}S$.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db10().plot()  # note that db10() will scale S-parameters, which are voltage-waves, incorrectly!
```


##### ml()

```python
ml() → SParams
```

Mismatch loss: returns $1-|S²|$.

Plot this on a *dB-scale*, or use the `db()` function.

Example:
```python
sel_nws().s(11).ml().plot()
```

##### vswr()

```python
vswr() → SParams
```

Voltage Standing Wave Ratio: returns $(1+|S²|)/(1-|S²|)$.

Plot this on a *linear* scale.

Example:
```python
sel_nws().s(11).vswr().plot()
```


##### abs()

```python
abs() → SParams
```

Returns $|S|$.

Example:
```python
sel_nws().s(11).abs().plot()
```


##### phase()

```python
phase(processing=None) → SParams
```

Returns the phase.

`processing` can be `None`, `'unwrap'` (unwrap phase), or `'remove_linear'` (unwrap, then remove linear phase).

Plot this on a *linear* scale.

Example:
```python
sel_nws().s(11).phase('unwrap').plot()
```


##### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → SParams.
```

Returns the same S-Param, but with a reduced frequency range.

Example:
```python
sel_nws().s(11).crop_f(f_end=2e9).plot()
```

##### norm()

```python
norm(at_f: float, method='div') → SParams
```

Normalizes the parameter to its value at the given frequency.

When `method='div'` (the default), all other frequencies are normalized by dividing their value by the value at the given frequency. When `method='sub"`, all other frequencies are normalized by subtracting their value from the value at the given frequency.

Example:
```python
sel_nws().sel_params().norm(1e9).plot()  # normalize all traces to the 1 GHz-point
```

##### mean()

```python
mean() → SParams.
```

Returns the arithmetic mean of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().mean().plot()
```

##### median()

```python
median() → SParams.
```

Returns the median of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().median().plot()
```

##### sdev()

```python
sdev(ddof=1) → SParams.
```

Returns the standard deviation of multiple S-parameters. The paraemter `ddof` is the delta degrees of freedom which is handed into NumPy's `std()` function. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().sdev().plot()
```

##### interpolate_lin()

```python
interpolate_lin(f_start: float=None, f_end: float=None, n: int=None) → SParams.
```

Interpolates all S-parameters to have the same, equidistant frequency grid.

The frequency range can be provided with `f_start` and `f_end`; otherwise, the maximum range of all parameters is used. The number of points can be provided with `n`; otherwise the mean of all parameters are used.

Example:
```python
sel_nws().sel_params().interpolate_lin(0, 10e9, 301).plot()
```

##### interpolate_log()

```python
interpolate_log(f_start: float, f_end: float, n: int) → SParams.
```

Same as `interpolate_lin()`, but with a logarithmic frequency grid.

Example:
```python
sel_nws().sel_params().interpolate_log(1, 10e9, 301).plot()
```

##### interpolate()

```python
interpolate(f_start: float=None, f_end: float=None, n: int=None) → SParams.
```

Same as `interpolate_lin()`.

Example:
```python
sel_nws().sel_params().interpolate(0, 10e9, 301).plot()
```


##### map()

```python
map(fn: callable) → SParams.
```

Applies an arbitrary function to each S-parameter. The function `fn` is called for each S-parameter (`numpy.ndarray`) individually.

Example:

```python
sel_nws().sel_params().map(lambda s: s**2).plot()  # squares the linear S-parameters
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
sel_nws().sel_params().rename(prefix='Gain of ').plot()
```


#### Unary Operators


##### Inversion

```python
~
```

Returns the inverse (i.e. $1/S$).

```python
(~(sel_nws().s(11))).plot()
```

#### Binary Operators


```python
+ - * /
```
Applies the corresponding mathematical operator. Each operand can also be a numeric constant.

```python
# normalize all to the network that was saved in the Filesystem Browser
(sel_nws().sel_params() / saved_nw().sel_params()).plot()

# alternative approach:
(sel_nws() / saved_nw()).sel_params().plot()
```

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
