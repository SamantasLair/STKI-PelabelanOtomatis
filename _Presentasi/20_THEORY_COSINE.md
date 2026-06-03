# PRES: THEORY OF COSINE SIMILARITY

Konteks: Turunan dari [[12_AI_NLP_ENGINE]].

## MATHEMATICAL FORMULATION (L3)
$$
\text{sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}
$$

## 5W1H: COSINE SIMILARITY & REPRESENTATION COLLAPSE
- **WHAT**: Geometric measurement of semantic distance. Representation Collapse is when this distance is universally 99% due to unactivated logits.
- **WHY**: Crucial for mapping multi-label intersections.
- **WHERE**: `TKI/app_web.py`
- **WHEN**: Asynchronous document relabeling.
- **HOW**: Mitigated by switching from direct logit evaluation to mean-pooling hidden states.
