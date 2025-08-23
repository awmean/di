from typing import Optional, Dict, Any

import requests

from app.core.config import settings
from app.orders.models import Order


class TelegramMessenger:
    BOT_TOKEN = settings.BOT_TOKEN
    CHANNEL_ID = settings.CHANNEL_ID
    """
    A static Python class for sending messages via Telegram Bot API
    All methods are static - no need to instantiate the class
    """

    @staticmethod
    def _get_base_url(bot_token: str) -> str:
        """
        Get the base URL for Telegram Bot API

        Args:
            bot_token (str): Telegram bot token

        Returns:
            str: Base URL for API calls
        """
        return f"https://api.telegram.org/bot{bot_token}"

    @staticmethod
    def send_message(bot_token: str, chat_id: str, text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a text message to a chat/channel

        Args:
            bot_token (str): Your Telegram bot token
            chat_id (str): Chat ID (e.g., "-1002631138340" or "@username")
            text (str): Message text to send
            parse_mode (str, optional): Parse mode ('HTML' or 'Markdown')

        Returns:
            Dict: API response
        """
        url = f"{TelegramMessenger._get_base_url(bot_token)}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def send_photo(bot_token: str, chat_id: str, photo_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a photo to a chat/channel

        Args:
            bot_token (str): Your Telegram bot token
            chat_id (str): Chat ID
            photo_url (str): URL of the photo to send
            caption (str, optional): Photo caption

        Returns:
            Dict: API response
        """
        url = f"{TelegramMessenger._get_base_url(bot_token)}/sendPhoto"

        payload = {
            "chat_id": chat_id,
            "photo": photo_url
        }

        if caption:
            payload["caption"] = caption

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def get_updates(bot_token: str) -> Dict[str, Any]:
        """
        Get updates from Telegram Bot API

        Args:
            bot_token (str): Your Telegram bot token

        Returns:
            Dict: API response with updates
        """
        url = f"{TelegramMessenger._get_base_url(bot_token)}/getUpdates"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def extract_chat_id_from_updates(updates_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract chat ID from getUpdates response

        Args:
            updates_response (Dict): Response from getUpdates API call

        Returns:
            str: Chat ID if found, None otherwise
        """
        if not updates_response.get("ok"):
            return None

        results = updates_response.get("result", [])
        if not results:
            return None

        # Get the latest update
        latest_update = results[-1]

        # Check for different message types
        if "message" in latest_update:
            return str(latest_update["message"]["chat"]["id"])
        elif "channel_post" in latest_update:
            return str(latest_update["channel_post"]["chat"]["id"])
        elif "edited_message" in latest_update:
            return str(latest_update["edited_message"]["chat"]["id"])
        elif "edited_channel_post" in latest_update:
            return str(latest_update["edited_channel_post"]["chat"]["id"])

        return None

    @staticmethod
    def get_chat_id(bot_token: str) -> Optional[str]:
        """
        Get chat ID by calling getUpdates

        Args:
            bot_token (str): Telegram bot token

        Returns:
            str: Chat ID if found, None otherwise
        """
        updates = TelegramMessenger.get_updates(bot_token)
        return TelegramMessenger.extract_chat_id_from_updates(updates)

    @staticmethod
    def send_document(bot_token: str, chat_id: str, document_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a document to a chat/channel

        Args:
            bot_token (str): Your Telegram bot token
            chat_id (str): Chat ID
            document_url (str): URL of the document to send
            caption (str, optional): Document caption

        Returns:
            Dict: API response
        """
        url = f"{TelegramMessenger._get_base_url(bot_token)}/sendDocument"

        payload = {
            "chat_id": chat_id,
            "document": document_url
        }

        if caption:
            payload["caption"] = caption

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def send_video(bot_token: str, chat_id: str, video_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a video to a chat/channel

        Args:
            bot_token (str): Your Telegram bot token
            chat_id (str): Chat ID
            video_url (str): URL of the video to send
            caption (str, optional): Video caption

        Returns:
            Dict: API response
        """
        url = f"{TelegramMessenger._get_base_url(bot_token)}/sendVideo"

        payload = {
            "chat_id": chat_id,
            "video": video_url
        }

        if caption:
            payload["caption"] = caption

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def _format_order_message(order) -> str:
        """
        Format an Order object into a formal Telegram message

        Args:
            order: Order SQLAlchemy model instance

        Returns:
            str: Formatted message string
        """

        # Header
        message = f"<b>Заказ №{order.id}</b>\n\n"

        # Customer info
        message += f"<b>Информация о клиенте:</b>\n"
        message += f"Имя: {order.customer_name}\n"
        message += f"Телефон: {order.customer_phone}\n\n"

        total_cost = 0
        # Order items
        if order.items:
            message += f"<b>Состав заказа:</b>\n"

            for i, item in enumerate(order.items, 1):
                product_name = getattr(item.product, 'name', f'Товар ID:{item.product_id}')
                message += f"{i}. {product_name} — {item.quantity} шт.\n"
                total_cost += item.product.price * item.quantity

        message += f"<b>Общая сумма:</b> {total_cost} ₽\n\n"

        # Comment
        if order.comment:
            message += f"<b>Комментарий к заказу:</b>\n{order.comment}\n\n"

        # Timestamps
        message += f"<b>Дата создания:</b> {order.created_at.strftime('%d.%m.%Y в %H:%M')}\n"
        if order.updated_at != order.created_at:
            message += f"<b>Последнее обновление:</b> {order.updated_at.strftime('%d.%m.%Y в %H:%M')}\n"

        return message

    @staticmethod
    def send_order(order: Order) -> Dict[str, Any]:
        try:
            message = TelegramMessenger._format_order_message(order)
            return TelegramMessenger.send_message(TelegramMessenger.BOT_TOKEN, TelegramMessenger.CHANNEL_ID, message,
                                                  parse_mode="HTML")

        except Exception as e:
            return {"ok": False, "error": f"Failed to format order: {str(e)}"}
