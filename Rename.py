import os
import re
import sys
from pathlib import Path

from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QFileDialog,
                             QTableWidget, QTableWidgetItem, QLabel, QHeaderView)

ChangedColor = QColor(131, 203, 172)
UnsafeColor = QColor(231, 124, 142)
UnsafeStr = ['?', '-']


class BatchRenameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("批量重命名工具")
        self.setGeometry(100, 100, 800, 600)

        # 初始化变量
        self.directory: Path = None
        self.files: list[Path] = []
        self.history: list[list[Path]] = []

        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 文件夹选择部分
        folder_layout = QHBoxLayout()
        # 设置文件夹选择输入框
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("选择文件夹路径...")
        self.folder_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_input)
        # 设置文件夹选择按钮
        folder_button = QPushButton("选择文件夹")
        folder_button.clicked.connect(self.select_folder)  # type: ignore
        folder_layout.addWidget(folder_button)
        # 设置重命名按钮
        rename_button = QPushButton("执行重命名")
        rename_button.clicked.connect(self.rename_files)  # noqa: F821
        folder_layout.addWidget(rename_button)
        # 设置刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_files)
        folder_layout.addWidget(refresh_button)
        # 设置撤销按钮
        undo_button = QPushButton("撤销")
        undo_button.clicked.connect(self.undo)
        folder_layout.addWidget(undo_button)

        layout.addLayout(folder_layout)

        # 正则表达式输入部分
        pattern_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("输入正则表达式模式...")
        self.pattern_input.textChanged.connect(self.update_preview)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("输入替换字符串...")
        self.replace_input.textChanged.connect(self.update_preview)
        pattern_layout.addWidget(QLabel("正则表达式:"))
        pattern_layout.addWidget(self.pattern_input)
        pattern_layout.addWidget(QLabel("替换为:"))
        pattern_layout.addWidget(self.replace_input)
        layout.addLayout(pattern_layout)

        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["原始文件名", "新文件名"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.preview_table)

    def refresh_files(self):
        """刷新文件列表"""
        if not self.directory:
            return
        # 列出文件
        self.files = [f for f in self.directory.glob("*") if f.is_file()]
        self.update_preview()

    def select_folder(self):
        """选择文件夹并加载文件列表"""
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if directory:
            self.directory = Path(directory)
            self.folder_input.setText(directory)
            self.refresh_files()

    def undo(self):
        """撤销重命名操作"""
        if not self.history:
            return

        want_files = self.history.pop()
        if len(want_files) != len(self.files):
            return

        for file, old_file in zip(self.files, want_files):
            try:
                os.rename(file, old_file)
            except OSError:
                continue

        self.refresh_files()

    def update_preview(self):
        """更新预览表格，显示重命名效果"""
        self.preview_table.setRowCount(0)
        if not self.directory or not self.files:
            return

        patternStr = self.pattern_input.text()
        replacement = self.replace_input.text()

        # 测试正则表达式是否有效
        try:
            pattern = re.compile(patternStr)
        except re.error:
            pattern = None
        # \[偽MIDI泥の会 \(石恵)]
        self.preview_table.setRowCount(len(self.files))
        for row, file in enumerate(self.files):
            # 原始文件名
            original_item = QTableWidgetItem(file.name)
            self.preview_table.setItem(row, 0, original_item)

            # 新文件名
            try:
                new_filename = re.sub(pattern, replacement, file.name)
            except TypeError:
                self.preview_table.setItem(row, 1, QTableWidgetItem("无效的正则表达式"))
            else:
                new_item = QTableWidgetItem(new_filename)
                if new_filename != file.name:
                    color = UnsafeColor if any([i in new_filename for i in UnsafeStr]) else ChangedColor
                    # 高亮变化的文件名
                    new_item.setForeground(color)
                    font = QFont()
                    font.setBold(True)
                    new_item.setFont(font)
                self.preview_table.setItem(row, 1, new_item)

    def rename_files(self):
        """执行重命名操作"""
        pattern = self.pattern_input.text()
        replacement = self.replace_input.text()

        try:
            re.compile(pattern)
        except re.error:
            return

        self.history.append(self.files)

        for file in self.files:
            try:
                new_filename = re.sub(pattern, replacement, file.name)
                if new_filename != file.name:
                    os.rename(
                        file,
                        self.directory.joinpath(new_filename)
                    )
            except (re.error, OSError):
                continue

        # 刷新文件列表
        self.refresh_files()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BatchRenameApp()
    window.show()
    sys.exit(app.exec())
