## Comparability branch

Use this branch only when changed comparison meaning or concrete contrary evidence affects a proposed use of retained results. A workflow update or unchanged original use does not trigger it.

Read the old and new meaning, the affected result or class, and evidence needed for the proposed comparison. Choose `unaffected` when that use is still supported, `re-evaluated` when a needed new measurement supports it, or `voided` when the proposed comparison is unsupported. Missing historical evidence limits that use; it does not erase the original result. Require no rerun of unrelated retained results.

Record the disposition and affected use in the existing log. Apply task-documents' epoch rule to the actual comparison change. Combine overlapping readiness questions in this assigned review instead of requiring another review of the same change. Review only additional dependent requirements that have not been resolved.

Completion means the affected comparison has a supported disposition and unresolved dependent work is identified. Unchanged results, unrelated readiness and original evidence remain intact.

## Output

For comparability, return:

```text
DISPOSITION: unaffected | re-evaluated | voided
Task: <canonical task path>
Slot: <A-H>
Epoch: <old> -> <new>
Reason: <decisive semantic comparison>
Affected results: <identifiers and final state>
```
