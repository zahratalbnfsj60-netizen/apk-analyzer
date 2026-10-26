import os
import sys
import re
from concurrent.futures import ThreadPoolExecutor, asChildThread if hasattr(sys, 'settrace') else ThreadPoolExecutor
import threading

# إعداد الألوان لعرض النتائج بشكل احترافي
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# الكلمات المفتاحية المستهدفة حصرياً (الاشتراكات، البرو، الـ VIP، التراخيص)
TARGET_KEYWORDS = [
    "premium", "subscription", "vip", "pro", "purchase", 
    "billing", "license", "unlock", "is_premium", "has_premium", 
    "sub_status", "is_pro", "is_vip", "purchased", "not_set"
]

# الكلمات المستبعدة تماماً (لتجاهل إعلانات Unity, AppLovin, Firebase, وغيرها)
EXCLUDE_KEYWORDS = [
    "unity3d", "applovin", "firebase", "ads", "analytics", 
    "protobuf", "facebook", "adjust", "google/android/gms/ads",
    "androidx/", "kotlin/", "java/"
]

print_lock = threading.Lock()

def analyze_smali_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # التحقق مما إذا كان الملف يتبع حزمة SDK مستبعدة لتوفير الوقت
        lower_path = file_path.replace('\\', '/').lower()
        if any(ex in lower_path for ex in EXCLUDE_KEYWORDS):
            return

        # البحث عن الدوال (.method) داخل الملف
        methods = re.findall(r'(\.method.*?\.end method)', content, re.DOTALL)
        
        for method in methods:
            method_lower = method.lower()
            
            # التأكد من أن الدالة تحتوي على الأقل على إحدى الكلمات المستهدفة للاشتراكات
            matched_keywords = [kw for kw in TARGET_KEYWORDS if kw in method_lower]
            
            if matched_keywords:
                # استخراج اسم الدالة للتمييز
                method_name_match = re.search(r'\.method.*? ([a-zA-Z0-9_<init>]+)\(', method)
                method_name = method_name_match.group(1) if method_name_match else "unknown_method"
                
                with print_lock:
                    print(f"\n{Colors.GREEN}[+] وجد هدف محتمل في الملف:{Colors.RESET} {file_path}")
                    print(f"{Colors.YELLOW}    [الدالة]: {Colors.BOLD}{method_name}{Colors.RESET}")
                    print(f"{Colors.CYAN    [الكلمات المطابقة]: {', '.join(matched_keywords)}{Colors.RESET}")
                    print(f"{Colors.HEADER}--------------------------------------------------{Colors.RESET}")
                    # طباعة أسطر الدالة بشكل مختصر وواضح
                    lines = method.strip().split('\n')
                    for line in lines[:15]: # عرض أول 15 سطراً فقط للاختصار
                        print(f"    {Colors.BLUE}{line}{Colors.RESET}")
                    if len(lines) > 15:
                        print(f"    {Colors.RED}... [تم اختصار باقي الأسطر] ...{Colors.RESET}")
                        
    except Exception as e:
        pass

def scan_directory(root_dir):
    smali_files = []
    print(f"{Colors.YELLOW}[*] جاري جمع ملفات Smali للبحث السريع...{Colors.RESET}")
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.smali'):
                smali_files.append(os.path.join(root, file))
                
    print(f"{Colors.GREEN}[+] تم العثور على {len(smali_files)} ملف. بدء عملية الفحص الذكي...{Colors.RESET}\n")
    
    # استخدام ThreadPoolExecutor للبحث الفائق السرعة عبر خيوط متعددة
    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        executor.map(analyze_smali_file, smali_files)
        
    print(f"\n{Colors.GREEN}[✔] انتهى الفحص بنجاح!{Colors.RESET}")

if __name__ == "__main__":
    # ضع مسار مجلد فك الضغط (مثل مجلد smali الرئيسي للتطبيق المستخرج)
    target_directory = input(f"{Colors.CYAN}أدخل مسار مجلد الـ smali للبدء: {Colors.RESET}").strip()
    if os.path.exists(target_directory):
        scan_directory(target_directory)
    else:
        print(f"{Colors.RED}[!] المسار غير موجود، تأكد من صحته وحاول مجدداً.{Colors.RESET}")
