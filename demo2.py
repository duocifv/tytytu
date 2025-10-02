# ---------------- Example usage (tối giản) ----------------

from nodes.content_and_facebook_node import content_and_facebook_node
from nodes.data_analysis_node import data_analysis_node


if __name__ == "__main__":
    # tạo poster
    data = content_and_facebook_node(state={})  # <-- truyền dictionary rỗng
    print("Saved poster to:", data)
