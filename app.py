Flask
alse, 'error': 'لم يتم اختيار أي ملفات'})
        
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'checklicense', 'hasaccess'
    ]
    
    matched_results = []
    
    try:
        for file in files:
            if file.filename == '':
                continue
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            text_chunks = re.findall(b'[\\x20-\\x7E]{5,}', content)
            for chunk in text_chunks:
                try:
                    s = chunk.decode('utf-8', errors='ignore').strip()
                    lower_s = s.lower()
                    if any(kw in lower_s for kw in unlock_keywords):
                        if len(s) < 100:
                            formatted_res = f"[{file.filename}] {s}"
                            if formatted_res not in matched_results:
                                matched_results.append(formatted_res)
                                if len(matched_results) >= 2000:
                                    break
                except Exception:
                    continue
                    
            if os.path.exists(file_path):
                os.remove(file_path)
                
        return jsonify({'success': True, 'methods': matched_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
s or files[0].filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    # كلمات مفتاحية دقيقة وشاملة لدوال واشتراكات المميزات
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'checklicense', 'hasaccess'
    ]
    
    matched_results = []
    
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            # استخراج الأنماط البرمجية والنصوص المرتبطة بالأسماء والدوال بدقة
            text_chunks = re.findall(b'[\\x20-\\x7E]{5,}', content)
            for chunk in text_chunks:
                try:
                    s = chunk.decode('utf-8', errors='ignore').strip()
                    lower_s = s.lower()
                    
                    # تصفية النصوص لتكون قريبة من شكل الدوال أو الأسماء البرمجية
                    if any(kw in lower_s for kw in unlock_keywords):
                        if len(s) < 100: # استبعاد الجمل الطويلة غير المفيدة
                            formatted_res = f"[{file.filename}] {s}"
                            if formatted_res not in matched_results:
                                matched_results.append(formatted_res)
                                if len(matched_results) >= 2000:
                                    break
                except Exception:
                    continue
                    
            if os.path.exists(file_path):
                os.remove(file_path)
                
        return jsonify({'success': True, 'methods': matched_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
files[0].filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    # الكلمات المفتاحية المركزة لفتح المميزات
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 'isvip', 'ispro'
    ]
    
    matched_results = []
    
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            # استخراج النصوص وأسماء الدوال بدقة متناهية من الملف الثنائي
            text_chunks = re.findall(b'[\x20-\x7E]{4,}', content)
            for chunk in text_chunks:
                try:
                    s = chunk.decode('utf-8', errors='ignore')
                    lower_s = s.lower()
                    if any(kw in lower_s for kw in unlock_keywords):
                        formatted_res = f"[{file.filename}] {s}"
                        if formatted_res not in matched_results:
                            matched_results.append(formatted_res)
                            if len(matched_results) >= 1500:
                                break
                except:
                    continue
                    
            if os.path.exists(file_path):
                os.remove(file_path)
                
        return jsonify({'success': True, 'methods': matched_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
run(host='0.0.0.0', port=port)
