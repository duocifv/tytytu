from services.daily_hexagram_service import DailyHexagramService
import json

# Quick run example
if __name__ == "__main__":
   
    svc = DailyHexagramService()

    # Example inputs (you would replace with real daily data)
    thien = "Dữ liệu thiên văn cho ngày 29/09/2025 cho thấy chỉ số Kp chỉ ở mức 2.67 (cùng với các chỉ số phụ Ap≈12, Cp≈8), nghĩa là hoạt động địa từ rất yếu, không có bão mặt trời hay hiện tượng bức xạ mạnh ảnh hưởng đến vệ tinh, viễn thông hoặc hàng không. Ngược lại, tin tức địa phương báo cáo bão số 10 đang gây ra mưa lớn, gió mạnh ở miền Trung Việt Nam, đặc biệt ở khu vực Vũng Áng. Bão này làm tăng áp lực khí quyển, gây nguy cơ sạt lở, ngập lụt và làm suy giảm khả năng truyền sóng vô tuyến, ảnh hưởng tới các chuyến bay nội địa và các trạm viễn thông trên đất liền và trên biển. Tuy nhiên, do chỉ số Kp thấp, các hệ thống vệ tinh và GPS vẫn ổn định, không có gián đoạn đáng kể từ bão địa từ."
    dia = "Các sự kiện địa chất ghi nhận trong ngày bao gồm 5 trận động đất nhỏ (độ lớn 0.9-2.1) tại Texas, California và Alaska, hầu hết ở độ sâu vài km và không gây thiệt hại đáng kể. Các trận này cho thấy khu vực Tây Bắc Thái Bình Dương vẫn hoạt động địa chấn bình thường, nhưng mức độ rủi ro cho dân cư địa phương là thấp. Song song với đó, bão số 10 đã gây sập kho than tại nhà máy nhiệt điện Vũng Áng 2, tạo nguy cơ rò rỉ than và chất thải vào môi trường biển và đất liền, có thể dẫn đến ô nhiễm nước, đất và ảnh hưởng đến hệ sinh thái ven biển."
    nhan = "Sự sập kho than ở Vũng Áng 2 do bão số 10 tạo ra tác động trực tiếp tới cộng đồng địa phương: nguy cơ ô nhiễm không khí và nước do bụi thải và chất thải khoáng sản, gây ra các vấn đề sức khỏe hô hấp, đặc biệt cho những người làm việc trong và quanh khu công nghiệp. Ngoài ra, việc ngừng hoạt động của nhà máy nhiệt điện tạm thời làm giảm cung cấp điện, ảnh hưởng tới doanh nghiệp và sinh hoạt hằng ngày, đồng thời tạo áp lực lên chính quyền địa phương trong việc xử lý khẩn cấp và bồi thường. Các trận động đất nhỏ không gây thương vong hay thiệt hại lớn, nên ảnh hưởng xã hội của chúng là không đáng kể."
    key_event = "Sự kiện nổi bật nhất trong ngày là việc kho than của nhà máy nhiệt điện Vũng Áng 2 sập do bão số 10, gây nguy cơ ô nhiễm môi trường và ảnh hưởng nghiêm trọng tới sức khỏe cộng đồng, kinh tế địa phương và an ninh năng lượng. Sự kiện này liên kết chặt chẽ với các yếu tố Thiên (bão mạnh), Địa (rủi ro môi trường và địa chất) và Nhân (tác động xã hội và y tế)."

    node = svc.create_daily_node(thien, dia, nhan, key_event)
    print(json.dumps(node, ensure_ascii=False, indent=2))
