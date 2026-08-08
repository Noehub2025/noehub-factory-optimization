# Slot contracts

Read this reference completely when creating a new A-H contract or materially reframing an existing contract.

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

State what to minimize or maximize. Define whether the task uses one objective or several objectives.

For multiple objectives, define weights, lexicographic order, Pareto dominance, or thresholds. Define the baseline and success test.

For approximate success, state whether error is additive or multiplicative. For Pareto order, define the front as the deliverable.

Completion test: A reader can compare any two legal solutions or explain why neither dominates.

## E. Evaluation and quantifiers

Define aggregation over instances and randomness. Separate algorithm randomness, measurement noise, and seed variation.

Define finite or asymptotic scope. State quantifier order, uniformity across scale, and whether a solution can vary with scale.

Define the adversary scope. Include inputs, tie-breaking, scheduling, and adaptation when applicable.

Completion test: The evaluation gives one unambiguous mathematical meaning to the comparison in Slot D.

## F. Resources

Record solution operating cost and search cost separately. Cover applicable time, memory, energy, communication, hardware, samples, experiments, and computation.

Define a conversion rule before combining different resource currencies.

Completion test: A reader can distinguish the cost of a solution from the cost of finding it.

## G. Interaction and information

State whether the task is static, online, dynamic, or sequential. Define available pretraining, offline data, oracle access, and future information.

State whether the environment or opponent adapts to the optimizer. For sequential tasks, define regret, competitive ratio, or final value when applicable.

Completion test: Every information advantage and feedback timing rule is explicit.

## H. Measurement

Define evaluation data, repetitions, statistics, confidence requirements, and measurement code. Pin executable measurement code to a commit.

State whether each measured value is the real objective or a proxy. Record known proxy error and Goodhart risk.

Completion test: Another agent can reproduce the measurement and interpret its difference from the real objective.
