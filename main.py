import flet as ft
from flet import (
    Page,
    Row,
    Column,
    Text,
    TextField,
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    )
import camelot.io as camelot
import pandas as pd
from pypdf import PdfReader

class PdfFileRow(Column):
    def __init__(self):
        super().__init__()
        self.pick_files_dialog = FilePicker(on_result=self.pick_files_result)
        self.selected_files = TextField(
            label='请指定要提取的PDF文件',
            multiline=True,
            on_focus=lambda _: self.pick_files_dialog.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["pdf"]
                    ),
            )
        self.handle_pages = TextField(label='请指定要提取的页码，用,分隔; 为空时将提取全部')
        self.transfer_btn = ElevatedButton("开始提取", disabled=True, on_click=self.transfer)
        self.reset_btn = ElevatedButton("重置", on_click=self.reset)
        self.log_show = Text('', selectable=True)
        self.controls = [
                self.selected_files,
                self.handle_pages,
                Row([self.transfer_btn, self.reset_btn,], alignment=ft.MainAxisAlignment.CENTER),
                Column([self.log_show], height=350, auto_scroll=True, scroll=ft.ScrollMode.AUTO)
                ]
        self.alignment=ft.MainAxisAlignment.START,
        self.horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    
    def reset(self, e):
        self.transfer_btn.text = '开始提取'
        self.transfer_btn.disabled = True

        self.selected_files.disabled = False
        self.selected_files.value = ''
        self.selected_files.label = '请指定要提取的PDF文件'

        self.handle_pages.value = ''
        self.log_show.value = ''

        self.reset_btn.disabled = False
        self.update()

    def transfer(self, e):
        self.transfer_btn.text = '提取中'
        self.transfer_btn.disabled = True
        self.transfer_btn.update()

        self.reset_btn.disabled = True
        self.reset_btn.update()

        try:
            pdf_path = self.selected_files.value
            xlsx_path = pdf_path[:-3] + 'xlsx'
            pages = self.handle_pages.value
            if pages is None or pages == '' :
                page_count = len(PdfReader(pdf_path).pages)
                pages = (','.join('%s' %i for i in list(range(1, page_count + 1))))
            tables = camelot.read_pdf(pdf_path, pages=pages)
            if tables is not None and len(tables) > 0:
                self.log_show.value = self.log_show.value + f"\n 共提取到{len(tables)}张表格"
                self.log_show.update()
                with pd.ExcelWriter(xlsx_path) as writer:
                    for table in tables:
                        self.log_show.value = self.log_show.value + f"\n 正在处理第{table.page}页表格"
                        self.log_show.update()
                        sheet_name = f"page-{table.page}-table-{table.order}"
                        table.df.to_excel(writer, sheet_name=sheet_name, index=False, header=None)
        
                self.log_show.value = self.log_show.value + f"\n 处理完成，Excel文件路径为：{xlsx_path}"
                self.log_show.update()

            else:
                self.log_show.value = self.log_show.value + "\n 未提取到表格，请重新指定文件"
                self.reset(None)
                return
        except Exception as e:
            self.log_show.value = self.log_show.value + f"\n 发生异常：{e}"

        self.reset_btn.disabled = False
        self.update()
        self.transfer_btn.text = '开始提取'
        self.transfer_btn.disabled = False
        self.transfer_btn.update()

    def pick_files_result(self, e: FilePickerResultEvent):
        self.selected_files.value = (
            ",".join(map(lambda f: f.path, e.files)) if e.files else ''
        )
        if self.selected_files.value == '': return
        self.selected_files.label = 'PDF文件路径'
        self.selected_files.disabled = True
        self.selected_files.update()

        self.transfer_btn.disabled = False
        self.transfer_btn.update()
    
    # happens when example is added to the page (when user chooses the FilePicker control from the grid)
    def did_mount(self):
        self.page.overlay.append(self.pick_files_dialog)
        self.page.update()
        
    # happens when example is removed from the page (when user chooses different control group on the navigation rail)
    def will_unmount(self):
        self.page.overlay.remove(self.pick_files_dialog)
        self.page.update()


def main(page: Page):
    page.title = "PDF提取表格数据工具"
    page.window_full_screen = False
    page.window_maximizable = False
    page.window_resizable = False
    page.window_height = 600
    page.window_width = 800
    
    pdf_file_row = PdfFileRow()
    page.add(pdf_file_row)
    


ft.app(target = main)
