from PIL import Image, ImageDraw, ImageFont

def create_mdi_badge(badge_size):
    badge = Image.new('RGBA', (badge_size, badge_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    blue_color = (41, 128, 185, 255)
    corner_radius = max(2, badge_size // 8)
    draw.rounded_rectangle([(0, 0), (badge_size - 1, badge_size - 1)], radius=corner_radius, fill=blue_color)
    font_size = max(int(badge_size * 0.35), 6)
    font = None
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        pass
    text = "MDI"
    estimated_width = font_size * 2.2
    estimated_height = font_size
    x = int((badge_size - estimated_width) / 2)
    y = int((badge_size - estimated_height) / 2)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    return badge

files = [("assets/favicon-16x16.png", 16), ("assets/favicon-32x32.png", 32), ("assets/favicon-48x48.png", 48), ("assets/favicon-64x64.png", 64), ("assets/favicon-128x128.png", 128), ("assets/favicon-256x256.png", 256)]

for path, size in files:
    favicon = Image.open(path).convert('RGBA')
    badge_size = max(int(size * 0.30), 10)
    badge = create_mdi_badge(badge_size)
    padding = max(1, int(size * 0.03))
    x_pos = size - badge_size - padding
    y_pos = size - badge_size - padding
    favicon.paste(badge, (x_pos, y_pos), badge)
    favicon.save(path, 'PNG')
    print(f"Added MDI badge to {path}")

f16 = Image.open("assets/favicon-16x16.png")
f32 = Image.open("assets/favicon-32x32.png")
f48 = Image.open("assets/favicon-48x48.png")
f16.save("assets/favicon.ico", format='ICO', sizes=[(16,16), (32,32), (48,48)])
print("Updated assets/favicon.ico")
print("Complete!")
