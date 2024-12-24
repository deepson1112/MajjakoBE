from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
import textwrap

def custom_wrap(text, width):
    # Wrap text to fit within the specified width
    return textwrap.fill(text, width)

def generate_pdf_labels(order_number, vendor, food_items):
    label_width = 4 * inch  # 4 inches wide
    label_height = 2 * inch  # 2 inches high
    columns = 2  # 2 columns
    rows = 5  # 5 rows
    margin = 0.25 * inch  # Margin around the page
    padding = 0.1 * inch  # Padding inside each label
    text_width = 38  # Approximate character count that fits in the label width
    font_size = 14  # Increased font size
    line_spacing = 16  # Line spacing in points

    filename = f'order_{order_number}_vendor_{vendor}.pdf'
    c = canvas.Canvas(filename, pagesize=letter)

    x = margin
    y = letter[1] - margin - label_height

    for food_name, addons, receiver, vendor_name in food_items:
        addons_text = ', '.join(addons)

        # Wrap each text element
        vendor_text = custom_wrap(f'Restaurant: {vendor_name}', text_width)
        item_text = custom_wrap(f'Item: {food_name}', text_width)
        addons_text = custom_wrap(f'Add-ons: {addons_text}', text_width)
        receiver_text = custom_wrap(f'Receiver: {receiver}', text_width)

        # Draw a rectangle for the label
        c.rect(x, y, label_width, label_height)

        # Draw the text inside the rectangle
        text_object = c.beginText(
            x + padding, y + label_height - padding - 0.3 * inch)
        text_object.setFont("Helvetica", font_size)
        text_object.setLeading(line_spacing)

        # Add vendor, item, and addons text
        text_object.textLines(vendor_text)
        text_object.textLines(item_text)
        text_object.textLines(addons_text)

        # Add receiver text in bold
        text_object.setFont("Helvetica-Bold", font_size)
        text_object.textLine(receiver_text)

        c.drawText(text_object)

        # Update x and y for the next label
        x += label_width
        if x >= letter[0] - margin:
            x = margin
            y -= label_height

            if y < margin:  # Start a new page if we run out of space
                c.showPage()
                y = letter[1] - margin - label_height

    c.save()
    return filename