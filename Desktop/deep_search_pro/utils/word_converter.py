import logging
import time
from pathlib import Path

import markdown as md

try:
    import pythoncom
    import win32com.client

    _HAS_WORD_COM = True
except ImportError:
    _HAS_WORD_COM = False


def convert_md_to_pdf_via_word(md_abs_path: Path, pdf_abs_path: Path) -> str:
    """
    使用 Microsoft Word COM 接口将 Markdown 转换为 PDF。
    依赖：pip install markdown pywin32；Windows 上需安装 Microsoft Word。
    """
    if not _HAS_WORD_COM:
        return "缺少依赖库，请安装: pip install pywin32（且需已安装 Microsoft Word）"

    temp_html_path = md_abs_path.with_suffix(".temp.html")
    word_app = None

    try:
        with open(md_abs_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_body = md.markdown(md_content, extensions=["tables", "fenced_code"])
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: "Microsoft YaHei", "SimHei", sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid black; padding: 8px; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; }}
                code {{ font-family: "Consolas", "Monaco", monospace; }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pythoncom.CoInitialize()
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = False

        doc = word_app.Documents.Open(str(temp_html_path.resolve()))
        doc.SaveAs(str(pdf_abs_path.resolve()), FileFormat=17)  # wdFormatPDF = 17
        doc.Close(SaveChanges=0)

        if pdf_abs_path.exists():
            return f"成功转换: {pdf_abs_path} (Word引擎)"
        return f"转换完成但未生成文件: {pdf_abs_path}"

    except Exception as e:
        logging.error("Word转换PDF失败: %s", e, exc_info=True)
        return f"转换失败: {str(e)}"

    finally:
        if word_app:
            try:
                word_app.Quit()
            except Exception:
                pass

        if temp_html_path.exists():
            try:
                temp_html_path.unlink()
            except Exception:
                pass

        if _HAS_WORD_COM:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
