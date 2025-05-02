import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import User, Task, Category, Priority, UserCategory
from .keyboards import (
    get_main_keyboard, get_task_keyboard, get_task_actions_keyboard,
    get_priority_keyboard, get_categories_keyboard, get_settings_keyboard,
    get_edit_task_keyboard
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_due_date = State()
    waiting_for_priority = State()
    waiting_for_category = State()
    waiting_for_task_to_delete = State()
    waiting_for_task_to_complete = State()
    waiting_for_category_name = State()
    waiting_for_category_color = State()
    waiting_for_notification_time = State()
    waiting_for_edit_title = State()
    waiting_for_edit_description = State()
    waiting_for_edit_date = State()
    waiting_for_edit_priority = State()
    waiting_for_edit_category = State()

@router.message(Command("start"))
async def cmd_start(message: Message, session: Session):
    # Ищем пользователя в базе данных
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Создаем нового пользователя
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        session.add(user)
        await session.commit()
    
    await message.answer(
        "👋 Привет! Я твой персональный ToDo бот!\n\n"
        "Вот что я умею:\n"
        "📝 /add - Добавить новую задачу\n"
        "📋 /list - Показать список задач\n"
        "✅ /done - Отметить задачу как выполненную\n"
        "❌ /delete - Удалить задачу",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_title)
    await message.answer("📝 Введите название задачи:")

@router.message(TaskStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_for_description)
    await message.answer("📝 Теперь введите описание задачи (или отправьте '-' если описание не нужно):")

@router.message(TaskStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    await state.update_data(description=description)
    await state.set_state(TaskStates.waiting_for_due_date)
    await message.answer("📅 Введите дату выполнения в формате ДД.ММ.ГГГГ (или отправьте '-' если дата не нужна):")

@router.message(TaskStates.waiting_for_due_date)
async def process_due_date(message: Message, state: FSMContext, session: Session):
    data = await state.get_data()
    
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one()
    
    due_date = None
    if message.text != "-":
        try:
            due_date = datetime.strptime(message.text, "%d.%m.%Y")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Попробуйте еще раз.")
            return
    
    task = Task(
        user_id=user.id,
        title=data["title"],
        description=data["description"],
        due_date=due_date
    )
    
    session.add(task)
    await session.commit()
    
    await state.clear()
    await message.answer(
        "✅ Задача успешно добавлена!",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("list"))
async def cmd_list(message: Message, session: Session):
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one()
    
    result = await session.execute(
        select(Task).where(Task.user_id == user.id)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await message.answer("📋 У вас пока нет задач!")
        return
    
    text = "📋 Ваши задачи:\n\n"
    for task in tasks:
        status = "✅" if task.is_completed else "⏳"
        due_date = f"\n📅 До: {task.due_date.strftime('%d.%m.%Y')}" if task.due_date else ""
        text += f"{status} {task.title}{due_date}\n"
    
    await message.answer(text, reply_markup=get_task_keyboard(tasks))

@router.message(Command("delete"))
async def cmd_delete(message: Message, state: FSMContext, session: Session):
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one()
    
    result = await session.execute(
        select(Task).where(Task.user_id == user.id)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await message.answer("📋 У вас пока нет задач для удаления!")
        return
    
    await state.set_state(TaskStates.waiting_for_task_to_delete)
    await message.answer(
        "❌ Выберите задачу для удаления:",
        reply_markup=get_task_keyboard(tasks)
    )

@router.callback_query(TaskStates.waiting_for_task_to_delete)
async def process_task_deletion(callback: CallbackQuery, state: FSMContext, session: Session):
    task_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    await session.delete(task)
    await session.commit()
    
    await state.clear()
    await callback.message.answer(
        "✅ Задача успешно удалена!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.message(Command("done"))
async def cmd_done(message: Message, state: FSMContext, session: Session):
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one()
    
    result = await session.execute(
        select(Task).where(
            Task.user_id == user.id,
            Task.is_completed == False
        )
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await message.answer("📋 У вас нет невыполненных задач!")
        return
    
    await state.set_state(TaskStates.waiting_for_task_to_complete)
    await message.answer(
        "✅ Выберите задачу для отметки как выполненной:",
        reply_markup=get_task_keyboard(tasks)
    )

@router.callback_query(TaskStates.waiting_for_task_to_complete)
async def process_task_completion(callback: CallbackQuery, state: FSMContext, session: Session):
    task_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    task.is_completed = True
    await session.commit()
    
    await state.clear()
    await callback.message.answer(
        "✅ Задача отмечена как выполненная!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_"))
async def process_task_callback(callback: CallbackQuery, session: Session):
    task_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    text = f"📝 {task.title}\n"
    if task.description:
        text += f"\n📋 Описание:\n{task.description}\n"
    if task.due_date:
        text += f"\n📅 До: {task.due_date.strftime('%d.%m.%Y')}\n"
    text += f"\nСтатус: {'✅ Выполнено' if task.is_completed else '⏳ В процессе'}"
    
    await callback.message.answer(
        text,
        reply_markup=get_task_actions_keyboard(task)
    )
    await callback.answer()

@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, session: Session):
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one()
    
    result = await session.execute(
        select(Task).where(Task.user_id == user.id)
    )
    total_tasks = len(result.scalars().all())
    
    result = await session.execute(
        select(Task).where(
            Task.user_id == user.id,
            Task.is_completed == True
        )
    )
    completed_tasks = len(result.scalars().all())
    
    pending_tasks = total_tasks - completed_tasks
    
    text = (
        f"📊 Ваша статистика:\n\n"
        f"📝 Всего задач: {total_tasks}\n"
        f"✅ Выполнено: {completed_tasks}\n"
        f"⏳ В процессе: {pending_tasks}\n"
        f"📈 Прогресс: {int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)}%"
    )
    
    await message.answer(text, reply_markup=get_main_keyboard())

@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    text = (
        "ℹ️ Список команд и возможностей:\n\n"
        "📝 Добавить задачу - Создать новую задачу\n"
        "📋 Список задач - Показать все ваши задачи\n"
        "✅ Выполненные - Показать выполненные задачи\n"
        "❌ Удалить задачу - Удалить выбранную задачу\n"
        "📊 Статистика - Показать вашу статистику\n\n"
        "Команды:\n"
        "/start - Начать работу с ботом\n"
        "/add - Добавить новую задачу\n"
        "/list - Показать список задач\n"
        "/done - Отметить задачу как выполненную\n"
        "/delete - Удалить задачу\n"
        "/help - Показать это сообщение"
    )
    
    await message.answer(text, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "back_to_list")
async def process_back_to_list(callback: CallbackQuery, session: Session):
    result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = result.scalar_one()
    
    result = await session.execute(
        select(Task).where(Task.user_id == user.id)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await callback.message.answer("📋 У вас пока нет задач!")
        return
    
    text = "📋 Ваши задачи:\n\n"
    for task in tasks:
        status = "✅" if task.is_completed else "⏳"
        due_date = f"\n📅 До: {task.due_date.strftime('%d.%m.%Y')}" if task.due_date else ""
        text += f"{status} {task.title}{due_date}\n"
    
    await callback.message.answer(text, reply_markup=get_task_keyboard(tasks))
    await callback.answer()

@router.callback_query(F.data.startswith("complete_"))
async def process_complete_task(callback: CallbackQuery, session: Session):
    task_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    task.is_completed = True
    await session.commit()
    
    await callback.message.answer(
        "✅ Задача отмечена как выполненная!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_"))
async def process_delete_task(callback: CallbackQuery, session: Session):
    task_id = int(callback.data.split("_")[1])
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    await session.delete(task)
    await session.commit()
    
    await callback.message.answer(
        "✅ Задача успешно удалена!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.message(F.text == "📝 Добавить задачу")
async def cmd_add_button(message: Message, state: FSMContext):
    await cmd_add(message, state)

@router.message(F.text == "📋 Список задач")
async def cmd_list_button(message: Message, session: Session):
    await cmd_list(message, session)

@router.message(F.text == "✅ Выполненные")
async def cmd_completed(message: Message, session: Session):
    user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
    tasks = session.query(Task).filter(
        Task.user_id == user.id,
        Task.is_completed == True
    ).all()
    
    if not tasks:
        await message.answer("📋 У вас нет выполненных задач!")
        return
    
    text = "✅ Выполненные задачи:\n\n"
    for task in tasks:
        due_date = f"\n📅 До: {task.due_date.strftime('%d.%m.%Y')}" if task.due_date else ""
        text += f"✅ {task.title}{due_date}\n"
    
    await message.answer(text, reply_markup=get_task_keyboard(tasks))

@router.message(F.text == "📁 Категории")
async def cmd_categories(message: Message, session: Session):
    categories = session.query(Category).all()
    await message.answer(
        "📁 Ваши категории:",
        reply_markup=get_categories_keyboard(categories)
    )

@router.callback_query(F.data == "add_category")
async def process_add_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_category_name)
    await callback.message.answer("📝 Введите название новой категории:")
    await callback.answer()

@router.message(TaskStates.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TaskStates.waiting_for_category_color)
    await message.answer("🎨 Введите цвет категории в формате HEX (например, #FF0000):")

@router.message(TaskStates.waiting_for_category_color)
async def process_category_color(message: Message, state: FSMContext, session: Session):
    data = await state.get_data()
    try:
        category = Category(
            name=data["name"],
            color=message.text
        )
        session.add(category)
        session.commit()
        
        await state.clear()
        await message.answer(
            "✅ Категория успешно добавлена!",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        await message.answer(
            "❌ Ошибка при добавлении категории. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: Message):
    await message.answer(
        "⚙️ Настройки:",
        reply_markup=get_settings_keyboard()
    )

@router.callback_query(F.data == "notification_settings")
async def process_notification_settings(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_notification_time)
    await callback.message.answer(
        "🔔 За сколько часов до дедлайна вы хотите получать уведомления?\n"
        "Введите число от 1 до 24:"
    )
    await callback.answer()

@router.message(TaskStates.waiting_for_notification_time)
async def process_notification_time(message: Message, state: FSMContext, session: Session):
    try:
        hours = int(message.text)
        if not 1 <= hours <= 24:
            raise ValueError
        
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        user.notification_time = hours
        session.commit()
        
        await state.clear()
        await message.answer(
            f"✅ Время уведомлений установлено на {hours} часов до дедлайна.",
            reply_markup=get_main_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неверное значение. Введите число от 1 до 24:"
        )

@router.callback_query(F.data.startswith("edit_"))
async def process_edit_task(callback: CallbackQuery, session: Session):
    task_id = int(callback.data.split("_")[1])
    task = session.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    await callback.message.answer(
        "✏️ Что вы хотите изменить?",
        reply_markup=get_edit_task_keyboard(task)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_title_"))
async def process_edit_title(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[2])
    await state.update_data(task_id=task_id)
    await state.set_state(TaskStates.waiting_for_edit_title)
    await callback.message.answer("📝 Введите новое название задачи:")
    await callback.answer()

@router.message(TaskStates.waiting_for_edit_title)
async def process_new_title(message: Message, state: FSMContext, session: Session):
    data = await state.get_data()
    task = session.query(Task).filter(Task.id == data["task_id"]).first()
    
    if not task:
        await message.answer("❌ Задача не найдена!")
        return
    
    task.title = message.text
    session.commit()
    
    await state.clear()
    await message.answer(
        "✅ Название задачи обновлено!",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data.startswith("edit_priority_"))
async def process_edit_priority(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split("_")[2])
    await state.update_data(task_id=task_id)
    await state.set_state(TaskStates.waiting_for_edit_priority)
    await callback.message.answer(
        "🎯 Выберите новый приоритет:",
        reply_markup=get_priority_keyboard()
    )
    await callback.answer()

@router.callback_query(TaskStates.waiting_for_edit_priority)
async def process_new_priority(callback: CallbackQuery, state: FSMContext, session: Session):
    data = await state.get_data()
    task = session.query(Task).filter(Task.id == data["task_id"]).first()
    
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return
    
    priority_map = {
        "priority_high": Priority.HIGH,
        "priority_medium": Priority.MEDIUM,
        "priority_low": Priority.LOW
    }
    
    task.priority = priority_map[callback.data]
    session.commit()
    
    await state.clear()
    await callback.message.answer(
        "✅ Приоритет задачи обновлен!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "export_tasks")
async def process_export_tasks(callback: CallbackQuery, session: Session):
    user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
    tasks = session.query(Task).filter(Task.user_id == user.id).all()
    
    if not tasks:
        await callback.answer("📋 У вас пока нет задач для экспорта!")
        return
    
    import json
    from datetime import datetime
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
            "created_at": task.created_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority.value,
            "category": task.category.name if task.category else None
        })
    
    await callback.message.answer_document(
        document=json.dumps(tasks_data, ensure_ascii=False, indent=2),
        filename=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    await callback.answer()

@router.message(F.document)
async def process_import_tasks(message: Message, session: Session):
    try:
        import json
        from datetime import datetime
        
        file = await message.bot.download(message.document)
        tasks_data = json.loads(file.read())
        
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        for task_data in tasks_data:
            task = Task(
                user_id=user.id,
                title=task_data["title"],
                description=task_data["description"],
                is_completed=task_data["is_completed"],
                created_at=datetime.fromisoformat(task_data["created_at"]),
                due_date=datetime.fromisoformat(task_data["due_date"]) if task_data["due_date"] else None,
                priority=Priority(task_data["priority"])
            )
            session.add(task)
        
        session.commit()
        await message.answer(
            "✅ Задачи успешно импортированы!",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        await message.answer(
            "❌ Ошибка при импорте задач. Проверьте формат файла.",
            reply_markup=get_main_keyboard()
        )

async def check_notifications(bot, engine):
    while True:
        try:
            async_session = sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            async with async_session() as session:
                now = datetime.now()
                users = await session.execute(select(User))
                users = users.scalars().all()
                
                for user in users:
                    tasks = await session.execute(
                        select(Task).where(
                            Task.user_id == user.id,
                            Task.is_completed == False,
                            Task.due_date != None,
                            Task.last_notified == None
                        )
                    )
                    tasks = tasks.scalars().all()
                    
                    for task in tasks:
                        time_diff = task.due_date - now
                        if time_diff.total_seconds() <= user.notification_time * 3600:
                            try:
                                await bot.send_message(
                                    user.telegram_id,
                                    f"🔔 Напоминание!\n"
                                    f"Задача \"{task.title}\" должна быть выполнена до {task.due_date.strftime('%d.%m.%Y %H:%M')}!"
                                )
                                task.last_notified = now
                                await session.commit()
                            except Exception as e:
                                logger.error(f"Ошибка при отправке уведомления: {e}")
        except Exception as e:
            logger.error(f"Ошибка в check_notifications: {e}")
        
        await asyncio.sleep(300)  # Проверяем каждые 5 минут 