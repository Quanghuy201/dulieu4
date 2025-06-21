import threading
import time
import random
from collections import defaultdict
from zlapi import ZaloAPI, ThreadType, Message
from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.running = False

    def fetchGroupInfo(self):
        try:
            all_groups = self.fetchAllGroups()
            group_list = []
            for group_id, _ in all_groups.gridVerMap.items():
                group_info = super().fetchGroupInfo(group_id)
                group_name = group_info.gridInfoMap[group_id]["name"]
                group_list.append({'id': group_id, 'name': group_name})
            return group_list
        except Exception as e:
            print(f"Lỗi khi lấy danh sách nhóm: {e}")
            return []

    def display_group_menu_grouped(self, groups):
        if not groups:
            print("Không tìm thấy nhóm nào.")
            return None
        grouped = defaultdict(list)
        for group in groups:
            first_letter = group['name'][0].lower()
            grouped[first_letter].append(group)
        flat_list = []
        count = 1
        for letter in sorted(grouped.keys()):
            print(f"\n=== Nhóm bắt đầu bằng chữ '{letter.upper()}' ===")
            for group in grouped[letter]:
                print(f"{count}. {group['name']} (ID: {group['id']})")
                flat_list.append(group)
                count += 1
        return flat_list

    def select_group(self):
        groups = self.fetchGroupInfo()
        if not groups:
            return None
        flat_group_list = self.display_group_menu_grouped(groups)
        if not flat_group_list:
            return None
        while True:
            try:
                choice = int(input("\nNhập số thứ tự của nhóm: ").strip())
                if 1 <= choice <= len(flat_group_list):
                    return flat_group_list[choice - 1]['id']
                print(f"Vui lòng nhập từ 1 đến {len(flat_group_list)}.")
            except ValueError:
                print("Vui lòng nhập số hợp lệ.")

    def send_file_spam_random(self, thread_id, filename, delay, user):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                responses = [line.strip() for line in f if line.strip()]
            if not responses:
                print("File rỗng hoặc không có dòng hợp lệ.")
                return
            remaining_responses = responses.copy()
            self.running = True

            def spam_loop():
                nonlocal remaining_responses
                while self.running:
                    if not remaining_responses:
                        print("✅ Đã gửi hết tất cả nội dung trong file. Lặp lại...")
                        remaining_responses = responses.copy()
                    response = random.choice(remaining_responses)
                    remaining_responses.remove(response)
                    message_to_send = response.replace("{user}", user)
                    self.send(
                        Message(text=message_to_send),
                        thread_id=thread_id,
                        thread_type=ThreadType.GROUP
                    )
                    print(f"Đã gửi: {message_to_send}")
                    time.sleep(delay)

            spam_thread = threading.Thread(target=spam_loop)
            spam_thread.daemon = True
            spam_thread.start()

            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_sending()
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file: {filename}")
        except Exception as e:
            print(f"❌ Lỗi khi gửi nội dung: {e}")

    def stop_sending(self):
        self.running = False
        print("⛔ Đã dừng gửi tin nhắn.")

    def send_plain_message(self, thread_id, message_text):
        try:
            self.send(
                Message(text=message_text),
                thread_id=thread_id,
                thread_type=ThreadType.GROUP
            )
            print(f"Đã gửi: {message_text}")
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn: {e}")

def run_tool():
    print("TOOL GỬI FILE KHÔNG LẶP LẠI (KHÔNG TAG, KHÔNG MÀU)")
    print("[1] Gửi nội dung từ file")
    print("[0] Thoát")
    choice = input("Nhập lựa chọn: ").strip()
    if choice != '1':
        print("Đã thoát tool.")
        return
    client = Bot(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
    thread_id = client.select_group()
    if not thread_id:
        print("Không có nhóm được chọn.")
        return
    filename = input("Nhập tên file chứa nội dung: ").strip()
    try:
        delay = float(input("Nhập delay giữa các lần gửi (giây): ").strip())
    except ValueError:
        print("Giá trị không hợp lệ, dùng mặc định 10s.")
        delay = 10
    user = input("Nhập giá trị thay thế cho {user}: ").strip()
    client.send_file_spam_random(thread_id, filename, delay, user)

if __name__ == "__main__":
    run_tool()
