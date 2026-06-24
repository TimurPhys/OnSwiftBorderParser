# from parser import get_monthly_data
from parser import session_parser


def job():
    print("Запуск парсинга...")
    # get_monthly_data()
    session_parser()


if __name__ == "__main__":
    job()
    # while True:
    #     try:
    #         job()
    #     except Exception as e:
    #         print(f"Ошибка в работе: {e}")

    #     time.sleep(10)
