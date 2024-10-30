from db_client.functions.corpus_helpers import get_taxonomy_by_corpus_type_name

EXPECTED_UNFCCC_TAXONOMY = {
    "author": {
        "allow_any": True,
        "allow_blanks": False,
        "allowed_values": [],
    },
    "author_type": {
        "allow_any": False,
        "allow_blanks": False,
        "allowed_values": ["Party", "Non-Party"],
    },
    "event_type": {
        "allow_any": False,
        "allow_blanks": True,
        "allowed_values": [
            "Amended",
            "Appealed",
            "Closed",
            "Declaration Of Climate Emergency",
            "Dismissed",
            "Entered Into Force",
            "Filing",
            "Granted",
            "Implementation Details",
            "International Agreement",
            "Net Zero Pledge",
            "Other",
            "Passed/Approved",
            "Repealed/Replaced",
            "Set",
            "Settled",
            "Updated",
        ],
    },
    "_event": {
        "event_type": {
            "allow_any": False,
            "allow_blanks": True,
            "allowed_values": [
                "Amended",
                "Appealed",
                "Closed",
                "Declaration Of Climate Emergency",
                "Dismissed",
                "Entered Into Force",
                "Filing",
                "Granted",
                "Implementation Details",
                "International Agreement",
                "Net Zero Pledge",
                "Other",
                "Passed/Approved",
                "Repealed/Replaced",
                "Set",
                "Settled",
                "Updated",
            ],
        },
        "datetime_event_name": {
            "allow_any": False,
            "allow_blanks": False,
            "allowed_values": ["Passed/Approved"],
        },
    },
    "_document": {
        "role": {
            "allow_any": False,
            "allow_blanks": False,
            "allowed_values": [
                "MAIN",
                "AMENDMENT",
                "SUPPORTING LEGISLATION",
                "SUMMARY",
                "PREVIOUS VERSION",
                "ANNEX",
                "SUPPORTING DOCUMENTATION",
                "INFORMATION WEBPAGE",
                "PRESS RELEASE",
                "DOCUMENT(S) STORED ON WEBPAGE",
            ],
        },
        "type": {
            "allow_any": False,
            "allow_blanks": False,
            "allowed_values": [
                "Accord",
                "Act",
                "Action Plan",
                "Agenda",
                "Annex",
                "Assessment",
                "Bill",
                "Constitution",
                "Criteria",
                "Decision",
                "Decision and Plan",
                "Decree",
                "Decree Law",
                "Directive",
                "Discussion Paper",
                "Edict",
                "EU Decision",
                "EU Directive",
                "EU Regulation",
                "Executive Order",
                "Framework",
                "Law",
                "Law and Plan",
                "Order",
                "Ordinance",
                "Plan",
                "Policy",
                "Press Release",
                "Programme",
                "Protocol",
                "Roadmap",
                "Regulation",
                "Resolution",
                "Royal Decree",
                "Rules",
                "Statement",
                "Strategic Assessment",
                "Strategy",
                "Summary",
                "Vision",
                "Biennial Report",
                "Biennial Update Report",
                "Facilitative Sharing of Views Report",
                "Global Stocktake Synthesis Report",
                "Industry Report",
                "Intersessional Document",
                "Long-Term Low-Emission Development Strategy",
                "National Communication",
                "National Inventory Report",
                "Pre-Session Document",
                "Progress Report",
                "Publication",
                "Report",
                "Submission to the Global Stocktake",
                "Summary Report",
                "Synthesis Report",
                "Technical Analysis Summary Report",
                "Nationally Determined Contribution",
                "Adaptation Communication",
                "National Adaptation Plan",
                "Technology Needs Assessment",
                "Fast-Start Finance Report",
                "IPCC Report",
                "Annual Compilation and Accounting Report",
                "Biennial Report,National Communication",
                "Biennial Update Report,National Communication",
                "National Adaptation Plan,Adaptation Communication",
                "National Communication,Biennial Report",
                "National Communication,Biennial Update Report",
                "Nationally Determined Contribution,Adaptation Communication",
                "Nationally Determined Contribution,National Communication",
                "Pre-Session Document,Annual Compilation and Accounting Report",
                "Pre-Session Document,Progress Report",
                "Pre-Session Document,Synthesis Report",
                "Publication,Report",
                "Technical Analysis Technical Report",
            ],
        },
    },
}


def test_get_taxonomy_is_none_when_type_none(test_db):
    assert get_taxonomy_by_corpus_type_name(test_db, None) is None


def test_get_taxonomy_is_good_when_UNFCCC(test_db):
    assert (
        get_taxonomy_by_corpus_type_name(test_db, "Intl. agreements")
        == EXPECTED_UNFCCC_TAXONOMY
    )
