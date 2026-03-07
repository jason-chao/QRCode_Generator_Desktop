"""Unit tests for qrcode_gen.py (pure functions only — no display required)."""

import configparser
import os

import pytest
from PIL import Image

import qrcode as _qrcode

# ---------------------------------------------------------------------------
# Import helpers under test
# ---------------------------------------------------------------------------

from qrcode_gen import (
    ec_label_for,
    generate_qr_image,
    is_valid_hex,
    load_config,
    normalise_colour,
)


# ---------------------------------------------------------------------------
# ec_label_for
# ---------------------------------------------------------------------------

class TestEcLabelFor:
    def test_all_valid_uppercase(self):
        assert ec_label_for("L") == "L  –  7%"
        assert ec_label_for("M") == "M  – 15%"
        assert ec_label_for("Q") == "Q  – 25%"
        assert ec_label_for("H") == "H  – 30%"

    def test_lowercase_input(self):
        assert ec_label_for("l") == "L  –  7%"
        assert ec_label_for("m") == "M  – 15%"
        assert ec_label_for("q") == "Q  – 25%"
        assert ec_label_for("h") == "H  – 30%"

    def test_unknown_defaults_to_m(self):
        assert ec_label_for("X") == "M  – 15%"
        assert ec_label_for("") == "M  – 15%"


# ---------------------------------------------------------------------------
# is_valid_hex
# ---------------------------------------------------------------------------

class TestIsValidHex:
    @pytest.mark.parametrize("value", [
        "#abc", "#ABC", "#abcdef", "#ABCDEF", "#1a2b3c",
        "abc", "abcdef",          # without leading #
    ])
    def test_valid(self, value):
        assert is_valid_hex(value) is True

    @pytest.mark.parametrize("value", [
        "#abcd",        # 4 hex digits
        "#ab",          # 2 hex digits
        "#abcdefg",     # 7 hex digits
        "#gggggg",      # invalid characters
        "gggggg",       # invalid without #
        "",             # empty
        "#",            # only hash
        "not-a-colour",
    ])
    def test_invalid(self, value):
        assert is_valid_hex(value) is False


# ---------------------------------------------------------------------------
# normalise_colour
# ---------------------------------------------------------------------------

class TestNormaliseColour:
    def test_transparent_returns_none(self):
        assert normalise_colour("transparent") is None
        assert normalise_colour("TRANSPARENT") is None
        assert normalise_colour("  transparent  ") is None

    @pytest.mark.parametrize("name", [
        "black", "white", "red", "green", "blue",
        "yellow", "cyan", "magenta", "orange", "purple", "gray",
    ])
    def test_named_colours(self, name):
        assert normalise_colour(name) == name

    def test_hex_with_hash(self):
        assert normalise_colour("#ff0000") == "#ff0000"
        assert normalise_colour("#ABC123") == "#ABC123"

    def test_hex_without_hash_gets_prefixed(self):
        assert normalise_colour("ff0000") == "#ff0000"
        assert normalise_colour("abc") == "#abc"

    def test_unknown_returns_none(self):
        assert normalise_colour("notacolour") is None
        assert normalise_colour("#zzzzzz") is None


# ---------------------------------------------------------------------------
# generate_qr_image
# ---------------------------------------------------------------------------

EC_M = _qrcode.constants.ERROR_CORRECT_M


class TestGenerateQrImage:
    def test_returns_pil_image(self):
        img = generate_qr_image("https://example.com", "black", "white", EC_M, 10, 4)
        assert isinstance(img, Image.Image)

    def test_image_mode_is_rgba(self):
        img = generate_qr_image("https://example.com", "black", "white", EC_M, 10, 4)
        assert img.mode == "RGBA"

    def test_transparent_background(self):
        img = generate_qr_image("https://example.com", "black", None, EC_M, 10, 4)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"

    def test_box_size_affects_dimensions(self):
        small = generate_qr_image("hi", "black", "white", EC_M, 5, 4)
        large = generate_qr_image("hi", "black", "white", EC_M, 10, 4)
        assert large.size[0] > small.size[0]
        assert large.size[1] > small.size[1]

    def test_border_affects_dimensions(self):
        narrow = generate_qr_image("hi", "black", "white", EC_M, 10, 1)
        wide   = generate_qr_image("hi", "black", "white", EC_M, 10, 8)
        assert wide.size[0] > narrow.size[0]

    @pytest.mark.parametrize("ec_level", [
        _qrcode.constants.ERROR_CORRECT_L,
        _qrcode.constants.ERROR_CORRECT_M,
        _qrcode.constants.ERROR_CORRECT_Q,
        _qrcode.constants.ERROR_CORRECT_H,
    ])
    def test_all_error_correction_levels(self, ec_level):
        img = generate_qr_image("https://example.com", "black", "white", ec_level, 10, 4)
        assert isinstance(img, Image.Image)

    def test_empty_string_produces_image(self):
        # The qrcode library encodes empty data without error; the UI layer
        # is responsible for rejecting blank input before it reaches here.
        img = generate_qr_image("", "black", "white", EC_M, 10, 4)
        assert isinstance(img, Image.Image)

    def test_overlong_data_raises(self):
        # QR codes top out at version 40; data exceeding that capacity raises ValueError.
        with pytest.raises((ValueError, Exception)):
            generate_qr_image("x" * 10000, "black", "white", EC_M, 10, 4)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_defaults_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("qrcode_gen.CONFIG_FILE", str(tmp_path / "no_such.ini"))
        cfg = load_config()
        assert cfg["url"] == "https://github.com/jason-chao/QRCode_Generator_Desktop"
        assert cfg["foreground"] == "black"
        assert cfg["background"] == "white"
        assert cfg["error_correction"] == "M"
        assert cfg["box_size"] == "10"
        assert cfg["border"] == "4"

    def test_reads_values_from_file(self, tmp_path, monkeypatch):
        ini = tmp_path / "config.ini"
        ini.write_text(
            "[defaults]\n"
            "url = https://pytest.org\n"
            "foreground = red\n"
            "background = white\n"
            "error_correction = H\n"
            "box_size = 5\n"
            "border = 2\n"
        )
        monkeypatch.setattr("qrcode_gen.CONFIG_FILE", str(ini))
        cfg = load_config()
        assert cfg["url"] == "https://pytest.org"
        assert cfg["foreground"] == "red"
        assert cfg["background"] == "white"
        assert cfg["error_correction"] == "H"
        assert cfg["box_size"] == "5"
        assert cfg["border"] == "2"

    def test_partial_config_uses_defaults_for_missing_keys(self, tmp_path, monkeypatch):
        ini = tmp_path / "config.ini"
        ini.write_text("[defaults]\nurl = https://partial.example\n")
        monkeypatch.setattr("qrcode_gen.CONFIG_FILE", str(ini))
        cfg = load_config()
        assert cfg["url"] == "https://partial.example"
        assert cfg["foreground"] == "black"   # default
        assert cfg["box_size"] == "10"         # default
