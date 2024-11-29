import sys
import random
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QGraphicsTextItem, QPushButton, QVBoxLayout,
    QWidget, QStackedWidget, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPixmap

def create_database():
    conn = sqlite3.connect('sql.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS score (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        time INTEGER NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

class FoodropGame(QGraphicsView):
    def __init__(self, submit_callback):
        super().__init__()
        self.submit_callback = submit_callback 
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor(Qt.GlobalColor.white))
        self.setSceneRect(0, 0, 800, 600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.basket = QGraphicsRectItem(0, 0, 100, 20)
        self.basket.setPos(350, 580)
        self.basket.setBrush(QColor(Qt.GlobalColor.black))
        self.scene.addItem(self.basket)

        self.score = 0
        self.miss_score = 0
        self.score_text = QGraphicsTextItem(f'Счёт: {self.score} | Пропущено: {self.miss_score}/8')
        self.score_text.setPos(10, 10)
        self.scene.addItem(self.score_text)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGame)
        self.timer.start(100)
        self.game_duration = 0
        self.timer_display = QGraphicsTextItem(f'Время: {self.game_duration}')
        self.timer_display.setPos(10, 40)
        self.scene.addItem(self.timer_display)
        self.base_drop_speed = 5  
        self.speed_increment_time = 5  
        self.speed_increment_value = 1  
        self.food_items = []
        self.bonus_items = []

    def dropFood(self):
        food_types = ['img/apple.png', 'img/orange.jpg', 'img/banana.jpg']
        food_item = QGraphicsPixmapItem(QPixmap(random.choice(food_types)))
        food_item.setPos(random.randint(0, 700), 0)
        food_item.setScale(0.1)
        self.scene.addItem(food_item)
        self.food_items.append(food_item)

    def dropBonus(self):
        bonus_item = QGraphicsPixmapItem(QPixmap('img/banana.png')) 
        bonus_item.setPos(random.randint(0, 700), 0)
        bonus_item.setScale(0.1)
        self.scene.addItem(bonus_item)
        self.bonus_items.append(bonus_item)

    def updateGame(self):
        self.game_duration += 0.1
        self.timer_display.setPlainText(f'Время: {int(self.game_duration)}')
        if int(self.game_duration) % self.speed_increment_time == 0:
            self.base_drop_speed += self.speed_increment_value  
        for food_item in self.food_items:
            food_item.moveBy(0, self.base_drop_speed / 2)  
            if self.basket.collidesWithItem(food_item):
                self.score += 1 
                self.score_text.setPlainText(f'Счёт: {self.score} | Пропущено: {self.miss_score}/8')  
                self.scene.removeItem(food_item)  
                self.food_items.remove(food_item) 
                del food_item  
            elif food_item.y() > 600:
                self.miss_score += 1  
                self.score_text.setPlainText(f'Счёт: {self.score} | Пропущено: {self.miss_score}/8') 
                self.scene.removeItem(food_item)
                self.food_items.remove(food_item)
                del food_item  
                if self.miss_score >= 8:
                    self.showNameInput()
        for bonus_item in self.bonus_items:
            bonus_item.moveBy(0, 5)  
            if self.basket.collidesWithItem(bonus_item):
                pixmap = bonus_item.pixmap()
                if not pixmap.isNull() and pixmap.cacheKey() == QPixmap('img/banana.png').cacheKey():
                    self.scene.removeItem(bonus_item)  
                    self.bonus_items.remove(bonus_item)  
                    del bonus_item  
                    if self.miss_score > 0:
                        self.miss_score -= 1
                    self.score_text.setPlainText(f'Счёт: {self.score} | Пропущено: {self.miss_score}/8') 

        for bonus_item in self.bonus_items:
            if bonus_item.y() > 600:
                self.scene.removeItem(bonus_item)
                self.bonus_items.remove(bonus_item)
                del bonus_item
        if len(self.food_items) < 5:  
            self.dropFood()
        bonus_chance = 0.01 + (self.game_duration // 10) * 0.01  
        if random.random() < bonus_chance:  
            self.dropBonus()

    def showNameInput(self):
        self.timer.stop()
        name_input_screen = NameInputScreen(self.game_duration, self.submit_callback)
        name_input_screen.show()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Left:
            self.basket.moveBy(-10, 0)
        elif key == Qt.Key.Key_Right:
            self.basket.moveBy(10, 0)
        elif key == Qt.Key.Key_Escape:  
            self.timer.stop()  
            self.scene.clear()  
            self.submit_callback("", self.score, None)

class GameOverScreen(QWidget):
    def __init__(self, restart_callback):
        super().__init__()
        self.setWindowTitle("Игра окончена!")
        self.game_over_label = QGraphicsTextItem("Игра окончена!")
        self.game_over_label.setDefaultTextColor(QColor(Qt.GlobalColor.red))
        self.game_over_label.setPos(350, 250) 
        self.restart_button = QPushButton("Перезапустить игру")
        self.restart_button.clicked.connect(restart_callback)
        layout = QVBoxLayout()
        layout.addWidget(self.restart_button)
        self.setLayout(layout)

class NameInputScreen(QWidget):
    def __init__(self, game_duration, submit_callback):
        super().__init__()
        self.setWindowTitle("Введите своё имя")
        self.instruction_label = QLabel("Введите своё имя:")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ваше имя")
        self.submit_button = QPushButton("Отправить")
        self.submit_button.clicked.connect(lambda: submit_callback(self.name_input.text(), game_duration, self)) 
        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

class MainMenu(QWidget):
    def __init__(self, start_game_callback):
        super().__init__()
        self.setWindowTitle("Foodrop Game - Main Menu")
        self.setStyleSheet("QWidget { background-image: url('img/background_image.jpg'); }")  
        self.title_label = QLabel("FOODDROP")
        self.title_label.setStyleSheet("font-size: 30px; color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_button = QPushButton("Начать игру")
        self.start_button.setFixedSize(200, 60)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 20px;
                border: none;
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(start_game_callback)

        self.leaderboard_button = QPushButton("Посмотреть таблицу лидеров")
        self.leaderboard_button.setFixedSize(200, 60)
        self.leaderboard_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 20px;
                border: none;
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.leaderboard_button.clicked.connect(self.update_leaderboard)

        self.leaderboard_label = QLabel("Таблица лидеров:")
        self.leaderboard_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.leaderboard_text = QLabel("")
        self.leaderboard_text.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.leaderboard_button)
        layout.addWidget(self.leaderboard_label)
        layout.addWidget(self.leaderboard_text)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.update_leaderboard()

    def update_leaderboard(self):
        conn = sqlite3.connect('sql.db')
        c = conn.cursor()
        c.execute("SELECT name, time FROM score ORDER BY time ASC LIMIT 10")
        scores = c.fetchall()
        conn.close()

        leaderboard_text = ""
        for idx, (name, time) in enumerate(scores):
            leaderboard_text += f"{idx + 1}. {name} - {time} seconds\n"

        self.leaderboard_text.setText(leaderboard_text)

class GameApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.main_menu = MainMenu(self.start_game)
        self.game = FoodropGame(self.submit_score) 
        self.game_over = GameOverScreen(self.restart_game)

        self.addWidget(self.main_menu)
        self.addWidget(self.game)
        self.addWidget(self.game_over)
        self.setCurrentWidget(self.main_menu)

    def start_game(self):
        self.setCurrentWidget(self.game)

    def restart_game(self):
        self.game.score = 0
        self.game.miss_score = 0
        self.game.base_drop_speed = 5  
        self.game.speed_increment_time = 5  
        self.game.speed_increment_value = 1 
        self.game.score_text.setPlainText(f'Счёт: {self.game.score} | Пропущено: {self.game.miss_score}/8')
        self.game.timer_display.setPlainText(f'Время: {self.game.game_duration}')
        self.game.scene.clear()
        self.game.basket = QGraphicsRectItem(0, 0, 100, 20)  
        self.game.basket.setPos(350, 580)  
        self.game.basket.setBrush(QColor(Qt.GlobalColor.black)) 
        self.game.scene.addItem(self.game.basket)  
        self.game.scene.addItem(self.game.score_text) 
        self.game.scene.addItem(self.game.timer_display)  
        self.game.food_items.clear()
        self.game.bonus_items.clear()  
        self.game.timer.start(100) 
        self.game.game_duration = 0  
        self.setCurrentWidget(self.game)  

    def submit_score(self, name, game_duration, dialog):  # Change score to game_duration
        if name: 
            conn = sqlite3.connect('sql.db')
            c = conn.cursor()
            c.execute("INSERT INTO score (name, time) VALUES (?, ?)", (name, int(game_duration)))  # Use game_duration here
            conn.commit()
            conn.close()
            print("Ваш счёт зарегистрирован")
            dialog.close() 
            self.setCurrentWidget(self.game_over)  

if __name__ == '__main__':
    create_database()  
    app = QApplication(sys.argv)
    game_app = GameApp()
    game_app.resize(800, 600)
    game_app.show()
    sys.exit(app.exec())