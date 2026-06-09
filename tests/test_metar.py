from solarstorm.data._metar import parse_tmp_c_int_from_row


def test_parse_standard_metar_positive():
    tt, dwp, dq, _ = parse_tmp_c_int_from_row(
        "NZWN 150300Z AUTO 36015KT 9999 FEW020 18/12 Q1015",
        tmpf=None,
    )
    assert tt == 18
    assert dwp == 12
    assert dq == "ok"


def test_parse_metar_negative_temperature():
    tt, dwp, dq, _ = parse_tmp_c_int_from_row(
        "NZWN 150300Z AUTO 36005KT 9999 FEW030 M02/M05 Q1020",
        tmpf=None,
    )
    assert tt == -2
    assert dwp == -5
    assert dq == "ok"


def test_parse_metar_blank_falls_back_to_tmpf():
    tt, dwp, dq, implausible = parse_tmp_c_int_from_row(
        "NZWN 150300Z AUTO 36005KT 9999 FEW030",
        tmpf=68.0,   # 20.0°C
    )
    assert tt == 20
    assert dwp is None
    assert dq == "imputed"
    assert not implausible


def test_parse_metar_missing_all():
    tt, dwp, dq, implausible = parse_tmp_c_int_from_row(
        None, tmpf=None,
    )
    assert tt is None
    assert dwp is None
    assert dq == "missing"
    assert not implausible


def test_parse_metar_implausible_temperature():
    tt, _, dq, implausible = parse_tmp_c_int_from_row(
        "NZWN 150300Z AUTO 36005KT 9999 FEW020 55/12 Q1015",
        tmpf=None,
    )
    assert tt is None
    assert dq == "missing"
    assert implausible


def test_parse_metar_temp_group_at_end_of_string():
    """TT/DD as the final token (no trailing space) must still parse as 'ok'
    via integer-truth, not silently fall back to tmpf imputation."""
    tt, dwp, dq, _ = parse_tmp_c_int_from_row(
        "NZWN 150300Z AUTO 36015KT 9999 FEW020 18/12",
        tmpf=99.9,  # would mis-impute to 38°C if the regex misses the group
    )
    assert tt == 18
    assert dwp == 12
    assert dq == "ok"
