REGISTRIES = {
    "uk_companies_house": {
        "label": "UK Companies House",
        "jurisdiction": "UK",
        "record_type": "company_registration",
        "url": "https://find-and-update.company-information.service.gov.uk/",
        "hint": (
            "Type the name into the company search box and submit. From the search results list, extract the matching "
            "companies directly (copy company name, company number as license_number, registered address as location, "
            "and record link as record_url) even if results are partial matches. Copy the status exactly as shown; "
            "if the search listing shows no explicit status, return an empty string. "
            "If a result shows 'Matching previous name: X', capture that in matched_previous_name."
        ),
        "status_regex": r"Company status\W*([A-Za-z][A-Za-z \-]{2,30})",
    },
    "fl_sunbiz": {
        "label": "Florida Division of Corporations (Sunbiz)",
        "jurisdiction": "US-FL",
        "record_type": "company_registration",
        "url": "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName",
        "hint": (
            "Type the name into the 'Entity Name' input box and click 'Search Now'. "
            "From the search results table, extract each Corporate Name as name, Document Number as license_number, "
            "and Status (e.g. Active, Inactive, INACT) as status, and the row link as record_url."
        ),
        "status_regex": r"Status\W*([A-Za-z]+)",
    },
    "ca_dca": {
        "label": "California Department of Consumer Affairs",
        "jurisdiction": "US-CA",
        "record_type": "professional_license",
        "url": "https://search.dca.ca.gov/",
        "hint": (
            "Select Search by Personal Name or Business Name. Fill in Last Name or Business Name and submit. "
            "Copy license type, number, status, issue and expiration dates."
        ),
    },
}
