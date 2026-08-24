import os
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.results_loader import discover_additional_data_dirs, find_result_files, load_results_dataframe


def _write_minimal_docx(path, table_rows=None, paragraphs=None):
    table_rows = table_rows or []
    paragraphs = paragraphs or []

    body_parts = []
    for paragraph in paragraphs:
        body_parts.append(
            f"<w:p><w:r><w:t>{escape(paragraph)}</w:t></w:r></w:p>"
        )

    for row in table_rows:
        row_xml = []
        for cell in row:
            row_xml.append(
                "<w:tc><w:p><w:r><w:t>{}</w:t></w:r></w:p></w:tc>".format(escape(cell))
            )
        body_parts.append(f"<w:tbl><w:tr>{''.join(row_xml)}</w:tr></w:tbl>")

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body_parts)}</w:body>"
        '</w:document>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        '</Relationships>'
    )

    with zipfile.ZipFile(path, 'w') as docx_zip:
        docx_zip.writestr('[Content_Types].xml', content_types)
        docx_zip.writestr('_rels/.rels', rels)
        docx_zip.writestr('word/document.xml', document_xml)


def test_csv_results_load():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir)

        csv_path = os.path.join(data_dir, 'results_2026-05-31.csv')
        with open(csv_path, 'w', encoding='utf-8') as handle:
            handle.write("Track,Date,Race,Winner,2nd,3rd,4th\n")
            handle.write("Richmond,2026-05-31,1,2,1,6,3\n")
            handle.write("Gunnedah,2026-05-31,2,1,6,2,4\n")

        df = load_results_dataframe(data_dir)
        assert len(df) == 2
        assert list(df['Track']) == ['Gunnedah', 'Richmond'] or list(df['Track']) == ['Richmond', 'Gunnedah']
        assert set(df['Winner']) == {1, 2}


def test_docx_results_load():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir)

        docx_path = os.path.join(data_dir, '31052026RESULTS.docx')
        _write_minimal_docx(
            docx_path,
            table_rows=[['Richmond31/05/2026', 'R12163', 'R28672', 'R102615']]
        )

        df = load_results_dataframe(data_dir)
        assert len(df) == 3
        assert list(df['Date'].unique()) == ['2026-05-31']
        assert df.loc[df['RaceNumber'] == 10, '4th'].iloc[0] == 5


def test_mixed_results_deduplicate_csv_over_docx():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        outputs_dir = os.path.join(temp_dir, 'outputs')
        os.makedirs(data_dir)
        os.makedirs(outputs_dir)

        csv_path = os.path.join(data_dir, 'results_2026-05-31.csv')
        with open(csv_path, 'w', encoding='utf-8') as handle:
            handle.write("Track,Date,Race,Winner,2nd,3rd,4th\n")
            handle.write("Richmond,2026-05-31,1,2,1,6,3\n")

        docx_path = os.path.join(outputs_dir, '31052026RESULTS.docx')
        _write_minimal_docx(
            docx_path,
            table_rows=[['Richmond31/05/2026', 'R12163', 'R28672']]
        )

        result_files = find_result_files(data_dir)
        assert docx_path in result_files

        df = load_results_dataframe(data_dir)
        assert len(df) == 2
        assert df.loc[df['RaceNumber'] == 1, '_source_format'].iloc[0] == 'csv'
        assert df.loc[df['RaceNumber'] == 2, '_source_format'].iloc[0] == 'docx'


def test_malformed_docx_is_skipped():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir)

        csv_path = os.path.join(data_dir, 'results_2026-05-31.csv')
        with open(csv_path, 'w', encoding='utf-8') as handle:
            handle.write("Track,Date,Race,Winner,2nd,3rd,4th\n")
            handle.write("Richmond,2026-05-31,1,2,1,6,3\n")

        broken_docx = os.path.join(data_dir, '31052026RESULTS.docx')
        with open(broken_docx, 'wb') as handle:
            handle.write(b'not-a-real-docx')

        df = load_results_dataframe(data_dir)
        assert len(df) == 1
        assert df.iloc[0]['Track'] == 'Richmond'


def test_discover_additional_data_dirs_orders_numeric_suffix():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir)
        os.makedirs(os.path.join(temp_dir, 'data2'))
        os.makedirs(os.path.join(temp_dir, 'data10'))
        os.makedirs(os.path.join(temp_dir, 'data4'))
        os.makedirs(os.path.join(temp_dir, 'data_predictions'))

        discovered = discover_additional_data_dirs(data_dir)
        assert discovered == [
            os.path.join(temp_dir, 'data2'),
            os.path.join(temp_dir, 'data4'),
            os.path.join(temp_dir, 'data10'),
        ]


def test_find_result_files_auto_includes_data_directories():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        data4_dir = os.path.join(temp_dir, 'data4')
        os.makedirs(data_dir)
        os.makedirs(data4_dir)

        with open(os.path.join(data4_dir, 'results_2026-06-30.csv'), 'w', encoding='utf-8') as handle:
            handle.write("Track,Date,Race,Winner,2nd,3rd,4th\n")
            handle.write("Richmond,2026-06-30,1,2,1,3,4\n")

        result_files = find_result_files(data_dir)
        assert os.path.join(data4_dir, 'results_2026-06-30.csv') in result_files


if __name__ == "__main__":
    test_csv_results_load()
    print("✅ test_csv_results_load passed")
    test_docx_results_load()
    print("✅ test_docx_results_load passed")
    test_mixed_results_deduplicate_csv_over_docx()
    print("✅ test_mixed_results_deduplicate_csv_over_docx passed")
    test_malformed_docx_is_skipped()
    print("✅ test_malformed_docx_is_skipped passed")
    test_discover_additional_data_dirs_orders_numeric_suffix()
    print("✅ test_discover_additional_data_dirs_orders_numeric_suffix passed")
    test_find_result_files_auto_includes_data_directories()
    print("✅ test_find_result_files_auto_includes_data_directories passed")
