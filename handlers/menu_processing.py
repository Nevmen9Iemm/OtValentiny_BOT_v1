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
    orm_get_user_details,  # Отримання деталей користувача
)
from kbds.inline import (
    get_products_btns,
    get_user_cart,
    get_user_catalog_btns,
    get_user_main_btns,
)

from utils.paginator import Paginator


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)

    if banner is None:
        print(f"[main_menu] Банер із назвою '{menu_name}' не знайдено!")
        return InputMediaPhoto(
            media="banners/m",  # Заглушка
            caption="Інформація наразі недоступна."
        ), get_user_main_btns(level=level)

    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    kbds = get_user_main_btns(level=level)
    return image, kbds


async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    if banner is None:
        print(f"Банер із назвою '{menu_name}' не знайдено!")
        return None, get_user_catalog_btns(level=level, categories=[])

    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(level=level, categories=categories)
    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Попер."] = "previous"

    if paginator.has_next():
        btns["Слід. ▶"] = "next"

    return btns


async def products(session, level, category, page):
    # Отримання продуктів
    products = await orm_get_products(session, category_id=category)

    # Перевірка, чи список продуктів не порожній
    if not products:
        return InputMediaPhoto(
            media="banners/empty_category.jpg",  # Замініть на зображення для порожньої категорії
            caption="У цій категорії наразі немає продуктів."
        ), None

    paginator = Paginator(products, page=page)

    # Перевірка, чи є продукти на цій сторінці
    if not paginator.get_page():
        return InputMediaPhoto(
            media="banners/no_products.jpg",  # Замініть на зображення для порожньої сторінки
            caption="На цій сторінці немає продуктів."
        ), None

    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=f"<strong>{product.name}</strong>\n{product.description}\nВартість: {round(product.price, 2)}\n\
                <strong>Продукт {paginator.page} з {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds


async def carts(session, level, menu_name, page, user_id, product_id):
    if menu_name == "order":
        # Обробка замовлення
        response = await process_order(session, user_id)
        return InputMediaPhoto(
            media="banners/confirmation",  # Замініть на реальне зображення підтвердження
            caption=response,
        ), None

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


async def process_order(session: AsyncSession, user_id: int):
    """
    Обробляє замовлення: зберігає його у базу даних.
    """
    # Отримання деталей користувача
    user_details = await orm_get_user_details(session, user_id)
    if not user_details:
        return "Будь ласка, заповніть свої дані для доставки."

    # Отримання вмісту кошика
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

    # Збереження замовлення
    await orm_save_order(session, order_data)

    # Очищення кошика після оформлення замовлення
    for cart in user_cart:
        await orm_delete_from_cart(session, user_id, cart.product.id)

    return f"Замовлення оформлено! Загальна сума: {total_price}$"


async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
    product_id: int | None = None,
    user_id: int | None = None,
):
    if level == 0:
        result = await main_menu(session, level, menu_name)
    elif level == 1:
        result = await catalog(session, level, menu_name)
    elif level == 2:
        result = await products(session, level, category, page)
    elif level == 3:
        result = await carts(session, level, menu_name, page, user_id, product_id)
    else:
        result = None, None

    if result is None:
        print("Меню не знайдено!")
        return None, None  # Повідомте користувача або повертайте заглушку

    return result