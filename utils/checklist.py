from datetime import datetime, timedelta

# NEW: Add prohibited lists (from company doc)
PROHIBITED_COUNTRIES = [
    "Afghanistan", "Algeria", "Bangladesh", "Belarus", "Bhutan", 
    "Bosnia and Herzegovina", "Burma (Myanmar)", "Burundi", 
    "Central African Republic", "China", 
    "The Democratic Republic of Congo", "Croatia", "Cuba", "Ethiopia", 
    "Gaza Strip", "Guinea-Bissau", "Haiti", "Iran", "Iraq", "Kenya", 
    "Kosovo", "Lebanon", "Libya", "Macedonia (North)", "Mali", 
    "Montenegro", "Morocco", "Mozambique", "Nepal", "Nicaragua", 
    "Niger", "North Korea", "Pakistan", "Qatar", "Russian Federation", 
    "Serbia", "Slovenia", "Somalia", "South Sudan", "Sudan", "Syria", 
    "Ukraine", "Venezuela (Bolivarian Republic of)", 
    "West Bank (Palestinian Territory)", "Yemen", "Zimbabwe"
    # ... [full list from company doc]
]

PROHIBITED_INDUSTRIES = [
    "Gambling", "Marijuana/cannabis", "Guns", 
    "Arms and ammunition", "Adult entertainment", 
]

def validate_kyb_checklist(data):
    failures = []
    business = data.get("business", {})
    verification = data.get("verification_results", {})
    documents = data.get("proof_of_address", {})
    watchlist_hits = data.get("watchlist_hits", {})

    # ===== 1. BUSINESS CHECKS =====
    # NEW: Expanded required fields (company doc)
    required_business_fields = [
        "name",  # Original
        "legal_name",  # NEW
        "ein",  # NEW
        "address",  # NEW
        "incorporation_country"  # Original + renamed
    ]
    for field in required_business_fields:
        if not business.get(field):
            failures.append(f"Business {field.replace('_', ' ')} missing")

    # ===== 2. PROHIBITED CHECKS ===== (NEW)
    if business.get("country") in PROHIBITED_COUNTRIES:
        failures.append(f"Prohibited country: {business['country']}")
    if business.get("industry") in PROHIBITED_INDUSTRIES:
        failures.append(f"Prohibited industry: {business['industry']}")

    # ===== 3. CONTROL PERSON ===== (Original)
    if not data.get("control_person", {}).get("full_name"):
        failures.append("Control person full name is missing")

    # ===== 4. BENEFICIAL OWNERS ===== (Original + enhanced)
    beneficial_owners = data.get("beneficial_owners", [])
    if not any(bo.get("full_name") and bo.get("ownership") for bo in beneficial_owners):
        failures.append("Valid beneficial owner missing")
    # NEW: Check watchlist hits for owners
    if watchlist_hits.get("beneficial_owners"):
        failures.append("Beneficial owner watchlist match")

    # ===== 5. DOCUMENT CHECKS =====
    # Original 90-day logic + NEW status check
    if documents.get("status") != "approved":
        if not documents.get("document_date"):
            failures.append("Proof of address missing")
        else:
            doc_date = datetime.strptime(documents["document_date"], "%Y-%m-%d")
            if (datetime.now() - doc_date) > timedelta(days=90):
                failures.append("Proof of address expired (>90 days)")

    # ===== 6. WATCHLIST/PEP CHECKS =====
    # Original dual-source verification
    if (verification.get("watchlist") != "clear" or 
        watchlist_hits.get("business")):
        failures.append("Business watchlist match")
    if (verification.get("pep") != "clear" or 
        watchlist_hits.get("control_person")):
        failures.append("PEP match detected")

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
