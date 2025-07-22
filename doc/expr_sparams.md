SParams Class
=============


The `SParams` class is a container for one or more S-parameters, or X-/Y-data in general.

To get an `SParams` object, call `s()` on a `Networks` object.

Just like with the `Networks` class, any operation on the object may, by design, fail silently.

[See here](./expr_sparams.md) for a list of supported methods and operations.



## Methods


### plot()

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



### db()

```python
db() → SParams
```

Returns $20 \cdot \log_{10} S$.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db().plot()
```



### db20()

```python
db20() → SParams
```

Same as `db20()`.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db20().plot()
```



### db10()

```python
db10() → SParams
```

Returns $10 \cdot \log_{10}S$.

Plot this on a *linear* scale (otherwise the logarithm is applied *twice*).

Example:
```python
sel_nws().s().db10().plot()  # note that db10() will scale S-parameters, which are voltage-waves, incorrectly!
```



### ml()

```python
ml() → SParams
```

Mismatch loss: returns $1-|S²|$.

Plot this on a *dB-scale*, or use the `db()` function.

Example:
```python
sel_nws().s(11).ml().plot()
```



### vswr()

```python
vswr() → SParams
```

Voltage Standing Wave Ratio: returns $(1+|S²|)/(1-|S²|)$.

Plot this on a *linear* scale.

Example:
```python
sel_nws().s(11).vswr().plot()
```



### abs()

```python
abs() → SParams
```

Returns $|S|$.

Example:
```python
sel_nws().s(11).abs().plot()
```



### phase()

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



### crop_f()

```python
crop_f(f_start=-inf, f_end=+inf) → SParams.
```

Returns the same S-Param, but with a reduced frequency range.

Example:
```python
sel_nws().s(11).crop_f(f_end=2e9).plot()
```



### norm()

```python
norm(at_f: float, method='div') → SParams
```

Normalizes the parameter to its value at the given frequency.

When `method='div'` (the default), all other frequencies are normalized by dividing their value by the value at the given frequency. When `method='sub"`, all other frequencies are normalized by subtracting their value from the value at the given frequency.

Example:
```python
sel_nws().sel_params().norm(1e9).plot()  # normalize all traces to the 1 GHz-point
```



### min()

```python
min() → SParams.
```

Returns the minimum value (per frequency) of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid. If the input data has complex data type, the absolute is taken first.

Example:
```python
sel_nws().sel_params().abs().min().plot()
```



### max()

```python
max() → SParams.
```

Returns the maximum value (per frequency) of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid. If the input data has complex data type, the absolute is taken first.

Example:
```python
sel_nws().sel_params().abs().max().plot()
```



### mean()

```python
mean() → SParams.
```

Returns the arithmetic mean of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().mean().plot()
```



### median()

```python
median() → SParams.
```

Returns the median of multiple S-parameters. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().median().plot()
```



### sdev()

```python
sdev(ddof=1) → SParams.
```

Returns the standard deviation of multiple S-parameters. The paraemter `ddof` is the delta degrees of freedom which is handed into NumPy's `std()` function. Applies `interpolate()` first, to get a common frequency grid.

Example:
```python
sel_nws().sel_params().sdev().plot()
```



### rsdev()

```python
rsdev(quantiles=50) → SParams.
```

Returns the robust standard deviation of multiple S-parameters, by calculating the inter-quantile range (IQR), and comparing it to the IQR of a normal distribution. If the input data has complex data type, the absolute is taken first. Applies `interpolate()` first, to get a common frequency grid.

The parameter `quantiles` can be:

* A tuple of percentages, e.g. `(25,75)` to get the 25%..75% IQR.
* A single percentages, e.g. `50` to get the 25%..75% IQR.

Example:
```python
sel_nws().sel_params().abs().rsdev().plot()
```



### interpolate_lin()

```python
interpolate_lin(f_start: float=None, f_end: float=None, n: int=None) → SParams.
```

Interpolates all S-parameters to have the same, equidistant frequency grid.

The frequency range can be provided with `f_start` and `f_end`; otherwise, the maximum range of all parameters is used. The number of points can be provided with `n`; otherwise the mean of all parameters are used.

Example:
```python
sel_nws().sel_params().interpolate_lin(0, 10e9, 301).plot()
```



### interpolate_log()

```python
interpolate_log(f_start: float, f_end: float, n: int) → SParams.
```

Same as `interpolate_lin()`, but with a logarithmic frequency grid.

Example:
```python
sel_nws().sel_params().interpolate_log(1, 10e9, 301).plot()
```



### interpolate()

```python
interpolate(f_start: float=None, f_end: float=None, n: int=None) → SParams.
```

Same as `interpolate_lin()`.

Example:
```python
sel_nws().sel_params().interpolate(0, 10e9, 301).plot()
```



### map()

```python
map(fn: callable) → SParams.
```

Applies an arbitrary function to each S-parameter. The function `fn` is called for each S-parameter (`numpy.ndarray`) individually.

Example:

```python
sel_nws().sel_params().map(lambda s: s**2).plot()  # squares the linear S-parameters
```



### rename()

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



## Unary Operators

### Inversion

```python
~
```

Returns the inverse (i.e. $1/S$).

```python
(~(sel_nws().s(11))).plot()
```



## Binary Operators


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
