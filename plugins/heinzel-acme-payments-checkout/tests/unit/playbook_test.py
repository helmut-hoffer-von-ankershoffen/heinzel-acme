import pytest
from heinzel import PlaybookLet
from heinzel_acme_payments_checkout import DRAFT_TAGS, module

pytestmark = pytest.mark.unit


def playbook():
    return next(let for let in module.heinzel_lets() if isinstance(let, PlaybookLet))


def test_the_weekly_report_template_names_every_asset_type():
    (template,) = playbook().templates
    assert template.name == "weekly-report"
    assert set(template.placeholders()) == {a.name for a in playbook().assets}


def test_the_weekly_report_document_is_kept_by_the_template():
    kept = {a.name: a.kept_by for a in playbook().assets}
    assert kept["weekly-report"] == "weekly-report"


def test_the_template_drafts_by_friday_17_but_never_schedules_itself():
    text = playbook().templates[0].text
    assert '# schedule: "0 17 * * FRI"' in text
    assert "\n  schedule:" not in text


def test_the_template_reads_code_host_tracker_and_documents():
    text = playbook().templates[0].text
    for read in ("code-host.merged_pull_requests", "tracker.issues_updated", "documents.read"):
        assert f"read: {read}" in text


def test_every_kept_asset_has_a_draft_tag():
    assert {a.name for a in playbook().assets if a.kept_by} <= set(DRAFT_TAGS)
