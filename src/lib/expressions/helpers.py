import dataclasses



@dataclasses.dataclass
class DefaultAction:
    s_args: list
    s_kwargs: dict
    plot_args: list
    plot_kwargs: dict



def format_call_signature(fn, *args, **kwargs) -> str:
    all_args = [
        *[f'{v}' for v in args],
        *[f'{k}={v}' for k,v in kwargs.items()],
    ]
    args_str = ','.join(all_args)
    return f'{fn.__name__}({args_str})'
