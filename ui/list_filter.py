def reflow_rows(items, query, **pack_kwargs):
    """Re-pack only the rows matching `query`, in their original creation
    order, so hiding/showing rows during a live search never scrambles
    their relative order.

    `items` is a list of (name, widget) tuples. `query` is matched
    case-insensitively as a substring of `name`; an empty/blank query
    matches everything.
    """
    query = query.strip().lower()
    pack_kwargs.setdefault("fill", "x")
    pack_kwargs.setdefault("pady", 2)
    for _, row in items:
        row.pack_forget()
    for name, row in items:
        if not query or query in name.lower():
            row.pack(**pack_kwargs)
