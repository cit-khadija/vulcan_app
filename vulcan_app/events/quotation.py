import frappe
import json

#######################################################################################################
#Item Details

@frappe.whitelist()
def get_items(quotation):
    #Returns items and the item details documents
    if quotation:
        qo = frappe.get_doc("Quotation", quotation)

        items = []
        item_codes = [i.item_code for i in qo.items]
        product_bundle_parents = [
			pb.new_item_code
			for pb in frappe.get_all(
				"Product Bundle", {"new_item_code": ["in", item_codes]}, ["new_item_code"]
			)
		]

        for i in qo.items:
            if i.item_code not in product_bundle_parents and i.door_no:
                items.append(
                    dict(
                        name=i.name,
                        item_code=i.item_code,
                        description = i.description,
                        item_details = i.item_details,
                        quotation_item = i.name,
                        quotation = i.parent,
                        door_no = i.door_no
                    )
                )

        return items


@frappe.whitelist()
def create_item_details_pages(items):
    items = json.loads(items)
    docs = []

    for i in items:
        if not i.get("item_details") and i.get("door_no"):
            doc = frappe.get_doc(
                {
                    "doctype":"Item Details",
                    "item_code": i["item_code"],
                    "door_no": i["door_no"],
                    "quotation": i["quotation"]
                }
            ).insert()
            docs.append(
                dict(
                    {'item_details': doc.name}
                )
            )
    return docs