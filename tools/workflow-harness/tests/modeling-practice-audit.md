# Modeling practice and parameter-basis audit

Date: 2026-10-06. This portable extract retains the general primary-source
findings and questions from a read-only source-project audit. Project-specific
code paths, private execution traces and experiment settings are omitted. The
original audit did not modify Skills, runtime, business records or experiments.

## Finding and limits

The source audit found influential empirical settings without a retained basis
in the inspected evidence, despite existing rules requiring such reasoning.
That supports checking the actual first adoption and methodological coverage;
it does not establish that the settings were wrong or that all historical
experiments lacked justification. Documentation delivery and rule application
remain different observations. Missing rationale may be repaired through the
existing owner without rewriting history or mandating a tuning stage.

## Primary-source evidence

All sources were accessed on 2026-10-06. They guide technical judgment, not the exact best configuration for this project.

- **Google Research, Deep Learning Tuning Playbook:** start from closely related work where possible, with an affordable configuration achieving reasonable validation performance. Initial choices include architecture, optimizer settings, and training steps. Later tuning advice assumes a working pipeline and sufficient resources. Learning curves help diagnose failures; short-run conclusions may not transfer to longer runs. Periodic evaluation may use a reliable proxy or subset. The guide recommends fixed-step training with retrospective best-checkpoint selection and says prospective early stopping is usually unnecessary under that arrangement. [Primary source](https://github.com/google-research/tuning_playbook).
- **Keras:** stopping and restoring selected weights are distinct controls. `EarlyStopping` supports a monitored metric, patience, and warm-up; `restore_best_weights` defaults to false. Early stopping alone therefore does not establish best-weight use. [Official API](https://keras.io/api/callbacks/early_stopping/).
- **PyTorch:** when choosing by validation performance, save or copy the selected state; `model.state_dict()` alone retains a reference subsequently changed by training. This is conditional implementation guidance, not a universal selection policy. [Official tutorial](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html).
- **scikit-learn:** tuning against test outcomes leaks test information into model selection. Validation supports development choices; held-out test data support final evaluation. Cross-validation changes the data/computation tradeoff, rather than eliminating the final-test distinction. [Official guide](https://scikit-learn.org/stable/modules/cross_validation.html).

## Auditable questions

1. **Basis and first adoption:** What supported the influential settings: comparable baseline, prior measurements, calculation, professional judgment, or explicit exploratory guess? Why were they adequate for the intended observation? Was the existing rule applied when the implementation first fixed them?
2. **Applicable practice:** Did the developer consider a relevant mature method and its transfer conditions, or did API correctness stand in for methodological preparation? Existing knowledge may suffice; this question does not demand a new survey.
3. **Observation and claim:** Was the horizon a cost-bounded comparison, an execution probe, or evidence about attainable model quality? Which development signal could distinguish a weak realization from a weak mechanism? Absence of that signal does not prove undertraining or overfitting.
4. **Selection and consumption:** Which partitions may influence training choices, and which outcomes remain protected? If selection changes, will the actual scorer consume the chosen checkpoint correctly while preserving recovery and historical evidence?

## Minimal response and verification

First locate or correct the missing basis through the existing owner. If a general clarification is warranted, attach a concise consideration of applicable established practice to consequential realization and parameter choices. Preserve its scope and reasoning into implementation. Reuse sufficient evidence; require neither alternative success in advance nor a new specialist, form, review gate, full-pool per-epoch validation, or hyperparameter-search stage.

A later behavioral check should inspect actual assignment, implementation, observation, and adoption. Include controls with adequate existing rationale and legitimate fixed-condition experiments; both should continue without repeated research. Include prohibited test reuse. Count research, coordination, implementation, and evaluation costs. Rule changes, passing checks, actual use, and improved research efficiency remain separate claims. None is established here.
