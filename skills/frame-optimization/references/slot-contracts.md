# Slot contracts

Read this reference completely when creating a new A-H contract or materially reframing an existing contract.

When D, E, or H requires a new or materially revised measurement design, use `design-measurement` and [measurement-design.md](measurement-design.md). The Primary Framing Agent adopts its complete projection without rewriting the professional meaning. Existing-protocol execution and implementation-only repair do not invoke measurement design.

## A. Object and instance space

Identify the optimized system, algorithm, structure, or process. Define the task, input space, scale variables, and operating conditions.

For an average-case claim, name the input distribution. A numeric range does not define a distribution.

Completion test: A reader can determine which instances and scales each claim covers.

## B. Solution space and representation

Define legal and illegal solutions. Define the representation and whether representation is part of the problem.

State how representation determines neighborhoods, local optimality, or search difficulty. Define when two solutions are equivalent.

Completion test: A reader can decide whether any candidate is legal and whether two candidates are the same solution.

## C. Constraints and semantics

List every material correctness, safety, accuracy, stability, and physical constraint. Classify each constraint as hard, soft, or probabilistic.

For a probabilistic constraint, state the required probability. For a soft constraint, identify its penalty in Slot D.

Completion test: Every violation has a defined legal or objective consequence.

## D. Objective and comparison

State the final evaluated entity and what to minimize, maximize, or order. Define whether the task uses one objective or several objectives.

For multiple objectives, define weights, lexicographic order, Pareto dominance, or thresholds. Define the baseline and success test.

Separate the real objective from any value used only for diagnosis, search, or local comparison. Define objective-side success and material-improvement thresholds here. Slot H owns what a measured value can establish; R8 owns the campaign action chosen within that evidence ceiling.

State the smallest improvement relevant to each selection, route, or investment decision. When no value threshold exists, limit the measurement to a bounded diagnostic and state its resolution; do not silently use any positive difference for promotion or material allocation.

For approximate success, state whether error is additive or multiplicative. For Pareto order, define the front as the deliverable.

Completion test: A reader can compare any two legal solutions or explain why neither dominates, and can identify the objective-side threshold relevant to the comparison without consulting a proxy definition.

## E. Evaluation and quantifiers

Define the elementary outcome and aggregation over instances and randomness. Separate algorithm randomness, measurement noise, and seed variation.

Define the observation unit, evaluation cases, repetitions or samples, sources of variation, aggregation, and the population or fixed set to which uncertainty refers. A fixed evaluation set supports conclusions about that set unless the contract supplies an applicable wider-scope argument.

Distinguish the observation count from the independent analysis-unit count. Define which competing explanations the comparison can separate and which confounding or alternative explanations remain.

Define finite or asymptotic scope. State quantifier order, uniformity across scale, and whether a solution can vary with scale.

Define the adversary scope. Include inputs, tie-breaking, scheduling, and adaptation when applicable.

Completion test: The evaluation gives one unambiguous mathematical meaning to the comparison in Slot D, including the elementary outcome, cross-instance or cross-condition aggregation, conditions, and inferential target covered by the result.

## F. Resources

Record solution operating cost and search cost separately. Cover applicable time, memory, energy, communication, hardware, samples, experiments, and computation.

Define a conversion rule before combining different resource currencies.

Completion test: A reader can distinguish the cost of a solution from the cost of finding it.

## G. Interaction and information

State whether the task is static, online, dynamic, or sequential. Define available pretraining, offline data, oracle access, and future information.

State whether the environment or opponent adapts to the optimizer. For sequential tasks, define regret, competitive ratio, or final value when applicable.

Completion test: Every information advantage and feedback timing rule is explicit.

## H. Measurement

Define the reusable measurement meaning, evaluation data, repetitions, statistics, confidence requirements, and measurement code. Pin executable measurement code to a commit. Reference the applicable D objective and E evaluation clauses rather than copying them.

For each measured value whose lifecycle changes its meaning, define the applicable initialization, intermediate, and decision-ready states and the context keys needed to interpret an observation at those states. An initialization or default value, execution success, and a context-incomplete intermediate snapshot establish only their direct operational facts.

Classify the value's relationship to D as `real-objective`, `established-proxy`, or `unknown-proxy`. Keep its execution role, such as `diagnostic-only`, separate. State the strongest factual conclusion supported and the stronger unsupported conclusions. An unknown relationship may support one bounded diagnostic observation when its possible results can change the next decision; it cannot by itself establish objective improvement.

Record lightweight source coverage for every decision-critical D, E, or H fact used to interpret the value. Each relied-on fact is either linked to a source that actually supports it or remains explicitly unresolved. One source may support several facts. Do not create fact identifiers, source identifiers, a registry, or a second relationship-evidence field.

Give every material schedule part one distinct role and decision-relevant information contribution. Separate execution checks, calibration, direct comparison, robustness checks, and confirmation. Reuse protocol-level calibration while its assumptions remain valid; a new candidate alone does not require recalibration.

Record controls and sensitivity checks only when they expose a material failure mode. Record adaptive exposure only when earlier results guide later generation, tuning, screening, ranking, or selection. State the maximum supported factual inference for each material result class, plus recalibration, replacement, and invalidation conditions. R8 maps those factual limits to actual investment consequences.

Completion test: Another agent can reproduce the measurement, distinguish an initialization or intermediate value from the decision-ready result, trace every decision-critical interpretation to supported or unresolved facts, explain its relationship to the real objective, and apply its factual limit without redefining D or E.
