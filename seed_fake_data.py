#!/usr/bin/env python3
"""
اسکریپت ساخت داده‌های فیک برای Freelance Project Manager API
از طریق خود endpoint های HTTP (نه اتصال مستقیم به دیتابیس) تا اعتبارسنجی‌ها
و رابطه‌های بین جدول‌ها رعایت بشن.

نصب پیش‌نیاز:
    pip install requests faker

استفاده:
    python seed_fake_data.py

می‌تونی با متغیر محیطی BASE_URL آدرس API رو عوض کنی:
    BASE_URL=http://localhost:8000 python seed_fake_data.py
"""

import os
import random
import sys
from datetime import date, timedelta

import requests
from faker import Faker

fake = Faker()

BASE_URL = os.environ.get(
    "BASE_URL", "https://freelancetodo.pythonanywhere.com"
).rstrip("/")

# ---- تنظیمات مقدار داده‌ها ----
NUM_CLIENTS = 8
NUM_PROJECTS = 15
NUM_TASKS_PER_PROJECT = (2, 6)      # حداقل و حداکثر تسک به ازای هر پروژه
NUM_PAYMENTS_PER_PROJECT = (1, 4)
NUM_CREDENTIALS_PER_PROJECT = (0, 2)
NUM_NOTES_PER_PROJECT = (0, 3)

PROJECT_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
PRIORITIES = ["low", "medium", "high"]
TASK_STATUSES = ["todo", "in_progress", "done", "cancelled"]
PAYMENT_TYPES = ["income", "expense"]
PAYMENT_STATUSES = ["paid", "unpaid"]


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: str | None = None

    def _headers(self) -> dict:
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    def register_and_login(self) -> None:
        email = fake.unique.email()
        password = "TestPass123!"
        first_name = fake.first_name()
        last_name = fake.last_name()

        register_payload = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/auth/register", json=register_payload
        )
        if resp.status_code not in (200, 201):
            print(f"[!] خطا در ثبت‌نام: {resp.status_code} - {resp.text}")
            sys.exit(1)
        print(f"[+] کاربر ساخته شد: {email}")

        login_payload = {"email": email, "password": password}
        resp = self.session.post(
            f"{self.base_url}/api/v1/auth/login", json=login_payload
        )
        if resp.status_code != 200:
            print(f"[!] خطا در لاگین: {resp.status_code} - {resp.text}")
            sys.exit(1)

        data = resp.json()
        self.access_token = data["access_token"]
        print("[+] لاگین موفق، توکن دریافت شد.")

    def create_client(self) -> dict:
        payload = {
            "name": fake.name(),
            "company": fake.company(),
            "email": fake.company_email(),
            "phone": fake.phone_number()[:20],
            "address": fake.address().replace("\n", ", "),
            "notes": fake.sentence(),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/clients",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_project(self, client_id: str | None) -> dict:
        start = fake.date_between(start_date="-6M", end_date="today")
        deadline = start + timedelta(days=random.randint(10, 120))
        payload = {
            "client_id": client_id,
            "name": fake.catch_phrase(),
            "description": fake.paragraph(nb_sentences=3),
            "status": random.choice(PROJECT_STATUSES),
            "priority": random.choice(PRIORITIES),
            "start_date": start.isoformat(),
            "deadline": deadline.isoformat(),
            "budget": round(random.uniform(300, 15000), 2),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/projects",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_task(self, project_id: str) -> dict:
        due = fake.date_between(start_date="today", end_date="+90d")
        payload = {
            "project_id": project_id,
            "title": fake.sentence(nb_words=5).rstrip("."),
            "description": fake.paragraph(nb_sentences=2),
            "status": random.choice(TASK_STATUSES),
            "priority": random.choice(PRIORITIES),
            "estimated_hours": round(random.uniform(1, 40), 1),
            "actual_hours": round(random.uniform(0, 40), 1),
            "due_date": due.isoformat(),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/tasks",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_payment(self, project_id: str) -> dict:
        pdate = fake.date_between(start_date="-3M", end_date="today")
        payload = {
            "project_id": project_id,
            "amount": round(random.uniform(50, 5000), 2),
            "type": random.choice(PAYMENT_TYPES),
            "status": random.choice(PAYMENT_STATUSES),
            "payment_date": pdate.isoformat(),
            "description": fake.sentence(),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/payments",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_credential(self, project_id: str) -> dict:
        payload = {
            "project_id": project_id,
            "title": f"{fake.word().capitalize()} Access",
            "username": fake.user_name(),
            "password": fake.password(length=14),
            "website": fake.url(),
            "notes": fake.sentence(),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/credentials",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def create_note(self, project_id: str, client_id: str | None) -> dict:
        payload = {
            "project_id": project_id,
            "client_id": client_id,
            "title": fake.sentence(nb_words=4).rstrip("."),
            "content": fake.paragraph(nb_sentences=4),
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/notes",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()


def main() -> None:
    print(f"[i] هدف: {BASE_URL}")
    api = ApiClient(BASE_URL)
    api.register_and_login()

    print(f"[i] ساخت {NUM_CLIENTS} کلاینت ...")
    clients = [api.create_client() for _ in range(NUM_CLIENTS)]
    print(f"[+] {len(clients)} کلاینت ساخته شد.")

    print(f"[i] ساخت {NUM_PROJECTS} پروژه ...")
    projects = []
    for _ in range(NUM_PROJECTS):
        client = random.choice(clients + [None] * 2)  # بعضی پروژه‌ها بدون کلاینت
        client_id = client["id"] if client else None
        projects.append(api.create_project(client_id))
    print(f"[+] {len(projects)} پروژه ساخته شد.")

    total_tasks = total_payments = total_credentials = total_notes = 0

    for project in projects:
        pid = project["id"]
        client_id = project.get("client_id")

        n_tasks = random.randint(*NUM_TASKS_PER_PROJECT)
        for _ in range(n_tasks):
            api.create_task(pid)
        total_tasks += n_tasks

        n_payments = random.randint(*NUM_PAYMENTS_PER_PROJECT)
        for _ in range(n_payments):
            api.create_payment(pid)
        total_payments += n_payments

        n_credentials = random.randint(*NUM_CREDENTIALS_PER_PROJECT)
        for _ in range(n_credentials):
            api.create_credential(pid)
        total_credentials += n_credentials

        n_notes = random.randint(*NUM_NOTES_PER_PROJECT)
        for _ in range(n_notes):
            api.create_note(pid, client_id)
        total_notes += n_notes

    print("\n===== خلاصه =====")
    print(f"کلاینت‌ها:     {len(clients)}")
    print(f"پروژه‌ها:      {len(projects)}")
    print(f"تسک‌ها:        {total_tasks}")
    print(f"پرداخت‌ها:     {total_payments}")
    print(f"کردنشیال‌ها:   {total_credentials}")
    print(f"یادداشت‌ها:    {total_notes}")
    print("==================\n")
    print("داده‌های فیک با موفقیت ساخته شدن.")


if __name__ == "__main__":
    main()
