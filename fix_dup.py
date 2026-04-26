content = open('app.py', 'rb').read().decode('utf-8', errors='replace')

# Find and remove the duplicate block between the two routes
dup_start = '\r\n\r\n            db = get_supabase()\r\n            result = db.table(\'bookings\').insert({\r\n                \'username\': user,\r\n                \'booked_by\': user,\r\n                \'service_name\': service,\r\n                \'appointment_date\': date,\r\n                \'appointment_time\': time,\r\n                \'stylist\': stylist,\r\n                \'notes\': notes,\r\n                \'payment_method\': payment_method,\r\n                \'service_type\': service_type,\r\n                \'address\': address,\r\n                \'status\': \'pending\',\r\n                \'created_at\': datetime.utcnow().isoformat()\r\n            }).execute()\r\n\r\n            print(f"=== BOOKING SAVED: {result.data} ===")\r\n            if request.is_json:\r\n                return jsonify({\'success\': True, \'message\': \'Booking confirmed!\'})\r\n            flash(\'Booking submitted successfully! \\u2705\', \'success\')\r\n            return redirect(url_for(\'bookings_page\'))\r\n        except Exception as e:\r\n            print(f"=== BOOKING ERROR: {str(e)} ===")\r\n            if request.is_json:\r\n                return jsonify({\'success\': False, \'message\': str(e)}), 500\r\n            flash(f\'Booking failed: {str(e)}\', \'error\')\r\n            return redirect(url_for(\'index\'))\r\n    return redirect(url_for(\'index\'))\r\n\r\n@app.route(\'/bookings\')'

dup_end = '\r\n@app.route(\'/bookings\')'

if dup_start in content:
    content = content.replace(dup_start, dup_end)
    print("Duplicate removed")
else:
    # Try to find it differently
    idx = content.find("    return redirect(url_for('index'))\r\n\r\n\r\n            db = get_supabase()")
    if idx != -1:
        # Find end of duplicate block
        end_marker = "\r\n@app.route('/bookings')"
        end_idx = content.find(end_marker, idx)
        if end_idx != -1:
            content = content[:idx + len("    return redirect(url_for('index'))\r\n")] + end_marker + content[end_idx + len(end_marker):]
            print("Duplicate removed (method 2)")
        else:
            print("End marker not found")
    else:
        print("Duplicate not found - checking...")
        idx2 = content.find("return redirect(url_for('index'))\r\n\r\n\r\n")
        print("Found at:", idx2)
        print(repr(content[idx2:idx2+100]))

open('app.py', 'w', encoding='utf-8').write(content)

# Verify syntax
import ast
try:
    ast.parse(content)
    print("Syntax OK")
except SyntaxError as e:
    print("Syntax Error:", e)
