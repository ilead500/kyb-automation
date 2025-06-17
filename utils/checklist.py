from datetime import datetime, timedelta

def validate_kyb_checklist(data):
    failures = []
    verification = data.get("verification_results", {})
    documents = data.get("proof_of_address", {})
    watchlist_hits = data.get("watchlist_hits", {})

    # 1. Business Checks (Required by buyer)
    if not data.get("business", {}).get("name"):
        failures.append("Business name is missing")
    if not data.get("business", {}).get("incorporation_country"):
        failures.append("Incorporation country is missing")

    # 2. Control Person Checks
    if not data.get("control_person", {}).get("full_name"):
        failures.append("Control person full name is missing")

    # 3. Beneficial Owners (Buyer requires verification)
    if not any(bo.get("full_name") and bo.get("ownership") 
           for bo in data.get("beneficial_owners", [])):
        failures.append("Valid beneficial owner missing")

    # 4. Document Verification (Critical 90-day check)
    if documents.get("status") != "approved":
        if not documents.get("document_date"):
            failures.append("Proof of address missing")
        else:
            doc_date = datetime.strptime(documents["document_date"], "%Y-%m-%d")
            if (datetime.now() - doc_date) > timedelta(days=90):
                failures.append("Proof of address expired (>90 days)")

    # 5. Watchlist/PEP Checks (From both sources)
    if (verification.get("watchlist") != "clear" or 
        watchlist_hits.get("business")):
        failures.append("Business watchlist match")
    if (verification.get("pep") != "clear" or 
        watchlist_hits.get("control_person")):
        failures.append("PEP match detected")
    if watchlist_hits.get("beneficial_owners"):
        failures.append("Beneficial owner watchlist match")

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "contact_email": data.get("form_filler", {}).get("email", "submitter@example.com")
    }

# Test payload - try running: python utils/checklist.py
if __name__ == "__main__":
    test_case = {
        "business": {"name": "Test Inc", "incorporation_country": "US"},
        "control_person": {"full_name": "John Doe"},
        "beneficial_owners": [{"full_name": "Alice", "ownership": 25}],
        "proof_of_address": {"status": "approved", "document_date": "2024-05-01"},
        "verification_results": {"watchlist": "clear", "pep": "clear"},
        "form_filler": {"email": "admin@test.com"}
    }
    print(validate_kyb_checklist(test_case))