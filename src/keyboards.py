from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .models import Task, Category, Priority

def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Добавить задачу"),
                KeyboardButton(text="📋 Список задач")
            ],
            [
                KeyboardButton(text="✅ Выполненные"),
                KeyboardButton(text="❌ Удалить задачу")
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="ℹ️ Помощь")
            ],
            [
                KeyboardButton(text="📁 Категории"),
                KeyboardButton(text="⚙️ Настройки")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_task_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    keyboard = []
    for task in tasks:
        priority_emoji = {
            Priority.LOW: "⬇️",
            Priority.MEDIUM: "➡️",
            Priority.HIGH: "⬆️"
        }[task.priority]
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{'✅' if task.is_completed else '⏳'} {priority_emoji} {task.title}",
                callback_data=f"task_{task.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_task_actions_keyboard(task: Task) -> InlineKeyboardMarkup:
    keyboard = []
    
    if not task.is_completed:
        keyboard.append([
            InlineKeyboardButton(
                text="✅ Отметить как выполненную",
                callback_data=f"complete_{task.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_{task.id}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Удалить задачу",
            callback_data=f"delete_{task.id}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад к списку",
            callback_data="back_to_list"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_priority_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="⬆️ Высокий",
                callback_data="priority_high"
            )
        ],
        [
            InlineKeyboardButton(
                text="➡️ Средний",
                callback_data="priority_medium"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬇️ Низкий",
                callback_data="priority_low"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🎨 {category.name}",
                callback_data=f"category_{category.id}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text="➕ Добавить категорию",
            callback_data="add_category"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔔 Настройки уведомлений",
                callback_data="notification_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="📤 Экспорт задач",
                callback_data="export_tasks"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Импорт задач",
                callback_data="import_tasks"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_edit_task_keyboard(task: Task) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Название",
                callback_data=f"edit_title_{task.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Описание",
                callback_data=f"edit_description_{task.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Дата",
                callback_data=f"edit_date_{task.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Приоритет",
                callback_data=f"edit_priority_{task.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📁 Категория",
                callback_data=f"edit_category_{task.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"task_{task.id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 