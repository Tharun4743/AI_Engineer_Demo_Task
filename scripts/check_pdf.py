import fitz

doc = fitz.open("architecture.pdf")
print(f"Total pages: {len(doc)}")
for i, page in enumerate(doc):
    blocks = page.get_text("blocks")
    # Exclude footer text at the bottom
    content_blocks = [b for b in blocks if b[1] < 740 and "Page " not in b[4]]
    if content_blocks:
        max_y = max(b[3] for b in content_blocks)
        last_block = content_blocks[-1]
        last_text = last_block[4].strip().replace("\n", " ")[:60]
        empty_space = 750 - max_y
        print(f"Page {i+1}: max content y = {max_y:.1f} pt (out of 750pt usable). Empty space at bottom = {empty_space:.1f} pt ({empty_space/750*100:.1f}%)")
        print(f"   Last text: {last_text}")
