def validate_kyb_checklist(data):
    failures = []

    business = data.get("business", {})
    control_person = data.get("control_person", {})
    beneficial_owners = data.get("beneficial_owners", [])
    watchlist_hits = data.get("watchlist_hits", {})

    # 1. Check business name
    if not business.get("name"):
        failures.append("Business name is missing")

    # 2. Check incorporation country
    if not business.get("incorporation_country"):
        failures.append("Incorporation country is missing")

    # 3. Check control person full name
    if not control_person.get("full_name"):
        failures.append("Control person full name is missing")

    # 4. Check at least one beneficial owner with full name and ownership
    if not any(bo.get("full_name") and bo.get("ownership") for bo in beneficial_owners):
        failures.append("Valid beneficial owner with name and ownership is missing")

    # 5. Check if business is flagged in watchlist
    if watchlist_hits.get("business"):
        failures.append("Business flagged in watchlist")

    # 6. Check if control person is flagged in watchlist
    if watchlist_hits.get("control_person"):
        failures.append("Control person flagged in watchlist")

    # 7. Check if any beneficial owner is flagged
    if watchlist_hits.get("beneficial_owners"):
        failures.append("A beneficial owner is flagged in watchlist")

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }

