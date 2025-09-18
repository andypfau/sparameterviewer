# Expressions

Preface
-------

Expressions are intended to unlock possibilities and flexibility of S-parameter handling that would be uuneccessarily complex with a GUI.

The majority of the functionality offered by expressions can easily be accessed using the "Template"-Button in the "Expressions" tab. The generatred expressions can then be modified to adapt to any need.



Basics
------

The basic concept is to load one (`nw("name")`) or multiple (`nws()`) networks, get a specific S-parameter (`s(i,j)`), and plot it (`plot()`):

```python
    nws("*amp.s2p").s(21).plot("IL")  # plot S21 of all files that match "*amp.s2p"
```

Which could be re-written as:

```python
    n: Networks = nws("*amp.s2p")  # get all files that match "*amp.s2p"
    s: SParams = n.s(21)           # get S21
    s.plot("IL")                   # plot S21
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


### map()

```python
map(fn, sparams, f_arg=False)
```

Maps `SParams` objects using a user-defined function `fn`.

If `f_arg=True`, the first argument handed to `fn` is the frequency (as `np.ndarray`), and all subsequent arguments are the S-parameters of each `sparams` argument (as `np.ndarray`). The S-parameters are interpolated to all have the same freuqencies. If `f_arg=False` (default), the frequency argument is omitted.

If the items of `sparams` have different numbers of elements, all items with only a single element are repeated. If there are different numbers of elements that are not one, an error occurs. Example:
- `map(fn, three_elements, three_elements)`: `fn()` is called 3x, with `three_elements[0],three_elements[0]`, `three_elements[1],three_elements[1]`, `three_elements[2],three_elements[2]`.
- `map(fn, three_elements, one_element)`: `fn()` is called 3x, with `three_elements[0],one_element`, `three_elements[1],one_element`, `three_elements[2],one_element`.
- `map(fn, three_elements, two_elements)`: fails.

Example:
```python
def my_fn(s, ref_s):
    return s / ref_s  # normalization

map(my_fn, sel_nws(), saved_nw())
```



Classes
-------

- `Networks`: a container for one or more RF networks.
- `SParams`: a container for one or more S-parameters, or X-/Y-data in general.


### Networks

The `Networks` class is a container for one or more S-parameter networks (i.e. files).

To get a `Networks` object, call the global functions `nws()`, `sel_nws()` or `nw()`.

Note that any operation on the object may, by design, fail silently. For example, if an object contains a 1-port and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports), the 1-port will silently be dropped. This is to avoid excessive errors when applying general expressions on a large set of networks.

[See here](./expr_networks.md) for a list of supported methods and operations.



### SParams

The `SParams` class is a container for one or more S-parameters, or X-/Y-data in general.

To get an `SParams` object, call `s()` on a `Networks` object.

Just like with the `Networks` class, any operation on the object may, by design, fail silently.

[See here](./expr_sparams.md) for a list of supported methods and operations.



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
sel_nws().s(il_only=True).plot(color='blue')  # plot insertion losses in blue
sel_nws().s(rl_only=True).plot(color='red')   # plot return losses in red
```

See the documentation of [SParams.plot()](./expr_sparams.md) for more details.



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
