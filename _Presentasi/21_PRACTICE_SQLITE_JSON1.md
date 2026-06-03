# PRES: PRACTICE OF SQLITE JSON1

Konteks: Turunan dari [[10_BACKEND_ARCHITECTURE]].

## 5W1H: JSON1 OFFLOADING (L3)
- **WHAT**: Delegation of JSON parsing from Python runtime to SQLite's native C-based extension.
- **WHY**: Prevents OOM crashes on large datasets.
- **WHERE**: `/api/documents` endpoint.
- **WHEN**: Document retrieval and Taxonomy filtering.
- **HOW**: 
```sql
SELECT id, filename FROM documents 
WHERE EXISTS (
    SELECT 1 FROM json_each(documents.labels) WHERE json_each.value = 'Target'
)
```
