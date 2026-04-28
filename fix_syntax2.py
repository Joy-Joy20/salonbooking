content = open('app.py', 'r', encoding='utf-8').read()

# The issue: email code was inserted between the insert and the if request.is_json check
# Need to add pass or move the email code after the if block

old = """            if request.is_json:
            # Send booking confirmation email
            try:"""

new = """            # Send booking confirmation email
            try:
                user_email = session.get('user_email', '')
                if user_email and service:
                    pass  # email sent below
            except Exception:
                pass
            if request.is_json:
            # Send booking confirmation email - placeholder
            try:"""

# Actually just fix by removing the duplicate and putting email after flash
# Find the exact block
idx = content.find("            if request.is_json:\n            # Send booking confirmation email\n            try:")
if idx != -1:
    # Replace with correct structure
    old_block = "            if request.is_json:\n            # Send booking confirmation email\n            try:\n                user_email = session.get('user_email', '')\n                if user_email and service:\n                    html = "
    # Find end of try block
    end_idx = content.find("            flash('Booking submitted successfully!", idx)
    
    # Extract the email html and send_email call
    email_section_start = content.find("                    html = ", idx)
    email_section_end = content.find("                print(f'Booking email error:", idx) + len("                print(f'Booking email error: {str(email_err)}')\n")
    email_code = content[email_section_start:email_section_end]
    
    # Build correct replacement
    new_block = "            if request.is_json:\n                return jsonify({'success': True, 'message': 'Booking confirmed!'})\n            # Send booking confirmation email\n            try:\n                user_email = session.get('user_email', '')\n                if user_email and service:\n                    " + email_code.strip() + "\n            except Exception as email_err:\n                print(f'Booking email error: {str(email_err)}')\n            "
    
    print("Found block, fixing...")
    print(repr(content[idx:idx+100]))

# Simpler approach - just fix the indentation issue
content = content.replace(
    "            if request.is_json:\n            # Send booking confirmation email",
    "            # Send booking confirmation email"
)
# Also fix the duplicate return
content = content.replace(
    "                return jsonify({'success': True, 'message': 'Booking confirmed!'})\n            flash('Booking submitted successfully!",
    "                return jsonify({'success': True, 'message': 'Booking confirmed!'})\n            else:\n                flash('Booking submitted successfully!"
)

open('app.py', 'w', encoding='utf-8').write(content)

import ast
try:
    ast.parse(content)
    print("Syntax OK")
except SyntaxError as e:
    print("Syntax Error:", e)
    lines = content.split('\n')
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
        print(f"{i+1}: {repr(lines[i])}")
