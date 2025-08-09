import pandas as pd
from api.services.parser import NeppanCSVParser


def test_number_columns_conversion(tmp_path):
    csv_content = (
        "予約ID,予約区分,チェックイン日,チェックアウト日,予約サイト名称,部屋タイプ名称,宿泊者名,大人人数計,子供人数計,幼児人数計\n"
        "1,通常,2024/01/01,2024/01/02,テストサイト,テスト部屋,山田太郎,2,1,1\n"
    )
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    parser = NeppanCSVParser(str(csv_file), encoding="utf-8")
    df, errors = parser.parse()

    assert errors == []
    assert df.loc[0, "num_adults"] == 2
    assert df.loc[0, "num_children"] == 1
    assert df.loc[0, "num_infants"] == 1
    assert pd.api.types.is_numeric_dtype(df["num_adults"])
    assert pd.api.types.is_numeric_dtype(df["num_children"])
    assert pd.api.types.is_numeric_dtype(df["num_infants"])
