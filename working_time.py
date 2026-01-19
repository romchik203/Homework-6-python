"""Алгоритм расчета рабочего времени по городским графикам."""

from datetime import datetime, time, timedelta
from typing import Iterable, Optional, Tuple


class WorkingTimeCalculator:
    """Калькулятор рабочего времени с учетом графиков работы по городам."""

    # Графики работы по городам
    CITY_SCHEDULES = {
        # ПО УМОЛЧАНИЮ: ПН-ЧТ 9:00-18:00, ПТ 9:00-16:45
        "москва": {
            "weekdays": (time(9, 0), time(18, 0)),
            "friday": (time(9, 0), time(16, 45)),
        },
        "нижний новгород": {
            "weekdays": (time(9, 0), time(18, 0)),
            "friday": (time(9, 0), time(16, 45)),
        },
        "саров": {
            "weekdays": (time(9, 0), time(18, 0)),
            "friday": (time(9, 0), time(16, 45)),
        },
        # НОВОУРАЛЬСК: ПН-ПТ 6:00-15:00
        "новоуральск": {
            "weekdays": (time(6, 0), time(15, 0)),
            "friday": (time(6, 0), time(15, 0)),
        },
        # КРАСНОКАМЕНСК: ПН-ЧТ 3:00-12:00, ПТ 3:00-11:45
        "краснокаменск": {
            "weekdays": (time(3, 0), time(12, 0)),
            "friday": (time(3, 0), time(11, 45)),
        },
    }

    # График по умолчанию для городов, не указанных в CITY_SCHEDULES
    DEFAULT_SCHEDULE = {
        "weekdays": (time(9, 0), time(18, 0)),
        "friday": (time(9, 0), time(16, 45)),
    }

    @classmethod
    def normalize_city_name(cls, city: str) -> str:
        """Нормализует название города для поиска в расписаниях."""
        if not city:
            return ""

        city_lower = city.lower().strip()

        for city_key in cls.CITY_SCHEDULES:
            if city_lower == city_key:
                return city_key

        for city_key in cls.CITY_SCHEDULES:
            if city_key in city_lower or city_lower in city_key:
                return city_key

        return city_lower

    @classmethod
    def is_working_day(cls, dt: datetime) -> bool:
        """Проверяет, является ли день рабочим (пн-пт)."""
        return dt.weekday() < 5

    @classmethod
    def get_working_hours(
        cls, dt: datetime, city: str
    ) -> Optional[Tuple[time, time]]:
        """Возвращает рабочие часы для указанного дня и города."""
        city_normalized = cls.normalize_city_name(city)

        if city_normalized in cls.CITY_SCHEDULES:
            schedule = cls.CITY_SCHEDULES[city_normalized]
        else:
            schedule = cls.DEFAULT_SCHEDULE

        if dt.weekday() == 4:  # Пятница
            return schedule["friday"]

        return schedule["weekdays"]

    @classmethod
    def calculate_working_time(
        cls, start_dt: datetime, end_dt: datetime, city: str
    ) -> float:
        """
        Рассчитывает рабочее время между двумя датами с учетом графиков работы по городам.

        Возвращает время в часах (float), учитывая только рабочие часы.
        """
        if start_dt >= end_dt:
            return 0.0

        total_hours = 0.0
        current_dt = start_dt

        while current_dt < end_dt:
            current_date = current_dt.date()

            if not cls.is_working_day(current_dt):
                if current_dt.weekday() == 5:  # Суббота
                    current_dt = datetime.combine(
                        current_date + timedelta(days=2), time(0, 0)
                    )
                elif current_dt.weekday() == 6:  # Воскресенье
                    current_dt = datetime.combine(
                        current_date + timedelta(days=1), time(0, 0)
                    )
                else:
                    current_dt += timedelta(days=1)
                continue

            work_hours = cls.get_working_hours(current_dt, city)
            if not work_hours:
                current_dt = datetime.combine(
                    current_date + timedelta(days=1), time(0, 0)
                )
                continue

            work_start, work_end = work_hours

            if current_date == start_dt.date():
                day_start = max(current_dt, datetime.combine(current_date, work_start))
            else:
                day_start = datetime.combine(current_date, work_start)

            if current_date == end_dt.date():
                day_end = min(end_dt, datetime.combine(current_date, work_end))
            else:
                day_end = datetime.combine(current_date, work_end)

            if day_start < day_end:
                day_hours = (day_end - day_start).total_seconds() / 3600.0
                total_hours += max(0.0, day_hours)

            current_dt = datetime.combine(
                current_date + timedelta(days=1), time(0, 0)
            )

        return total_hours

    @classmethod
    def calculate_reaction_time(
        cls, assigned_dt: datetime, start_dt: datetime, city: str
    ) -> Optional[float]:
        """Рассчитывает время реакции в рабочих часах."""
        if not assigned_dt or not start_dt:
            return None

        if start_dt <= assigned_dt:
            return 0.0

        return cls.calculate_working_time(assigned_dt, start_dt, city)

    @classmethod
    def calculate_resolution_time(
        cls, start_dt: datetime, end_dt: datetime, city: str
    ) -> Optional[float]:
        """Рассчитывает время решения в рабочих часах."""
        if not start_dt or not end_dt:
            return None

        if end_dt <= start_dt:
            return 0.0

        return cls.calculate_working_time(start_dt, end_dt, city)

    @classmethod
    def calculate_total_time(
        cls, assigned_dt: datetime, end_dt: datetime, city: str
    ) -> Optional[float]:
        """Рассчитывает общее время от направления до закрытия в рабочих часах."""
        if not assigned_dt or not end_dt:
            return None

        if end_dt <= assigned_dt:
            return 0.0

        return cls.calculate_working_time(assigned_dt, end_dt, city)


def _parse_datetime(value: str, formats: Iterable[str]) -> datetime:
    """Парсит дату/время из строки, пробуя несколько форматов."""
    last_error: Optional[ValueError] = None
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise ValueError("Не удалось распознать дату/время.")


def _read_datetime(prompt: str) -> datetime:
    """Читает дату/время из ввода пользователя в удобных форматах."""
    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    )

    while True:
        raw = input(prompt).strip()
        if not raw:
            print("Пустое значение. Пример: 2026-01-19 10:30")
            continue
        try:
            return _parse_datetime(raw, formats)
        except ValueError:
            print(
                "Не удалось распознать дату/время. "
                "Примеры: 2026-01-19 10:30, 19.01.2026 10:30"
            )


def _read_city(prompt: str) -> str:
    """Читает название города; пустое значение означает график по умолчанию."""
    while True:
        raw = input(prompt).strip()
        if raw:
            return raw
        print("Пустой город. Будет использован график по умолчанию.")
        return "по умолчанию"


def _format_hours(value: Optional[float]) -> str:
    if value is None:
        return "нет данных"
    return f"{value:.2f} ч"


def main() -> None:
    print("==============================================")
    print("Калькулятор рабочего времени по городским графикам")
    print("==============================================")
    print("Форматы дат: 2026-01-19 10:30 | 19.01.2026 10:30")
    print(
        "Города: "
        + ", ".join(sorted(WorkingTimeCalculator.CITY_SCHEDULES.keys()))
        + " (или оставьте пустым для графика по умолчанию)"
    )
    print()
    city = _read_city("Город: ")

    assigned_dt = _read_datetime("Дата направления: ")
    start_dt = _read_datetime("Дата начала работ: ")
    end_dt = _read_datetime("Дата завершения работ: ")

    reaction_time = WorkingTimeCalculator.calculate_reaction_time(
        assigned_dt, start_dt, city
    )
    resolution_time = WorkingTimeCalculator.calculate_resolution_time(
        start_dt, end_dt, city
    )
    total_time = WorkingTimeCalculator.calculate_total_time(
        assigned_dt, end_dt, city
    )

    print()
    print("--------------- Результаты -------------------")
    print(f"Город:           {city}")
    print(f"Направление:     {assigned_dt:%Y-%m-%d %H:%M}")
    print(f"Начало работ:    {start_dt:%Y-%m-%d %H:%M}")
    print(f"Завершение:      {end_dt:%Y-%m-%d %H:%M}")
    print("----------------------------------------------")
    print(f"Время реакции:   {_format_hours(reaction_time)}")
    print(f"Время решения:   {_format_hours(resolution_time)}")
    print(f"Общее время:     {_format_hours(total_time)}")
    print("----------------------------------------------")


if __name__ == "__main__":
    main()
