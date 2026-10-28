from app import config


def test_static_dir_contains_markdown_files():
    assert config.STATIC_DIR.is_dir()
    assert list(config.STATIC_DIR.glob("*.md"))


def test_chunk_overlap_is_smaller_than_chunk_size():
    assert config.CHUNK_OVERLAP < config.CHUNK_SIZE


def test_chroma_dir_is_inside_the_project():
    assert config.CHROMA_DIR.parent == config.ROOT