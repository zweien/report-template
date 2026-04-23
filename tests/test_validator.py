import pytest

from report_engine.validator import PayloadValidationError, validate_payload


def test_validate_payload_accepts_advanced_payload(advanced_payload):
    model, warnings = validate_payload(advanced_payload)
    assert model.context["PROJECT_NAME"] == "测试项目"
    assert isinstance(warnings, list)


def test_validate_payload_warns_for_missing_image():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "s1",
                "placeholder": "S1_SUBDOC",
                "blocks": [{"type": "image", "path": "missing.png"}],
            }
        ],
    }
    _, warnings = validate_payload(payload)
    assert warnings
    assert "image not found" in warnings[0]


def test_validate_payload_strict_images_errors():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "s1",
                "placeholder": "S1_SUBDOC",
                "blocks": [{"type": "image", "path": "missing.png"}],
            }
        ],
    }
    with pytest.raises(PayloadValidationError, match="image not found"):
        validate_payload(payload, strict_images=True)


def test_validate_payload_rejects_duplicate_section_id():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {"id": "dup", "placeholder": "A_SUBDOC", "blocks": []},
            {"id": "dup", "placeholder": "B_SUBDOC", "blocks": []},
        ],
    }
    with pytest.raises(PayloadValidationError, match="Duplicate section id"):
        validate_payload(payload)


def test_validate_payload_rejects_unsupported_block_type():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {"id": "s1", "placeholder": "S1_SUBDOC", "blocks": [{"type": "weird"}]},
        ],
    }
    with pytest.raises(PayloadValidationError, match="unsupported block type"):
        validate_payload(payload)
