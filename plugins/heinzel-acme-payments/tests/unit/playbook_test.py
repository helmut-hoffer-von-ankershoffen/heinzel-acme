import pytest
from heinzel import PlaybookLet
from heinzel_acme_payments import OKR_DOCUMENT, module

pytestmark = pytest.mark.unit


def test_the_org_brings_the_okr_asset_type_with_a_confirming_hint():
    playbook = next(let for let in module.heinzel_lets() if isinstance(let, PlaybookLet))
    (okr,) = playbook.assets
    assert okr.name == "okr"
    assert okr.hints[0].read == "documents.read"
    assert dict(okr.hints[0].args) == {"ref": OKR_DOCUMENT}
