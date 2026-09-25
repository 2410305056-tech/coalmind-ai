from typing import List, Dict, Any
from backend.store.base import BaseStore

def scan_and_record_conflicts(store: BaseStore, tolerance: float = 0.05) -> int:
    """
    Scans all metrics in the store to detect conflicting values for the same
    subsidiary/mine/year/parameter across different source documents.
    """
    all_metrics = store.query_metrics()
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for m in all_metrics:
        # Key: mine:year:parameter
        key = f"{m.get('mine', '').strip().lower()}:{m.get('year', '').strip()}:{m.get('parameter', '').strip().lower()}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(m)

    existing_conflicts = store.get_conflicts()
    existing_keys = {
        f"{c['mine'].lower()}:{c['year']}:{c['parameter'].lower()}:{c['source1']}:{c['source2']}"
        for c in existing_conflicts
    }

    new_conflicts_count = 0
    for key, items in grouped.items():
        if len(items) < 2:
            continue
        
        # Compare pairs across different sources
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                item1 = items[i]
                item2 = items[j]
                
                # Check if different source documents
                if item1["source_doc"] == item2["source_doc"]:
                    continue

                v1 = float(item1["value"])
                v2 = float(item2["value"])
                
                # If difference exceeds tolerance threshold
                if abs(v1 - v2) > max(0.01, min(v1, v2) * tolerance):
                    conflict_key1 = f"{item1['mine'].lower()}:{item1['year']}:{item1['parameter'].lower()}:{item1['source_doc']}:{item2['source_doc']}"
                    conflict_key2 = f"{item1['mine'].lower()}:{item1['year']}:{item1['parameter'].lower()}:{item2['source_doc']}:{item1['source_doc']}"
                    
                    if conflict_key1 not in existing_keys and conflict_key2 not in existing_keys:
                        store.add_conflict({
                            "subsidiary": item1.get("subsidiary", "SECL"),
                            "mine": item1.get("mine", "Gevra"),
                            "year": item1.get("year", "2022"),
                            "parameter": item1.get("parameter", "Coal Production"),
                            "val1": v1,
                            "source1": item1["source_doc"],
                            "val2": v2,
                            "source2": item2["source_doc"]
                        })
                        existing_keys.add(conflict_key1)
                        new_conflicts_count += 1

    return new_conflicts_count
