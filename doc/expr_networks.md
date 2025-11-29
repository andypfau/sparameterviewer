Networks Class
==============



The `Networks` class is a container for one or more S-parameter networks (i.e. files).

To get a `Networks` object, call the [global functions](./expressions.ms) `nws()`, `sel_nws()` or `nw()`.

Note that any operation on the object may, by design, fail silently. For example, if an object contains a 1-port and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports), the 1-port will silently be dropped. This is to avoid excessive errors when applying general expressions on a large set of networks.



## Methods

### plot_sel_params()

```python
plot_sel_params()
```

Plots the parameters of the networks, according to the parameter selector in the main window.

Example:
```python
nw("amp.s2p").plot_sel_params()  # you can use the Parameter Selector to choose which parameters to plot
```



### sel_params()

```python
sel_params()
```

Returns the S-parameters (an `SParams` object) of a network, according to the parameter selector in the main window.

Example:
```python
nw("amp.s2p").sel_params().plot(color="gray")  # you can use the Parameter Selector to choose which parameters to plot
```



### s(), z(), y(), abcd(), t()

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



### z(), y(), abcd(), t()

Similar as `s()`, but instead of S-parameters:
- `z()` returns the Z-matrix parameters,
- `y()` returns the Y-matrix parameters,
- `abcd()` returns the ABCD-matrix parameters,
- `t()` returns the T-matrix (scattering transfer) parameters,

Examples:
```python
sel_nws().z(2,1).plot()
```



### invert()

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



### flip()

```python
flip() → Networks
```

Flips the ports (e.g. to use it in reverse direction).

Example:
```python
nw("amp.s2p").flip().s(21).plot()
```



### half()

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



### k()

```python
k() → SParams
```

Returns the K (Rollet) stability factor. For a stable network, this should be >1 (or >0 dB).

Example:
```python
nw("amp.s2p").k().plot()
```



### mu()

```python
mu(mu=1) → SParams
```

Returns the µ (mu=1, default) or µ' (mu=2) method stability factor (Edwards-Sinsky). For a stable network, this should be >1 (or >0 dB).

Example:
```python
nw("amp.s2p").mu(1).plot("µ")
nw("amp.s2p").mu(2).plot("µ'")
```



### mag()

```python
mag() → SParams
```

Returns the maximum available power gain.

Example:
```python
nw("amp.s2p").mag().plot()
```



### msg()

```python
msg() → SParams
```

Returns the maximum stable power gain.

Example:
```python
nw("amp.s2p").msg().plot()
```



### u()

```python
u() → SParams
```

Returns Mason's unilateral gain.

Example:
```python
nw("amp.s2p").u().plot()
```



### losslessness()

```python
losslessness(egress_port_or_kind,ingress_port=None) → SParams
```

Checks a network for losslessness. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T \cdot S^* = U$ (wher $U$ is the unit matrix). This function calculates, for each frequency, $|S^T \cdot S^* - U|$, and returns the highest value of that matrix.

Example:
```python
nw("lpf.s2p").losslessness().plot()
```



### passivity()

```python
passivity() → SParams
```

Checks a network for passivity. For a reciprocal network, the result should be 0.

For a passive network, all eigenvalues $\lambda$ of the matrix $S^{T*} \cdot S$ should be $\lambda \le 1$. This function calculates, for each frequency, the eigenvalues, finds the highest eigenvalue $\lambda'$, and returns $max(0, \lambda'-1)$.

Example:
```python
nw("lpf.s2p").passivity().plot()
```



### reciprocity()

```python
reciprocity() → SParams
```

Checks a network for reciprocity. For a reciprocal network, the result should be 0.

For a reciprocal network, $S^T = S$. This function calculates, for each frequency, $|S^T - S|$, and returns the highest value of that matrix.

Example:
```python
nw("lpf.s2p").reciprocity().plot()
```



### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → Networks
```

Returns the same network, but with a reduced frequency range

Example:
```python
nw("lpf.s2p").crop_f(f_end=5e9).plot_sel_params()
```



### shunt()

```python
shunt(gamma_term=-1) → Networks
```

Calculates a new 2-port network, which represents a shunted version of the original network. Example usages:
- Take the S-parameters of a series impedance, and turn it into a shunt impedance (with `gamma_term=-1`, which represents a short to GND).
- Take the S-parameters of a transmission line, and turn it into a shorted stub (with `gamma_term=-1`, which represents a short to GND).
- Take the S-parameters of a transmission line, and turn it into an open stub (with `gamma_term=+1`, which represents an open).

Examples:
```python
nw("thru.s2p").shunt().plot_sel_params()  # turn that thru into a shorted stub
```



### plot_stab()

```python
plot_stab(f=None, n=None, port=2, n_points=101, label=None, style='-')
```

Plots the stability circles of a network. You can either specifcy:
- the freuqency of the circle you want to plot, with `f=...`, or
- the number of circle you want to plot, with `n=...` (then `n` equidistant frequency samples are plotted)

Set `port=1` if you want to calculate the stability at the input, otherwise the output is calculated.

The functions adds the frequency, and "s.i." (stable inside of the circle) or "s.o." (stable outside of the circle) to the plot label.

You can also provide the argument `n_points=...`, which defines how many graph points are used to represent the circle.

Example:
```python
nw("amp.s2p").plot_stab(n=10)  # use the Smith chart to plot this!
```



### s2m()

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



### m2s()

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



### renorm()

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



### rewire()

```python
rewire(ports: list[int])
```

Re-wires a network. The argument is the list of ports to keep.

Examples:
```python
nw('amp.s2p').rewire([2,1]).plot_sel_params()  # swap ports of a 2-port
nw('bpf.s2p').rewire([1]).plot_sel_params()  # only keep port 1 (port 2 is terminated)
```



### quick()

```python
quick(quick(parameter[, parameter...]))
```

Does the same as the global `quick()` function, see section above.

Example:
```python
nw('bpf.s2p').quick(21)
```



## Unary Operators

### Inversion

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



## Binary Operators

### Addition, Subtraction, Multiplication, Division

```python
+ - * @ /
```

Applies the operation on the parameters of two networks.

Note that `+ - * /` are element-wise operations, while `@` is the matrix multiplication.

Example:
```python
(sel_nws() / nw("thru.s2p")).s().plot()  # normalize all networks to thru.s2p, then plot S-parameters
```

**Notes**:

- A matrix multiplication is *not* the same as cascading! To cascade e.g. `thru.s2p`, use `sel_nws() ** nw("thru.s2p")`.
- A division is *not* the same as de-embedding! To de-embed e.g. `thru.s2p`, use `sel_nws() ** (~nw("thru.s2p"))`.



### Cascade

```python
**
```

Cascades two networks. Frequency grids are interpolated accordingly.

Example:
```python
(sel_nws() ** nw("thru.s2p")).plot_sel_params()  # cascade thru.s2p to selected networks, then plot S-parameters
```
