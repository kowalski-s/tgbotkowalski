"""
Класс для работы с SQLite базой данных
"""
import aiosqlite
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from .models import CREATE_USERS_TABLE, CREATE_MESSAGES_TABLE, CREATE_INDEXES

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Подключение к базе данных"""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self._create_tables()
        logger.info(f"База данных подключена: {self.db_path}")

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.connection:
            await self.connection.close()
            logger.info("База данных отключена")

    async def _create_tables(self):
        """Создание таблиц, если их нет"""
        async with self.connection.cursor() as cursor:
            await cursor.execute(CREATE_USERS_TABLE)
            await cursor.execute(CREATE_MESSAGES_TABLE)

            for index_query in CREATE_INDEXES:
                await cursor.execute(index_query)

            await self.connection.commit()
        logger.info("Таблицы созданы/проверены")

    # === Работа с пользователями ===

    async def add_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> bool:
        """Добавление нового пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        last_active = CURRENT_TIMESTAMP
                    """,
                    (user_id, username, first_name, last_name),
                )
                await self.connection.commit()
            logger.info(f"Пользователь {user_id} добавлен/обновлен")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False

    async def update_user_subscription(self, user_id: int, is_subscribed: bool = True) -> bool:
        """Обновление статуса подписки"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    UPDATE users
                    SET is_subscribed = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (is_subscribed, user_id),
                )
                await self.connection.commit()
            logger.info(f"Подписка пользователя {user_id} обновлена: {is_subscribed}")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления подписки: {e}")
            return False

    async def mark_file_received(self, user_id: int) -> bool:
        """Отметить, что пользователь получил файл"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    UPDATE users
                    SET received_file = 1, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
                await self.connection.commit()
            logger.info(f"Пользователь {user_id} получил файл")
            return True
        except Exception as e:
            logger.error(f"Ошибка отметки получения файла: {e}")
            return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    async def is_user_subscribed(self, user_id: int) -> bool:
        """Проверка статуса подписки в БД"""
        user = await self.get_user(user_id)
        return user.get("is_subscribed", False) if user else False

    # === Работа с сообщениями ===

    async def save_message(
        self, user_id: int, message_text: str, is_from_admin: bool = False
    ) -> bool:
        """Сохранение сообщения"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO messages (user_id, message_text, is_from_admin)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, message_text, is_from_admin),
                )
                await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
            return False

    async def get_user_messages(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних сообщений пользователя"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT * FROM messages
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения сообщений: {e}")
            return []

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT * FROM users
                    ORDER BY created_at DESC
                    """
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []

    async def get_all_user_ids(self) -> List[int]:
        """Получение всех user_id для рассылки"""
        try:
            async with self.connection.cursor() as cursor:
                await cursor.execute("SELECT user_id FROM users")
                rows = await cursor.fetchall()
                return [row["user_id"] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения user_ids: {e}")
            return []

    # === Статистика ===

    async def get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        try:
            async with self.connection.cursor() as cursor:
                # Общее количество пользователей
                await cursor.execute("SELECT COUNT(*) as total FROM users")
                total_row = await cursor.fetchone()
                total_users = total_row["total"] if total_row else 0

                # Количество подписавшихся
                await cursor.execute(
                    "SELECT COUNT(*) as subscribed FROM users WHERE is_subscribed = 1"
                )
                subscribed_row = await cursor.fetchone()
                subscribed_users = subscribed_row["subscribed"] if subscribed_row else 0

                # Количество получивших файл
                await cursor.execute(
                    "SELECT COUNT(*) as received FROM users WHERE received_file = 1"
                )
                received_row = await cursor.fetchone()
                received_file = received_row["received"] if received_row else 0

                # Общее количество сообщений
                await cursor.execute("SELECT COUNT(*) as total_messages FROM messages")
                messages_row = await cursor.fetchone()
                total_messages = messages_row["total_messages"] if messages_row else 0

                return {
                    "total_users": total_users,
                    "subscribed_users": subscribed_users,
                    "received_file": received_file,
                    "total_messages": total_messages,
                }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                "total_users": 0,
                "subscribed_users": 0,
                "received_file": 0,
                "total_messages": 0,
            }
