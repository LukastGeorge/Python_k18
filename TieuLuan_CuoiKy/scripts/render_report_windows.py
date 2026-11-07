"""Use the canonical DOCX renderer with bundled PDFium on Windows without Poppler."""
import importlib.util
import argparse
import os
from pathlib import Path
import tempfile
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.tools/kingcounty-20261107'
SKILL = Path('C:/Users/Truong Nguyen/.codex/plugins/cache/openai-primary-runtime/documents/26.1105.12137/skills/documents')
LO = Path('C:/Users/Truong Nguyen/.codex/visualizations/2026/10/09/01a1210b-9b44-7872-a3ec-c32f5369c69c/render-tools/LibreOffice-extracted/LibreOffice/program')


def pdfium_convert(pdf_path, *, dpi, output_folder, output_file='page', **kwargs):
    """Implement the renderer's image conversion contract using supplied PDFium."""
    doc = pdfium.PdfDocument(pdf_path)
    paths, texts = [], []
    for i in range(len(doc)):
        page = doc[i]
        image = page.render(scale=dpi / 72).to_pil()
        path = Path(output_folder) / (output_file + '0001-' + str(i + 1) + '.png')
        image.save(path)
        paths.append(str(path))
        text = page.get_textpage().get_text_range()
        texts.append(f'PAGE {i + 1}\n{text}\n')
        print('Rendered report page', i + 1, flush=True)
    (Path(output_folder) / 'page-text.txt').write_text('\n'.join(texts), encoding='utf-8')
    doc.close()
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'TieuLuan_CuoiKy/docs/Bao_cao_Phan_tich_Gia_nha_King_County.docx')
    parser.add_argument('--work', type=Path, default=WORK)
    parser.add_argument('--dpi', type=int, default=140)
    args = parser.parse_args()
    temporary = args.work / 'render-temp'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temporary)
    tempfile.tempdir = str(temporary)
    # LibreOffice can briefly retain its Windows profile files after export.
    # Ignore only profile-cleanup races; conversion and rendering errors still fail.
    native_temporary_directory = tempfile.TemporaryDirectory
    class WindowsTemporaryDirectory(native_temporary_directory):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('ignore_cleanup_errors', True)
            super().__init__(*args, **kwargs)
    tempfile.TemporaryDirectory = WindowsTemporaryDirectory
    os.environ['PATH'] = str(LO) + os.pathsep + os.environ['PATH']
    spec = importlib.util.spec_from_file_location('canonical_docx_renderer', SKILL / 'render_docx.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.convert_from_path = pdfium_convert
    paths = renderer.rasterize(str(args.input),
        str(args.work / 'report-preview'), dpi=args.dpi, verbose=True, emit_pdf=True)
    print('Canonical renderer completed with PDFium:', len(paths), 'pages')


if __name__ == '__main__':
    main()
