from flask import Flask, request, render_template_string, redirect, url_for, get_flashed_messages
from collections import deque
from datetime import datetime, time

app = Flask(__name__)
app.secret_key = 'change_this_to_a_secure_random_key'

# ——— Xodim va navbat klasslari ———
class Employee:
    def __init__(self, name, rus_level, work_start, work_end):
        self.name = name
        self.rus_level = rus_level  # 'biladi', 'ozgina', 'bilmaydi'
        h, m = map(int, work_start.split(':'))
        self.start = time(h, m)
        h, m = map(int, work_end.split(':'))
        self.end = time(h, m)

    def is_available(self, client_lang, now_time):
        if not (self.start <= now_time <= self.end):
            return False
        if client_lang == 'rus':
            return self.rus_level in ('biladi', 'ozgina')
        return True

class DynamicQueue:
    def __init__(self):
        self.queue = deque()
        self.customer_count = 0

    def add_employee(self, emp: Employee):
        self.queue.append(emp)

    def assign_customer(self, client_lang: str, now_time: time):
        if client_lang == 'rus':
            for idx, emp in enumerate(self.queue):
                if emp.is_available('rus', now_time):
                    # Rus xodimni navbatdan chiqarib, oxiriga qo'shish
                    self.queue.rotate(-idx)
                    assigned = self.queue.popleft()
                    self.queue.rotate(idx)
                    self.queue.append(assigned)
                    return assigned
            return None

        # Non-rus mijoz uchun oddiy circular queue
        n = len(self.queue)
        for _ in range(n):
            emp = self.queue.popleft()
            if emp.is_available('non-rus', now_time):
                self.queue.append(emp)
                return emp
            self.queue.append(emp)
        return None

    def handle_arrival(self, client_lang: str, now_time: time = None):
        if now_time is None:
            now_time = datetime.now().time()
        self.customer_count += 1
        label = f"mijoz{self.customer_count}"
        emp = self.assign_customer(client_lang, now_time)
        return label, emp.name if emp else "Xodim topilmadi"

# ——— Initial staff data and queue initialization ———
staff_data = [
    ("Ali Kantibekov",      "bilmaydi",    "09:00", "22:00"),
    ("Asilbek To'ychiyev",  "bilmaydi",    "09:00", "22:00"),
    ("Asilbek Usmonov",     "bilmaydi",    "09:00", "22:00"),
    ("Begzod Hakimov",      "biladi",      "09:00", "22:00"),
    ("Lobar Mamataliyeva",  "bilmaydi",    "09:00", "17:00"),
    ("Marjona",             "bilmaydi",    "09:00", "18:00"),
    ("Samira Xalmirzayeva", "biladi",      "10:00", "22:00"),
    ("Sardor Boyto'rayev",  "bilmaydi",    "09:00", "22:00"),
    ("Zaringis",            "ozgina",      "10:00", "22:00"),
    ("Олеся Шмелева",       "biladi",      "10:00", "22:00"),
]


dq = DynamicQueue()
assignments_history = []  # Kelgan mijoz-xodim juftliklari saqlanadi

# Dastlabki navbatni to‘ldirish
for name, lvl, start, end in staff_data:
    dq.add_employee(Employee(name, lvl, start, end))

# ——— HTML shablon ———
HTML = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Navbat Tizimi</title>
    <style>
      table { border-collapse: collapse; width: 60%; margin-bottom: 20px; }
      th, td { border: 1px solid #888; padding: 8px; text-align: left; }
      th { background: #f0f0f0; }
      .btn { margin-top: 10px; }
    </style>
  </head>
  <body>
    <h2>Xodimlar joriy navbati</h2>
    <table>
      <tr>
        <th>№</th><th>Xodim</th><th>Rus tilini bilishi</th><th>Ish vaqti</th>
      </tr>
      {% for emp in queue %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ emp.name }}</td>
        <td>{{ emp.rus_level }}</td>
        <td>{{ emp.start.strftime('%H:%M') }}–{{ emp.end.strftime('%H:%M') }}</td>
      </tr>
      {% endfor %}
    </table>

    <h2>Yangi mijoz kelishi</h2>
    <form method="POST" action="/assign">
      <label><input type="checkbox" name="is_russian"> Rus mijoz</label>
      <button type="submit" class="btn">Navbat berish</button>
    </form>

    {% if result %}
      <h3 style="margin-top:20px;">{{ result[0] }} → {{ result[1] }}</h3>
    {% endif %}

    {% if history %}
      <h2>Bajarilgan navbatlar</h2>
      <table>
        <tr><th>Mijoz</th><th>Xodim</th></tr>
        {% for m, e in history %}
        <tr>
          <td>{{ m }}</td>
          <td>{{ e }}</td>
        </tr>
        {% endfor %}
      </table>
      <form method="POST" action="/reset">
        <button type="submit" class="btn">Tozalash</button>
      </form>
    {% endif %}
  </body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    messages = get_flashed_messages()
    result = messages[0] if messages else None
    return render_template_string(
        HTML,
        queue=list(dq.queue),
        result=result,
        history=assignments_history
    )

@app.route('/assign', methods=['POST'])
def assign():
    is_rus = 'is_russian' in request.form
    lang = 'rus' if is_rus else 'non-rus'
    mijoz, xodim = dq.handle_arrival(lang, datetime.now().time())
    assignments_history.insert(0, (mijoz, xodim))
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    # Navbat va tarixni reset qilish
    dq.queue.clear()
    dq.customer_count = 0
    assignments_history.clear()
    # Dastlabki xodimlarni qayta qo'shish
    for name, lvl, start, end in staff_data:
        dq.add_employee(Employee(name, lvl, start, end))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
