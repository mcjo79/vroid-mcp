"""Dessine la bande rouge, le nœud de poitrine et les deux nœuds de jupe sur la texture de la robe."""
from PIL import Image, ImageDraw

SRC = r"D:\divers\vroid\out\dress021.png"
DST = r"D:\divers\vroid\out\dress021_red.png"

RED = (178, 30, 44, 255)
DARK = (118, 14, 26, 255)
LIGHT = (222, 72, 86, 255)


def bow(d, cx, cy, s=1.0):
    """Nœud plat : deux boucles, un centre, deux pans."""
    def p(dx, dy):
        return (cx + dx * s, cy + dy * s)
    # boucles
    d.polygon([p(0, 0), p(-95, -55), p(-120, -10), p(-112, 40), p(-70, 45), p(-8, 12)], fill=RED, outline=DARK)
    d.polygon([p(0, 0), p(95, -55), p(120, -10), p(112, 40), p(70, 45), p(8, 12)], fill=RED, outline=DARK)
    # reflets
    d.polygon([p(-18, -22), p(-88, -45), p(-96, -18), p(-40, 4)], fill=LIGHT)
    d.polygon([p(18, -22), p(88, -45), p(96, -18), p(40, 4)], fill=LIGHT)
    # pans
    d.polygon([p(-16, 8), p(-62, 95), p(-30, 100), p(-2, 30)], fill=RED, outline=DARK)
    d.polygon([p(16, 8), p(62, 95), p(30, 100), p(2, 30)], fill=RED, outline=DARK)
    # centre
    d.rounded_rectangle([cx - 20 * s, cy - 20 * s, cx + 20 * s, cy + 20 * s], radius=14 * s, fill=DARK)


def main():
    im = Image.open(SRC).convert("RGBA")
    d = ImageDraw.Draw(im)
    # nœud de poitrine
    bow(d, 1024, 700, 0.9)
    # nœuds de jupe (gauche / droite)
    bow(d, 700, 1690, 1.0)
    bow(d, 1350, 1690, 1.0)
    im.save(DST)
    print("ok", DST)


if __name__ == "__main__":
    main()
