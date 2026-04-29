content = open('templates/bookings.html', 'rb').read().decode('utf-8', errors='replace')

# Find the screenshot td and replace it
old = content[content.find('<td>\n                    {% if b.payment_screenshot %}'):
              content.find('</td>', content.find('<td>\n                    {% if b.payment_screenshot %}')) + 5]

new = """<td>
                    {% if b.payment_screenshot %}
                    <div style="text-align:center;">
                        <a href="{{ b.payment_screenshot }}" target="_blank">
                            <img src="{{ b.payment_screenshot }}"
                                style="width:55px; height:55px; object-fit:cover; border-radius:8px; border:2px solid #e91e8c; cursor:pointer; display:block; margin:0 auto 4px;"
                                onerror="this.style.display='none'">
                        </a>
                        <span style="padding:2px 8px; border-radius:999px; font-size:10px; font-weight:700;
                            {% if b.payment_status == 'paid' %}background:#d1fae5; color:#065f46;
                            {% elif b.payment_status == 'under_review' %}background:#fef3c7; color:#92400e;
                            {% elif b.payment_status == 'rejected' %}background:#fee2e2; color:#991b1b;
                            {% else %}background:#fee2e2; color:#991b1b;{% endif %}">
                            {{ (b.payment_status or 'unpaid')|upper|replace('_',' ') }}
                        </span>
                        {% if b.payment_status == 'rejected' and b.admin_payment_note %}
                        <br><small style="color:#E74C3C; font-size:10px;">⚠️ {{ b.admin_payment_note }}</small>
                        {% endif %}
                    </div>
                    {% else %}
                    <span style="color:#aaa; font-size:12px;">—</span>
                    {% endif %}
                </td>"""

if old:
    content = content.replace(old, new)
    print("Screenshot column updated")
else:
    print("Pattern not found")

open('templates/bookings.html', 'w', encoding='utf-8').write(content)
print("Done")
