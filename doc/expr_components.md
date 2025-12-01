Components Class
================


The [global object](./expressions.md) `Comp` gives acces to a set of `ParametricNetwork` classes, which describe parametric networks.

Example:
```python
(sel_nws() ** Comp.Line(len=0.1)).plot_sel_params()  # adds a 10 cm line after the selected network, and plots it; i.e. 1--sel_nws---Line--2
(Comp.CShunt(1e-12) ** sel_nws()).plot_sel_params()  # adds a 1 pF shunt capacitor before the selected network, and plots it; i.e. 1--CShunt--sel_nws--2
```

The S-parameters of a `ParametricNetwork` object are calculated ad-hoc, depending on the required frequency grid and reference impedance. As soon as a `ParametricNetwork` is combined with a regular network (i.e. a network from a file), its S-parameters of the `ParametricNetwork` are calculated based on the frequency grid and the reference impedance of that network.

Consider this example:
```python
(nw("amp.s2p") ** Comp.Line(len=0.1)).plot_sel_params()  # 1--amp.s2p---Line--2
```
The file "amp.s2p" comes from a file, and thus has a frequeny grid and a reference impedance defined. As soon as the `**` operator is executed, the frequency grid and reference impdance of "amp.s2p" is used to dynamically calculate the S-parameters for the 10 cm matched transmission line.

One caveat are multiple cascaded parametric networks; consider this example (copied from [here](expressions.md)):
```python
((nws("amp.s2p") ** Comp.CShunt(400e-15)) ** Comp.Line(delay=1e-9)).s(1,1).plot("Optimized","-")
```
Note the extra parentheses around `(nws("amp.s2p") ** Comp.CShunt(400e-15))`. This is to ensure that `Comp.Shunt(...)` cascaded with `nws("amp.s2p")` (and thus inherits its frequency scale and impedance), then the result is cascaded with ` Comp.Line(...)` (which in turn inherits the same frequency scale and impedance).


## Classes

### Comp.RSer

```python
Comp.RSer(r) -> ParametricNetwork
```

Creates a series resistance, i.e. a 2-port with a resistor from port 1 to port 2.

Example:
```python
sel_nws() ** Comp.RSer(10)  # adds a 10 Ω series resistance after the network, i.e. 1--sel_nws---RSer--2
```

### Comp.RShunt

```python
Comp.RShunt(r) -> ParametricNetwork
```

Creates a shunt resistance, i.e. a 2-port with a resistor across the terminals (shorted to GND).

Example:
```python
sel_nws() ** Comp.RShunt(10)  # adds a 10 Ω shunt resistance after the network, i.e. 1--sel_nws---RShunt--2
```

Note that `Comp.RShunt(...)` is equivalent to `Comp.RSer(...).shunt()`.


### Comp.LSer

```python
Comp.LSer(l) -> ParametricNetwork
```

Creates a series inductance, i.e. a 2-port with am inductor from port 1 to port 2.

Example:
```python
sel_nws() ** Comp.LSer(1e-9)  # adds a 1 nH series inductance after the network, i.e. 1--sel_nws---LSer--2
```


### Comp.LShunt

```python
Comp.LShunt(l) -> ParametricNetwork
```

Creates a series inductance, i.e. a 2-port with am inductor across the terminals (shorted to GND).

Example:
```python
sel_nws() ** Comp.LShunt(1e-9)  # adds a 1 nH shunt inductance after the network, i.e. 1--sel_nws---LShunt--2
```

Note that `Comp.LShunt(...)` is equivalent to `Comp.LSer(...).shunt()`.


### Comp.CSer

```python
Comp.CSer(l) -> ParametricNetwork
```

Creates a series capacitance, i.e. a 2-port with am capacitor from port 1 to port 2.

Example:
```python
sel_nws() ** Comp.CSer(1e-12)  # adds a 1pF series capacitor after the network, i.e. 1--sel_nws---CSer--2
```


### Comp.CShunt

```python
Comp.CShunt(l) -> ParametricNetwork
```

Creates a series capacitance, i.e. a 2-port with am capacitor across the terminals (shorted to GND).

Example:
```python
sel_nws() ** Comp.CShunt(1e-12)  # adds a 1 pF shunt capacitor after the network, i.e. 1--sel_nws---CShunt--2
```

Note that `Comp.CShunt(...)` is equivalent to `Comp.CSer(...).shunt()`.



### Comp.Line

```python
Comp.Line(z, c_m, l_m, r_m, g_m, len, eps_r, delay, deg, at_f, db, db_m_mhz, db_m_sqmhz) -> ParametricNetwork
```

Creates a transmission line. There are varios ways to define the transmission line characteristics:
- Via length:
    - `len`: length in meters
    - `z`: impedance in Ω (default: matched)
    - `eps_r`: dielectric constant εr (default: `eps_r=1`)
- Via delay: 
    - `delay`: delay in seconds; line length is derived from this
    - `z`: impedance in Ω (default: matched)
    - `eps_r`: dielectric constant εr (default: `eps_r=1`)
- Via phase-shift: 
    - `deg`: phase shift in degrees; line length is derived from this
    - `at_f`: the frequency, in Hz, at which the phase shift is defined
    - `z`: impedance in Ω (default: matched)
    - `eps_r`: dielectric constant εr (default: `eps_r=1`)
- Via material constants: 
    - `c_m`: distribted capacitance, in Farads per meter
    - `l_m`: distribted inductance, in Henries per meter
    - `r_m`: distribted resistance, in Ohms per meter (default: `r_m=0`)
    - `g_m`: distribted conductance, in Siemens per meter (default: `g_m=0`)

In all cases, *except* for the material constants, attenuation can also be defined (note that loss is given in positive dB values):
- either in decibels:
    - `db`: constant (frequency-independent) attenuation in dB (default: `db=0`)
    - `db_m_mhz`: attenuation in dB per meter per MHz (default: `db_m_mhz=0`)
    - `db_m_sqmhz`: attenuation in dB per meter per square-root of MHz (default: `db_m_sqmhz=0`)
- or as dissipation factor:
    - `df`: dissipation factor (default: `df=0`)

Examples:
```python
sel_nws() ** Comp.Line(len=1)  # adds a 1 m matched, lossless transmission line after the network (assume εr = 1), i.e. 1--sel_nws---Line--2
sel_nws() ** Comp.Line(len=0.3,eps_r=3.4,df=1e-3,z=75)  # adds a 30 cm, 75 Ω, lossy transmission line after the network, with εr = 3.4 and df=0.001, i.e. 1--sel_nws---Line--2
sel_nws() ** Comp.Line(deg=360,at_f=1e9)  # adds a matched, lossless transmission line after the network, which adds 360° phase shift at 1 GHz, i.e. 1--sel_nws---Line--2
sel_nws() ** Comp.Line(delay=1e-9)  # adds a matched, lossless transmission line after the network, which adds 1 ns of delay, i.e. 1--sel_nws---Line--2
Comp.Line(deg=90,at_f=10e9) ** sel_nws()  # adds a matched, lossless λ/4 (at 10 GHz) line before the network, i.e. 1--Line---sel_nws--2
```



### Comp.LineShunt

```python
Comp.LineShunt(..., stub_gamma=-1) -> ParametricNetwork
```

Same as `Comp.Line(...)`, except that this line is connected as a shunt stub.

The stub is terminated with the reflection coefficient `stub_gamma`; use e.g. `stub_gamma=-1` for an open shunt stub, or `stub_gamma=+1` for a shorted shunt stub.

Example:
```python
sel_nws() ** Comp.LineShunt(deg=90,a_f=1e9)  # adds a shorted λ/4 (at 1 GHz) shunt stub before the network, i.e. 1--sel_nws---LineShunt--2
Comp.LineShunt(deg=90,a_f=1e9,gamma_stub=+1) ** sel_nws()  # adds an open λ/4 (at 1 GHz) shunt stub after the network, i.e. 1--LineShunt--sel_nws--2
```

Note that `Comp.LineShunt(..., stub_gamma=...)` is equivalent to `Comp.Line(...).shunt(gamma_term=...)`.



### Comp.Phase

```python
Comp.Phase(deg) -> ParametricNetwork
```

Creates a constant phase shifter (i.e. phase shift is regardless of frequency).

Example:
```python
sel_nws() ** Comp.Phase(90)  # shifts the phase at the output port by 90°, i.e. 1--sel_nws---+90°--2
```



### Comp.Thru

```python
Comp.Thru() -> ParametricNetwork
```

Creates an ideal thru.

Cascading this component has no effect, so it can be used as a placeholder.

Example:
```python
sel_nws() ** Comp.Thru()  # no effect, i.e. 1--sel_nws---Thru--2, which is identical to 1--sel_nws--2
```



### Comp.Iso

```python
Comp.Iso(reverse=False) -> ParametricNetwork
```

Creates an ideal 2-port isolator.

Example:
```python
sel_nws() ** Comp.Iso()  # add an ideal isolator after the network, i.e. 1--sel_nws---Iso--2
Comp.Iso(reverse=True) ** sel_nws()  # add an ideal reverse isolator before the network, i.e. 1--Iso---sel_nws--2
```



### Comp.Term

```python
Comp.Term(gamma, z) -> ParametricNetwork
```

Creates an ideal 2-port termination, defined *either* by reflection coefficient Γ, *or* by impedance Z (default: `gamma=0`, i.e. matched load).

Example:
```python
sel_nws() ** Comp.Term()  # terminate network at port 2 with a matched load, i.e. 1--sel_nws---Term--2 (note that port 2 is then perfectly matched as well)
sel_nws() ** Comp.Term(gamma=+1)  # terminate network at port 2 with an open (Γ = +1), i.e. 1--sel_nws---Open--2 (note that port 2 is then open-terminated as well)
Comp.Term(z=0) ** sel_nws()  # short network at port 1 (Z = 0 Ω), i.e. 1--sel_nws---Short--2 (note that port 2 is then shorted as well)
```
