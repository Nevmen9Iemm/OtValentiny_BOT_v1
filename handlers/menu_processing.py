from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_add_to_cart,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_get_user_carts,
    orm_reduce_product_in_cart,
    orm_save_order,  # Нова функція для збереження замовлення
    orm_get_user_details,  # Функція для отримання інформації про користувача
)
from kbds.inline import (
    get_products_btns,
    get_user_cart,
    get_user_catalog_btns,
    get_user_main_btns,
)

from utils.paginator import Paginator


async def process_order(session: AsyncSession, user_id: int):
    """
    Обробка кнопки "Замовити".
    """
    # Отримати інформацію про користувача
    user_details = await orm_get_user_details(session, user_id)
    if not user_details:
        return "Будь ласка, заповніть ваші дані для доставки."

    # Отримати кошик користувача
    user_cart = await orm_get_user_carts(session, user_id)
    if not user_cart:
        return "Ваш кошик порожній."

    # Формування даних замовлення
    total_price = round(sum(cart.quantity * cart.product.price for cart in user_cart), 2)
    order_items = [
        {
            "product_id": cart.product.id,
            "name": cart.product.name,
            "quantity": cart.quantity,
            "price_per_unit": cart.product.price,
            "total_price": round(cart.quantity * cart.product.price, 2),
        }
        for cart in user_cart
    ]

    order_data = {
        "user_id": user_id,
        "user_phone": user_details.phone,
        "delivery_address": user_details.address,
        "comment": user_details.comment,
        "total_price": total_price,
        "items": order_items,
    }

    # Зберегти замовлення в базу даних
    await orm_save_order(session, order_data)

    # Очистити кошик користувача
    for cart in user_cart:
        await orm_delete_from_cart(session, user_id, cart.product.id)

    return f"Замовлення оформлено! Загальна сума: {total_price}$"


async def carts(session, level, menu_name, page, user_id, product_id):
    if menu_name == "order":
        # Обробка кнопки "Замовити"
        response = await process_order(session, user_id)
        return InputMediaPhoto(
            media="banners/confirmation",  # Замініть на зображення підтвердження
            caption=response,
        ), None

    # Решта функціоналу залишиться без змін
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        await orm_add_to_cart(session, user_id, product_id)

    carts = await orm_get_user_carts(session, user_id)

    if not carts:
        banner = await orm_get_banner(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        kbds = get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
            product_id=None,
        )

    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(
            sum(cart.quantity * cart.product.price for cart in carts), 2
        )
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n{cart.product.price}$ x {cart.quantity} = {cart_price}$\
                    \nПродукт {paginator.page} з {paginator.pages} в кошику.\nЗагальна вартість товарів у кошику {total_price}",
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds