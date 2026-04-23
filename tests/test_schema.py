from pydantic import ValidationError
import pytest

from report_engine.schema import Attachment, AttachmentsBundle, Block, Payload, Section


def test_block_accepts_extra_fields():
    block = Block(type="heading", text="标题", level=2)
    assert block.type == "heading"
    assert block.text == "标题"
    assert block.level == 2


def test_block_requires_type():
    with pytest.raises(ValidationError):
        Block()


def test_section_defaults():
    section = Section(id="research", placeholder="RESEARCH_SUBDOC")
    assert section.enabled is True
    assert section.blocks == []
    assert section.subdoc_title_level == 2


def test_attachment_defaults():
    attachment = Attachment(id="app1", placeholder="APP1_SUBDOC")
    assert attachment.enabled is True
    assert attachment.blocks == []
    assert attachment.title_level == 2


def test_attachments_bundle_defaults():
    bundle = AttachmentsBundle()
    assert bundle.placeholder == "APPENDICES_SUBDOC"
    assert bundle.flag_name == "ENABLE_APPENDICES"
    assert bundle.page_break_between_attachments is True


def test_payload_defaults():
    payload = Payload(context={"PROJECT_NAME": "测试"})
    assert payload.sections == []
    assert payload.attachments == []
    assert payload.style_map == {}
