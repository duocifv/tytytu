# ---------------- Example usage (tối giản) ----------------

from nodes.data_analysis_node import data_analysis_node


if __name__ == "__main__":
    # tạo poster
    data = data_analysis_node(state={})  # <-- truyền dictionary rỗng
    print("Saved poster to:", data)
