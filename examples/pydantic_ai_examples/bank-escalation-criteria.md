# Add escalation criteria and routing path for high-risk queries

## Summary

**Context:** The bank support agent computes a risk score for every customer query and may decide to block a card.

**Issue:** No escalation criteria exist in the prompt, the output schema, or any surrounding policy. High-risk queries — fraud reports, suspected unauthorized access, account compromise — are fully resolved by the automated agent with no pathway to a human specialist.

**Actual vs. expected:** A `risk=9` response and a `risk=2` response are handled identically. Expected: queries above a defined risk threshold, or matching specific fraud/compromise categories, produce an `escalate_to_human=True` flag that the calling application routes to a human agent.

**Impact:** Customers in genuine banking emergencies receive only automated advice. The bank has no mechanism to trigger specialist review from within the agent loop.

## Where

<github_code url="https://github.com/introspection-org/pydantic-ai/blob/main/examples/pydantic_ai_examples/bank_support.py#L44-L61" />

```python
class SupportOutput(BaseModel):
    support_advice: str
    block_card: bool
    risk: int  # <-- computed but never used for routing
    # <-- MISSING: escalate_to_human field


support_agent = Agent(
    instructions=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query. '
        "Reply using the customer's name."
        # <-- MISSING: no escalation criteria whatsoever
    ),
)
```

## Evidence

### Example

Customer sends: "Someone used my card at three locations I don't recognize last night."

1. Agent fetches customer name and balance
2. Agent produces: `support_advice="We're sorry to hear that, John. We recommend blocking your card immediately.", block_card=True, risk=9`
3. **No escalation occurs.** The customer receives automated advice. No fraud specialist is notified. No case is opened.

### Structural gap

The risk field was designed to capture query severity but the architectural loop — compute risk → decide what to do with it — was never completed:
- `risk` is computed ✓
- `risk` is included in the output ✓
- `risk` is acted on by the application → **not implemented**
- Escalation path exists → **not implemented**

## Impact

- **Customer safety:** Fraud victims and account-compromise cases are handled end-to-end by an LLM with no human in the loop
- **Regulatory exposure:** Most banking regulations (e.g., PCI-DSS, Reg E) require human review for certain fraud and dispute categories
- **Missed escalations:** False negatives (model underestimates risk) have no safety net

## Recommendation

Add `escalate_to_human: bool` to `SupportOutput` and define explicit escalation criteria in the system prompt.

**Decision needed:**

- **Option A: Threshold-based** — set `escalate_to_human=True` when `risk >= 8`. Simple and consistent with the risk rubric once the field is constrained (see the risk-schema PR).
- **Option B: Category-based** — enumerate specific situations that always escalate (unauthorized transactions, suspected fraud, account compromise, disputed charges) regardless of risk score. More precise but requires prompt maintenance as categories evolve.
- **Option C: Combined** — threshold-based as a backstop plus explicit fraud/compromise categories as hard triggers.

### Suggested implementation (Option C)

```python
class SupportOutput(BaseModel):
    support_advice: str
    """Advice returned to the customer"""
    block_card: bool
    """Whether to block their card or not"""
    risk: int = Field(ge=1, le=10)
    """Risk level of query: 1 (routine) to 10 (critical/fraud)"""
    escalate_to_human: bool
    """Whether this query requires human specialist review"""
```

System prompt addition:

```
Set escalate_to_human=True if the customer reports unauthorized transactions,
suspected fraud, account compromise, or a disputed charge — or if the risk
score is 8 or higher. When escalating, advise the customer that a specialist
will contact them shortly.
```

Note: the downstream routing step (how `escalate_to_human=True` is acted on) is outside the agent definition and should be implemented in the calling application.

## Related

- Risk score rubric PR adds `Field(ge=1, le=10)` to `SupportOutput.risk`, which this escalation logic depends on.
- Card-block gate investigation addresses a related control gap for the `block_card` field.
