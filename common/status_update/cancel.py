from rest_framework.exceptions import ValidationError

from apps.catalog.models.product import ProductCount


def restore_order_items_to_stock(order):
    order_items = order.items.select_related("product").all()

    product_ids = [item.product_id for item in order_items]
    product_counts = {
        pc.product_id: pc
        for pc in ProductCount.objects.select_for_update().filter(product_id__in=product_ids)
    }

    product_counts_to_update = []

    for item in order_items:
        product_count = product_counts.get(item.product_id)
        if not product_count:
            raise ValidationError({
                "stock": f"'{item.product_name}' uchun stock ma'lumoti topilmadi."
            })

        product_count.stock += item.quantity
        product_counts_to_update.append(product_count)

    if product_counts_to_update:
        ProductCount.objects.bulk_update(product_counts_to_update, ["stock"])