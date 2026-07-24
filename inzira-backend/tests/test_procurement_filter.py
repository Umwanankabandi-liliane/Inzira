"""Procurement vs youth opportunity classification."""

from opportunity_extractor import is_procurement_listing


def test_tender_notices_rejected():
    assert is_procurement_listing("Tender Notice for Supply of Laptops")
    assert is_procurement_listing("Request for Quotation — Office Furniture")
    assert is_procurement_listing("RFQ: Network Equipment")


def test_youth_jobs_kept():
    assert not is_procurement_listing("Human Resources Officer")
    assert not is_procurement_listing("Procurement Officer")
    assert not is_procurement_listing("Audit/Accounts Intern")
    assert not is_procurement_listing("Senior Project Officer")


def test_supplier_eoi_rejected():
    assert is_procurement_listing("Call for Expression of Interest (EoI)")
    assert is_procurement_listing(
        "Expression of Interest for Construction and Rehabilitation"
    )


def test_framework_and_tor():
    assert is_procurement_listing("Framework Contract/Seeds and Fertilizer Supply")
    assert is_procurement_listing("Terms of Reference for Office Renovation")
