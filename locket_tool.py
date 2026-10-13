import os
import sys
import json
import base64
import plistlib
import shutil
import zipfile
import time
import datetime
import re

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

MEMBER_SINCE_UTC = "2006-06-20T17:00:00Z"
MEMBER_SINCE_PLAIN = "2006-06-20T00:00:00Z"
GOLD_EXPIRES = "2099-12-31T00:00:00Z"

def log(msg):
    time_str = time.strftime('%H:%M:%S')
    try:
        print(f"[{time_str}] {msg}")
    except Exception:
        try:
            clean_msg = msg.encode('ascii', 'ignore').decode('ascii')
            print(f"[{time_str}] {clean_msg}")
        except Exception:
            pass

def load_remote_config_entries():
    """Tự động tìm và đọc toàn bộ cấu hình từ Locket_Unlocked.js nếu có, hoặc dùng fallback."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, 'js', 'Locket_Unlocked.js'),
        os.path.join(script_dir, 'Locket_Unlocked.js'),
        os.path.join(os.getcwd(), 'js', 'Locket_Unlocked.js'),
        os.path.join(os.getcwd(), 'Locket_Unlocked.js'),
    ]

    for js_path in possible_paths:
        if os.path.exists(js_path):
            try:
                with open(js_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                entries = {}
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('obj.entries.'):
                        parts = line.split('=', 1)
                        key = parts[0].replace('obj.entries.', '').strip()
                        rest = parts[1].strip()

                        stmt = rest
                        while not stmt.endswith(';') and i + 1 < len(lines):
                            i += 1
                            stmt += '\n' + lines[i]
                        stmt = stmt.rstrip(';').strip()

                        if stmt.startswith('JSON.stringify(') and stmt.endswith(')'):
                            inner = stmt[len('JSON.stringify('):-1].strip()
                            try:
                                py_inner = re.sub(r'\btrue\b', 'True', inner)
                                py_inner = re.sub(r'\bfalse\b', 'False', py_inner)
                                py_inner = re.sub(r'\bnull\b', 'None', py_inner)
                                py_inner = re.sub(r'([{\[,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', py_inner)
                                val_obj = eval(py_inner, {"streak": {}})
                                entries[key] = json.dumps(val_obj, ensure_ascii=False)
                            except Exception:
                                entries[key] = inner
                        elif (stmt.startswith('"') and stmt.endswith('"')) or (stmt.startswith("'") and stmt.endswith("'")):
                            entries[key] = stmt[1:-1]
                        else:
                            entries[key] = stmt
                    i += 1

                if entries:
                    log(f"⚡ Đã nạp thành công {len(entries)} cấu hình Remote Config từ: {os.path.basename(js_path)}")
                    return entries
            except Exception as e:
                pass

    log("⚡ Dùng bộ cấu hình Remote Config tích hợp sẵn...")
    return {
        "feature_gates": json.dumps({
            "app_icon_picker": "enabled",
            "camera_roll": "enabled",
            "camera_theme": "enabled",
            "locket_views": "enabled",
            "long_captions": "enabled",
            "longer_video": "enabled",
            "unlimited_friends": "enabled",
            "priority_support": "enabled",
            "profile_badge": "enabled",
            "remove_ads": "enabled",
            "video": "enabled",
            "custom_widget_frames": "enabled",
            "streak_recovery": "enabled",
        }),
        "history_ads_mode": "off",
        "moment_views_enabled": "true",
        "moment_views_v2": "true",
        "record_moment_views": "true",
        "notify_moment_views": "true",
        "max_friends_count": "9999",
        "friend_limit_mode": "0",
        "captions_enabled": "true",
        "music_caption_enabled": "true",
        "camera_roll_preview_enabled": "true",
        "profile_badge_visible": "true",
        "activity_bar_enabled": "true",
        "journal_activity_bar_enabled": "true",
    }

def get_golden_payload(uid, now=None):
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    req_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    req_date_ms = int(now.timestamp() * 1000)

    return {
        "request_date": req_date,
        "request_date_ms": req_date_ms,
        "subscriber": {
            "entitlements": {
                "Gold": {
                    "expires_date": GOLD_EXPIRES,
                    "grace_period_expires_date": None,
                    "product_identifier": "locket_3600_1y",
                    "purchase_date": MEMBER_SINCE_PLAIN
                },
                "effect_pack_10": {
                    "expires_date": GOLD_EXPIRES,
                    "grace_period_expires_date": None,
                    "product_identifier": "com.locket.Locket.FilterPack_10Photos_400",
                    "purchase_date": MEMBER_SINCE_PLAIN
                },
                "effect_pack_20": {
                    "expires_date": GOLD_EXPIRES,
                    "grace_period_expires_date": None,
                    "product_identifier": "com.locket.Locket.FilterPack_20Photos_500",
                    "purchase_date": MEMBER_SINCE_PLAIN
                },
                "custom_widget_frames": {
                    "expires_date": GOLD_EXPIRES,
                    "grace_period_expires_date": None,
                    "product_identifier": "locket_3600_1y",
                    "purchase_date": MEMBER_SINCE_PLAIN
                }
            },
            "first_seen": MEMBER_SINCE_PLAIN,
            "last_seen": req_date,
            "management_url": "https://apps.apple.com/account/subscriptions",
            "non_subscriptions": {},
            "original_app_user_id": uid,
            "original_application_version": "1.0",
            "original_purchase_date": MEMBER_SINCE_UTC,
            "other_purchases": {},
            "subscriptions": {
                "locket_3600_1y": {
                    "auto_resume_date": None, "billing_issues_detected_at": None,
                    "display_name": "Locket Gold (Yearly)",
                    "expires_date": GOLD_EXPIRES,
                    "grace_period_expires_date": None, "is_sandbox": True,
                    "management_url": "https://apps.apple.com/account/subscriptions",
                    "original_purchase_date": MEMBER_SINCE_UTC,
                    "ownership_type": "PURCHASED", "period_type": "normal",
                    "price": {"amount": 36.0, "currency": "USD"},
                    "purchase_date": MEMBER_SINCE_UTC,
                    "refunded_at": None, "store": "app_store",
                    "store_transaction_id": "530002538222649",
                    "unsubscribe_detected_at": None
                }
            }
        }
    }

def process_imazingapp(input_zip_path, output_zip_path):
    log("🔍 Đang rà quét cấu trúc file backup...")
    with zipfile.ZipFile(input_zip_path, 'r', allowZip64=True) as zin:
        etag_path = None
        group_path = None
        main_plist_path = None
        prefix = ""
        
        for info in zin.infolist():
            name = info.filename
            if 'Container/Library/' in name or 'Container/AppGroups/' in name:
                prefix = name.split('Container/')[0]
            if name.endswith('com.locket.Locket.revenuecat.etags.plist'): etag_path = name
            elif name.endswith('group.com.locket.Locket-Shared.plist'): group_path = name
            elif name.endswith('com.locket.Locket.plist'): main_plist_path = name
            
        if not etag_path: etag_path = f"{prefix}Container/Library/Preferences/com.locket.Locket.revenuecat.etags.plist"
        if not group_path: group_path = f"{prefix}Container/AppGroups/group.com.locket.Locket-Shared/Library/Preferences/group.com.locket.Locket-Shared.plist"
        if not main_plist_path: main_plist_path = f"{prefix}Container/Library/Preferences/com.locket.Locket.plist"
                
        etag_data = zin.read(etag_path) if etag_path in zin.namelist() else None
        group_data = zin.read(group_path) if group_path in zin.namelist() else None
        main_data = zin.read(main_plist_path) if main_plist_path in zin.namelist() else None
        
        etag_dict = plistlib.loads(etag_data) if etag_data else {}
        group_dict = plistlib.loads(group_data) if group_data else {}
        main_dict = plistlib.loads(main_data) if main_data else {}
        
        uid = None
        if etag_dict:
            for k in etag_dict.keys():
                if 'api.revenuecat.com/v1/subscribers/' in k:
                    tail = k.split('/')[-1]
                    if len(tail) > 10 and tail not in ['offerings', 'identify', 'attributes']:
                        uid = tail; break
        if not uid and group_dict:
            v = group_dict.get('com.revenuecat.userdefaults.appUserID.new')
            if isinstance(v, str) and len(v) > 10: uid = v
            if not uid:
                for k in group_dict.keys():
                    if k.startswith('com.revenuecat.userdefaults.purchaserInfo.'):
                        t = k.split('.')[-1]
                        if len(t) > 10: uid = t; break
                    elif k.endswith('/cached_theme'):
                        t = k.split('/')[0]
                        if len(t) > 10: uid = t; break
        if not uid and main_dict:
            for k in main_dict.keys():
                if '/cached_user' in k or '/history_window' in k:
                    t = k.split('/')[0]
                    if len(t) > 10: uid = t; break
                elif k.startswith('navigation-profile-picture-'):
                    t = k.replace('navigation-profile-picture-', '')
                    if len(t) > 10: uid = t; break

        if not uid:
            print("\n❌ LỖI: KHÔNG TÌM THẤY UID trong bản backup này. Có thể bạn chưa từng đăng nhập Locket hoặc file backup bị hỏng.")
            sys.exit(1)
            
        log(f"🎯 Tóm được UID: {uid}")
        now = datetime.datetime.now(datetime.timezone.utc)
        req_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        req_date_ms = int(now.timestamp() * 1000)

        p = get_golden_payload(uid, now)
        b64_data = base64.b64encode(json.dumps(p).encode('utf-8'))
        
        for k in list(etag_dict.keys()):
            if 'api.revenuecat.com/v1/subscribers/' in k:
                tail = k.split('/')[-1]
                if len(tail) > 10 and tail not in ['offerings', 'identify', 'attributes']:
                    try: val_node = json.loads(etag_dict[k].decode('utf-8'))
                    except: val_node = {}
                    p_user = get_golden_payload(tail, now)
                    val_node["data"] = base64.b64encode(json.dumps(p_user).encode('utf-8')).decode('utf-8')
                    val_node["verification_result"] = 1
                    val_node["status_code"] = val_node.get("status_code", 200)
                    val_node["e_tag"] = val_node.get("e_tag", "a1b2c3d4e5f6g7h8")
                    val_node["validation_time"] = req_date
                    etag_dict[k] = json.dumps(val_node).encode('utf-8')

        sub_key = f"https://api.revenuecat.com/v1/subscribers/{uid}"
        if sub_key not in etag_dict:
            val_node = {
                "validation_time": req_date,
                "e_tag": "a1b2c3d4e5f6g7h8",
                "status_code": 200,
                "data": b64_data.decode('utf-8'),
                "verification_result": 1
            }
            etag_dict[sub_key] = json.dumps(val_node).encode('utf-8')

        payload = {
            "entitlement_verification": 1,
            "schema_version": "3",
            "request_date": req_date,
            "request_date_ms": req_date_ms,
            "subscriber": get_golden_payload(uid, now)["subscriber"]
        }
        group_dict[f'com.revenuecat.userdefaults.purchaserInfo.{uid}'] = json.dumps(payload).encode('utf-8')
        group_dict[f'com.revenuecat.userdefaults.purchaserInfoLastUpdated.{uid}'] = datetime.datetime.utcnow()
        group_dict['com.revenuecat.userdefaults.appUserID.new'] = uid
        pem = {
            "entitlements_by_product": {
                "locket_099_1m": ["Gold", "custom_widget_frames"],
                "locket_199_1m": ["Gold", "custom_widget_frames"],
                "locket_199_6m": ["Gold", "custom_widget_frames"], 
                "locket_399_1m_only": ["Gold", "custom_widget_frames"],
                "locket_499_1m_only": ["Gold", "custom_widget_frames"],
                "locket_999_1y": ["Gold", "custom_widget_frames"],
                "locket_1599_1y": ["Gold", "custom_widget_frames"],
                "locket_1600_1y": ["Gold", "custom_widget_frames"],
                "locket_3600_1y": ["Gold", "custom_widget_frames"],
                "com.locket.Locket.FilterPack_10Photos": ["Gold", "effect_pack_10"],
                "com.locket.Locket.FilterPack_20Photos": ["Gold", "effect_pack_20"],
            }
        }
        group_dict['com.revenuecat.userdefaults.productEntitlementMapping'] = json.dumps(pem).encode('utf-8')
        group_dict['com.revenuecat.userdefaults.productEntitlementMappingLastUpdated'] = datetime.datetime.utcnow()

        # ============================================================
        # MỞ KHÓA TOÀN BỘ TÍNH NĂNG NHƯ LOCKET_UNLOCKED.JS
        # ============================================================
        log("🚀 Đang nạp Full tính năng & Remote Config từ Locket_Unlocked...")
        rc_entries = load_remote_config_entries()
        for k, v in rc_entries.items():
            group_dict[k] = v
            if main_dict:
                main_dict[k] = v

        # Mở khóa Khung ảnh Widget VIP
        group_dict[f'custom_widget_frames_unlocked/{uid}'] = True
        group_dict[f'custom_widget_frames_enabled/{uid}']  = True
        group_dict[f'custom_widget_frames_selected/{uid}'] = 'gold'
        group_dict['custom_widget_frames_unlocked'] = True
        group_dict['custom_widget_frames_enabled']  = True

        # Mở khóa Themes Camera VIP
        themes_list = ['gold', 'tinted', 'sunset', 'midnight', 'ocean', 'lavender', 'emerald', 'classic']
        group_dict[f'{uid}/cached_theme'] = 'gold'
        group_dict[f'{uid}/unlocked_themes'] = themes_list
        group_dict['unlocked_themes'] = themes_list
        group_dict['theme_picker_enabled'] = True
        group_dict['theme_picker_unlocked'] = True

        # Mở khóa Biểu tượng ứng dụng VIP (App Icons)
        icons_list = ['gold', 'classic', 'retro', 'black', 'neon', 'lunar_new_year']
        group_dict[f'{uid}/unlocked_app_icons'] = icons_list
        group_dict['unlocked_app_icons'] = icons_list
        group_dict['app_icon_picker_enabled'] = True

        # Kích hoạt toàn bộ cờ tính năng cục bộ
        group_dict['camera_roll_enabled'] = True
        group_dict['locket_views_enabled'] = True
        group_dict['longer_video_enabled'] = True
        group_dict['long_captions_enabled'] = True
        group_dict['video_enabled'] = True
        group_dict['remove_ads_enabled'] = True
        group_dict['profile_badge_enabled'] = True
        group_dict['profile_badge_visible'] = True
        group_dict['streak_recovery_enabled'] = True
        group_dict['unlimited_friends_enabled'] = True
        group_dict['max_friends_count'] = 9999
        group_dict['has_received_remote_config'] = True
        group_dict['setup_complete'] = True
        group_dict['onboarding_completed'] = True
        group_dict['has_seen_gold_onboarding'] = True
        group_dict['has_seen_badge_intro'] = True

        if main_dict:
            main_dict['microphone_enabled'] = True
            main_dict['has_received_remote_config'] = True
            main_dict['camera_roll_preview_enabled'] = True
            main_dict['camera_roll_enabled'] = True
            # Cache thời gian Remote Config tương lai để tránh Firebase ghi đè ngay lập tức
            main_dict['com.google.remoteconfig.last_fetch_time'] = datetime.datetime.utcnow() + datetime.timedelta(days=3650)
            main_dict['com.google.remoteconfig.last_fetch_status_key'] = 1
            main_dict['com.google.remoteconfig.cache_expiration_key'] = 864000000.0

        new_etag_data = plistlib.dumps(etag_dict, fmt=plistlib.FMT_BINARY)
        new_group_data = plistlib.dumps(group_dict, fmt=plistlib.FMT_BINARY)
        new_main_data = plistlib.dumps(main_dict, fmt=plistlib.FMT_BINARY) if main_dict else None

        log("📦 Đang đóng gói dữ liệu và tạo file .imazingapp mới...")

        seen = set()
        with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zout:
            for item in zin.infolist():
                if item.filename in seen:
                    continue
                seen.add(item.filename)
                
                if item.filename.endswith('/'):
                    zout.writestr(item, b'')
                    continue
                
                if item.filename == etag_path: 
                    zout.writestr(item, new_etag_data)
                elif item.filename == group_path: 
                    zout.writestr(item, new_group_data)
                elif item.filename == main_plist_path and new_main_data: 
                    zout.writestr(item, new_main_data)
                else:
                    with zin.open(item.filename) as f_in:
                        with zout.open(item, 'w') as f_out:
                            shutil.copyfileobj(f_in, f_out, length=5*1024*1024)
            
            now_tuple = time.localtime()
            if etag_path not in seen and new_etag_data:
                zi = zipfile.ZipInfo(filename=etag_path, date_time=now_tuple[:6])
                zi.create_system = 3
                zi.external_attr = 0o100644 << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(zi, new_etag_data)
                
            if group_path not in seen and new_group_data:
                zi = zipfile.ZipInfo(filename=group_path, date_time=now_tuple[:6])
                zi.create_system = 3
                zi.external_attr = 0o100644 << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(zi, new_group_data)
                
            if main_plist_path not in seen and new_main_data:
                zi = zipfile.ZipInfo(filename=main_plist_path, date_time=now_tuple[:6])
                zi.create_system = 3
                zi.external_attr = 0o100644 << 16
                zi.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(zi, new_main_data)

    log(f"✅ Hoàn tất! File đã lưu tại: {output_zip_path}")
    print("\n⭐ Locket Gold & Khung ảnh VIP đã được mở khóa!")
    print("👉 Hãy mở iMazing và khôi phục (Restore) file backup này vào điện thoại.")

if __name__ == "__main__":
    print("="*50)
    print("       TOOL KÍCH HOẠT LOCKET GOLD")
    print("="*50)
    
    input_file = ""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Thử mở hộp thoại chọn file (chạy trên Windows/Mac/Linux có GUI)
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw() # Ẩn cửa sổ chính
            root.attributes('-topmost', True)
            print("\n👉 Đang mở hộp thoại chọn file... (Vui lòng chọn file .imazingapp)")
            input_file = filedialog.askopenfilename(
                title="Chọn file backup Locket (.imazingapp)",
                filetypes=[("iMazing App Backup", "*.imazingapp"), ("All files", "*.*")]
            )
        except Exception:
            pass
            
        # Nếu hộp thoại bị hủy hoặc không dùng được tkinter, hỏi qua console
        if not input_file:
            print("\nKéo thả file .imazingapp vào đây, hoặc dán đường dẫn file:")
            input_file = input(">>> ").strip()
            # Bỏ dấu nháy kép nếu kéo thả trên Windows
            if input_file.startswith('"') and input_file.endswith('"'):
                input_file = input_file[1:-1]
            if input_file.startswith("'") and input_file.endswith("'"):
                input_file = input_file[1:-1]

    if not input_file:
        print("❌ Bạn chưa chọn file nào. Thoát...")
        sys.exit(0)

    if not os.path.exists(input_file):
        print(f"❌ LỖI: Không tìm thấy file {input_file}")
        sys.exit(1)
        
    if not input_file.lower().endswith(".imazingapp"):
        print("⚠️ CẢNH BÁO: File không có đuôi .imazingapp, nhưng tool vẫn sẽ thử...")
        
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_Gold{ext}"
    
    try:
        process_imazingapp(input_file, output_file)
        # Giữ màn hình console không bị tắt ngay (nếu chạy bằng double-click)
        input("\nNhấn Enter để thoát...")
    except Exception as e:
        print(f"\n❌ LỖI TRONG QUÁ TRÌNH XỬ LÝ:\n{e}")
        input("\nNhấn Enter để thoát...")
