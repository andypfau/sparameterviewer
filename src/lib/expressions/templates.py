from __future__ import annotations
from dataclasses import dataclass

from ..settings import PlotType, YQuantity



@dataclass
class ExpressionTemplate:
    name: str
    snippets: list[str]
    plot_type: PlotType|None = None
    y_quantity: YQuantity|None = None
    need_ref: bool = False
    min_selected: int|None = None
    need_many_for_stat: bool = False

@dataclass
class ExpressionTemplateGroup:
    name: str
    templates: list[ExpressionTemplate|ExpressionTemplateGroup|None]


def get_expression_templates() -> list[ExpressionTemplate|ExpressionTemplateGroup|None]:
    return [
        ExpressionTemplate(
            'As Currently Selected',
            ['{*generated}'],
        ),
        None,
        ExpressionTemplateGroup(
            'S-Parameters',
            [
                ExpressionTemplate(
                    'All S-Parameters',
                    ['sel_nws().s().plot()  # all S-params'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'Insertion Loss',
                    ['sel_nws().s(il_only=True).plot()  # insertion loss'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'Insertion Loss (forward only)',
                    ['sel_nws().s(fwd_il_only=True).plot()  # insertion loss (forward only)'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'Return Loss',
                    ['sel_nws().s(rl_only=True).plot()  # return loss'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'VSWR',
                    ['sel_nws().s(rl_only=True).vswr().plot()  # voltage standing wave ratio'],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'Mismatch Loss',
                    ['sel_nws().s(rl_only=True).ml().plot()  # mismatch loss'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                None,
                ExpressionTemplate(
                    'S11',
                    ['quick(11)'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'S11, S21, S22',
                    ['quick(11)', 'quick(21)', 'quick(22)'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'S11, S21, S12, S22',
                    ['quick(11)', 'quick(21)', 'quick(12)', 'quick(22)'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'S11, S21, S22, S31, S32, S33',
                    ['quick(11)', 'quick(21)', 'quick(12)', 'quick(22)', 'quick(31)', 'quick(32)', 'quick(33)'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Other Parameters',
            [
                ExpressionTemplate(
                    'Z-Matrix (Impedance)',
                    ['sel_nws().z(any,any).plot()  # Z-parameters'],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'Y-Matrix (Admittance)',
                    ['sel_nws().y(any,any).plot()  # Y-parameters'],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'ABCD-Matrix (Cascade; 2-Port Only)',
                    ['sel_nws().abcd(any,any).plot()  # ABCD-parameters'],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'T-Matrix (Scattering Transfer; Even Port Numbers Only)',
                    ['sel_nws().t(any,any).plot()  # scattering transfer parameters'],
                    PlotType.Cartesian
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'General Network Analysis',
            [
                ExpressionTemplate(
                    'Reciprocity (2-Port or Higher Only)',
                    ['sel_nws().reciprocity().plot()  # should be 0 for reciprocal network'],
                    PlotType.Cartesian, YQuantity.Magnitude
                ),
                ExpressionTemplate(
                    'Symmmetry (2-Port or Higher Only)',
                    ['sel_nws().symmetry().plot()  # should be 0 for symmetric network'],
                    PlotType.Cartesian, YQuantity.Magnitude
                ),
                ExpressionTemplate(
                    'Passivity',
                    ['sel_nws().passivity().plot()  # should be 0 for passive network'],
                    PlotType.Cartesian, YQuantity.Magnitude
                ),
                ExpressionTemplate(
                    'Losslessness',
                    ['sel_nws().losslessness().plot()  # should be 0 for lossless network'],
                    PlotType.Cartesian, YQuantity.Magnitude
                ),
                None,
                ExpressionTemplate(
                    'All of Above',
                    [
                        'sel_nws().reciprocity().plot()   # should be 0 for reciprocal network',
                        'sel_nws().symmetry().plot()      # should be 0 for symmetric network',
                        'sel_nws().passivity().plot()     # should be 0 for passive network',
                        'sel_nws().losslessness().plot()  # should be 0 for lossless network',
                    ],
                    PlotType.Cartesian, YQuantity.Magnitude
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Amplifier Analysis (2-Port only)',
            [
                ExpressionTemplate(
                    'Gain',
                    [
                        'sel_nws().s(21).plot()  # S-parameter gain',
                        'sel_nws().mag().plot()  # maximum available gain',
                        'sel_nws().msg().plot()  # maximum stable gain',
                        'sel_nws().u().plot()    # Mason\'s unilateral gain',
                    ],
                    PlotType.Cartesian,
                ),
                None,
                ExpressionTemplate(
                    'Stability k',
                    [
                        'sel_nws().k().plot()      # Stability k; should be > 1 for stable network',
                        'sel_nws().delta().plot()  # Stability Δ; should be < 1 for stable network',
                    ],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'Stability µ',
                    [
                        'sel_nws().mu(1).plot()  # µ; should be > 1 for stable network',
                        'sel_nws().mu(2).plot()  # µ\'; should be > 1 for stable network',
                    ],
                    PlotType.Cartesian
                ),
                ExpressionTemplate(
                    'Stability Circles',
                    ['sel_nws().plot_stab(n=5,port=2)  # stability circles of port 2'],
                    PlotType.Smith
                ),
                None,
                ExpressionTemplate(
                    'Noise Figure',
                    ['sel_nws().noisefactor().plot()  # noise factor F'],
                    PlotType.Cartesian, YQuantity.Decibels
                ),
                ExpressionTemplate(
                    'Noise Circles',
                    ['sel_nws().plot_noise([1,3],n=1)  # noise circles'],
                    PlotType.Smith
                ),
                ExpressionTemplate(
                    'Minimum Noise Parameters',
                    [
                        'sel_nws().f_min().plot()      # minimum noise factor Fmin',
                        'sel_nws().rn().plot()         # equivalent noise resistance Rn',
                        'sel_nws().gamma_opt().plot()  # optimum input reflection coefficient Γopt for minimum noise; plot in Smith chart',
                    ],
                    PlotType.Cartesian
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Add Network',
            [
                ExpressionTemplate(
                    'Add Passive To Network',
                    ['({*selected} ** Comp.CSer(1e-9)).plot_sel_params()  # add a passive series component'],
                    min_selected=1
                ),
                ExpressionTemplate(
                    'Add Shunted Passive To Network',
                    ['({*selected} ** Comp.RShunt(1e3)).plot_sel_params()  # add a shunted passive component'],
                    min_selected=1
                ),
                ExpressionTemplate(
                    'Add Line To Network',
                    ['({*selected} ** Comp.Line(len=0.1)).plot_sel_params()  # add a transmission line'],
                    min_selected=1
                ),
                ExpressionTemplate(
                    'Add Line-Stub To Network',
                    ['({*selected} ** Comp.LineStub(len=0.1, stub_gamma=+1)).plot_sel_params()  # add a transmission line stub'],
                    min_selected=1
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Cascading and De-Embedding',
            [
                ExpressionTemplate(
                    'Cascade Selected Networks',
                    ['({selected_explicit_casc}).s(2,1).plot()'],
                    min_selected=2
                ),
                ExpressionTemplate(
                    'Cascade Reference Network',
                    ['(({reference}) ** sel_nws()).plot_sel_params()  # cascade reference network']
                ),
                None,
                ExpressionTemplate(
                    'De-Embed Reference Network From Others',
                    ['((~{reference}) ** sel_nws()).plot_sel_params()  # de-embed reference network']
                ),
                ExpressionTemplate(
                    'De-Embed Reference Network (Flipped) From Others',
                    ['(~({reference}.flipped()) ** sel_nws()).plot_sel_params()  # de-embed flipped reference network']
                ),
                ExpressionTemplate(
                    'From Others De-Embed Reference Network',
                    ['(sel_nws() ** (~"{reference}).plot_sel_params()  # de-embed reference network']
                ),
                ExpressionTemplate(
                    'From Others De-Embed Reference Network (Flipped)',
                    ['(sel_nws() ** (~{reference}).flipped)).plot_sel_params()  # de-embed flipped reference network']
                ),
                None,
                ExpressionTemplate(
                    'Treat Reference as 2xTHRU, De-Embed from Others',
                    ['((~{reference}).half(side=1)) ** sel_nws() ** (~{reference}).half(side=2))).plot_sel_params()  # deembed 2x thru']
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Normalization and Conversion',
            [
                ExpressionTemplate(
                    'Normalize at Given Frequency',
                    ['{*selected}.sel_params().norm(at_f={freqref}).plot()  # normalize at given frequency']
                ),
                ExpressionTemplate(
                    'Normalize to Reference Network',
                    ['(sel_nws() / {reference}).plot_sel_params()  # normalize to reference newtork']
                ),
                None,
                ExpressionTemplate(
                    'Single-Ended to Mixed-Mode',
                    ["{*selected}.s2m('P1,P2,N1,N2').plot_sel_params()  # single-ended to mixed-mode"]
                ),
                ExpressionTemplate(
                    'Mixed-Mode to Single-Ended',
                    ["{*selected}.m2s('D1,D2,C1,C2').plot_sel_params()  # mixed-mode to single-ended"]
                ),
                None,
                ExpressionTemplate(
                    'Impedance Renormalization',
                    ['{*selected}.renorm([50,75]).plot_sel_params()  # re-normalize port impedances']
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Statistics',
            [
                ExpressionTemplate(
                    'Min, Max, Peak-Peak',
                    [
                        'sel_nws().sel_params().min().plot()     # lowest value',
                        'sel_nws().sel_params().max().plot()     # highest value',
                        'sel_nws().sel_params().pkpk().plot()    # peak-to-peak value',
                        'sel_nws().sel_params().plot(style=":")  # all raw data'
                    ],
                    PlotType.Cartesian, YQuantity.Decibels,
                    need_many_for_stat = True
                ),
                ExpressionTemplate(
                    'Mean and Stddev',
                    [
                        'sel_nws().sel_params().mean().plot()    # mean',
                        'sel_nws().sel_params().sdev().plot()    # standard deviation',
                        'sel_nws().sel_params().plot(style=":")  # all raw data'
                    ],
                    PlotType.Cartesian, YQuantity.Decibels,
                    need_many_for_stat = True
                ),
                ExpressionTemplate(
                    'Robust Mean and Stddev',
                    [
                        'sel_nws().sel_params().median().plot()             # median / robust mean',
                        'sel_nws().sel_params().rsdev(quantiles=50).plot()  # robust standard deviation from inter-quantile range',
                        'sel_nws().sel_params().plot(style=":")             # all raw data',
                    ],
                    PlotType.Cartesian, YQuantity.Decibels,
                    need_many_for_stat = True
                ),
            ]
        ),
        ExpressionTemplateGroup(
            'Miscellaneous',
            [
                ExpressionTemplate(
                    'All Available Networks',
                    ['nws().sel_params().plot()  # just plot all available networks']
                ),
                ExpressionTemplate(
                    'All Available Networks (via Explicit Name)',
                    ['{*all}.sel_params().plot()']
                ),
                ExpressionTemplate(
                    'Currently Selected Networks',
                    ['sel_nws().sel_params().plot()  # just plot all selected networks']
                ),
                ExpressionTemplate(
                    'Currently Selected Networks (via Explicit Name)',
                    ['{*selected_explicit}.sel_params().plot()']
                ),
                ExpressionTemplate(
                    'Select Networks via Slicer',
                    ["nws().slice(r'{slicerpattern}'').sel_params().plot()  # show slicer"]
                ),
                ExpressionTemplate(
                    'Slide through Frequencies',
                    [
                        'f0, f1, nf = sel_nws().get_f_min(), sel_nws().get_f_max(), 101',
                        'f = slider(linspace=(f0, f1 ,nf))',
                        'sel_nws().crop_f(f-(f1-f0)/nf, f+(f1-f0)/nf).plot_sel_params()',
                    ]
                ),
                ExpressionTemplate(
                    'Smooth Trace',
                    [
                        '#sel_nws().sel_params().plot()  # regular traces',
                        'sel_nws().sel_params().smooth().plot()  # smoothed traces',
                        '#(sel_nws().sel_params()/sel_nws().sel_params().smooth()).plot()  # plot only the "noisyness" of a trace',
                    ]
                ),
            ]
        ),
    ]
