from telegram import Bot

from app.core.config import settings
from app.orders.models import Order


class TelegramMessenger:
    BOT_TOKEN = settings.BOT_TOKEN
    CHANNEL_ID = settings.CHANNEL_ID

    @staticmethod
    def _format_order_message(order: Order) -> str:
        message = f"<b>Заказ №{order.id}</b>\n\n"
        message += f"<b>Информация о клиенте:</b>\n"
        message += f"Имя: {order.customer_name}\n"
        message += f"Телефон: {order.customer_phone}\n\n"

        total_cost = 0
        if order.items:
            message += f"<b>Состав заказа:</b>\n"
            for i, item in enumerate(order.items, 1):
                product_name = getattr(item.product, 'name', f'Товар ID:{item.product_id}')
                message += f"{i}. {product_name} — {item.quantity} шт.\n"
                total_cost += item.product.price * item.quantity
        message += f"<b>Общая сумма:</b> {total_cost} ₽\n\n"

        if order.comment:
            message += f"<b>Комментарий к заказу:</b>\n{order.comment}\n\n"

        message += f"<b>Дата создания:</b> {order.created_at.strftime('%d.%m.%Y в %H:%M')}\n"
        return message

    @staticmethod
    async def send_message(text: str, parse_mode: str = "HTML"):
        bot = Bot(token=TelegramMessenger.BOT_TOKEN)
        return await bot.send_message(
            chat_id=TelegramMessenger.CHANNEL_ID,
            text=text,
            parse_mode=parse_mode
        )

    @staticmethod
    async def send_photo(photo_url: str, caption: str = None):
        bot = Bot(token=TelegramMessenger.BOT_TOKEN)
        return await bot.send_photo(
            chat_id=TelegramMessenger.CHANNEL_ID,
            photo=photo_url,
            caption=caption
        )

    @staticmethod
    async def send_document(document_url: str, caption: str = None):
        bot = Bot(token=TelegramMessenger.BOT_TOKEN)
        return await bot.send_document(
            chat_id=TelegramMessenger.CHANNEL_ID,
            document=document_url,
            caption=caption
        )

    @staticmethod
    async def send_order(order: Order):
        try:
            message = TelegramMessenger._format_order_message(order)
            return await TelegramMessenger.send_message(message)
        except Exception as e:
            return {"ok": False, "error": f"Failed to send order: {str(e)}"}
