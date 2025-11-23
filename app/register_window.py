# app/register_window.py
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from ui.ui_register import Ui_SignUpWindow
from backend.chatclient import ChatClient
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QPainter, QBitmap
from PyQt5.QtCore imcport Qt
from PyQt5.QtCore import QTimer
import os

class RegisterWindow(QtWidgets.QMainWindow, Ui_SignUpWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)  # Load giao diện từ Qt Designer
        self.client = ChatClient()
        self.avatar_path = None
        self._avatar_pixmap = None  # Giữ reference để tránh bị GC

        # Kết nối các nút trong UI với hàm xử lý
        self.signUpButton.clicked.connect(self.do_register)
        self.signInButton.clicked.connect(self.open_login)
        self.avatarLabel.mousePressEvent = self.choose_avatar  # Click để chọn ảnh

        # Gán avatar mặc định nếu có
        default_avatar = os.path.join("avatars", "default.jpg")
        if os.path.exists(default_avatar):
            self._set_avatar_pixmap(default_avatar)
        else:
            self.avatarLabel.setText("Click to select avatar")

    def _set_avatar_pixmap(self, filepath):
        """Load ảnh, bo tròn và hiển thị trong avatarLabel."""
        try:
            pix = QPixmap(filepath)
            if pix.isNull():
                self.avatarLabel.setText("Invalid image")
                return

            # Scale avatar
            pix = pix.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

            # Bo tròn bằng mask
            mask = QBitmap(120, 120)
            mask.fill(Qt.color0)
            painter = QPainter(mask)
            painter.setBrush(Qt.color1)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 120, 120)
            painter.end()
            pix.setMask(mask)

            # Gán lên label
            self._avatar_pixmap = pix
            self.avatarLabel.setPixmap(self._avatar_pixmap)
            self.avatarLabel.setText("")  # Xóa text placeholder
            self.avatarLabel.setStyleSheet("""
                QLabel {
                    border: 2px solid #4A90E2;
                    border-radius: 60px;
                    background-color: white;
                }
                QLabel:hover {
                    border: 2px solid #5AA0F2;
                }
            """)
        except Exception as e:
            print("Avatar load error:", e)
            self.avatarLabel.setText("Click to select avatar")

    def choose_avatar(self, event):
        """Chọn ảnh đại diện (mở file dialog)."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh đại diện", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file:
            self.avatar_path = file
            self._set_avatar_pixmap(file)

    def do_register(self):
        """Gửi thông tin đăng ký tới server."""
        user = self.nameInput.text().strip()
        pw = self.passwordInput.text().strip()
        cf = self.confirmInput.text().strip()

        if not user or not pw or not cf:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin!")
            return

        if pw != cf:
            QMessageBox.critical(self, "Lỗi", "Mật khẩu không khớp!")
            return

        avatar = self.avatar_path if self.avatar_path else "avatars/default.jpg"

        try:
            self.client.connect()
            self.client.on_message = self.handle_server_message
            self.client.register(user, pw, avatar)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể kết nối tới server: {e}")

    def handle_server_message(self, message):
        """Nhận phản hồi từ server."""
        if "REGISTER_OK" in message:
            QMessageBox.information(self, "Thành công", "Đăng ký thành công!")

            # Delay 100ms trước khi mở login, tránh crash do QMessageBox đang active
            QTimer.singleShot(100, self.open_login)

        elif "REGISTER_FAIL" in message:
            QMessageBox.warning(self, "Lỗi", "Tên người dùng đã tồn tại!")

    def open_login(self):
        """Chuyển sang giao diện đăng nhập"""
        from app.login_window import LoginWindow  # import chéo
        self.login_window = LoginWindow()
        self.login_window.show()
        self.hide()   # ẩn thay vì đóng

