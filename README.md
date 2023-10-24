# foosball-tournament-backend

## Технологии
- Python
- FastAPI
- PostgreSQL

[Репозиторий с фронтендом](https://github.com/alexander1934/foosball-tournament-frontend)

## Описание
Веб-приложение Foosball Tournament позволяет проводить и управлять турнирами по настольному футболу.

### Регистрация и авторизация 
Прежде чем создавать турнир или принимать участие в одном из имеющихся, пользователю необходимо пройти авторизацию. Неавторизованный пользователь может только просматривать список турниров, детальную информацию о них, просматривать профили пользователей и их команд.

После авторизации пользователю открывается доступ к созданию команд, созданию турниров и участию в них. При регистрации пользователь указывает логин, пароль и свой никнейм в рамках площадки.

### Турниры
Авторизированный пользователь может создавать турниры. 
При создании указывается:
- Название турнира
- Описание
- Дата начала
- Дата конца
- Система, по которой будут распределяться команды-участники (реализована только Олимпийская система)

## Формирование сетки
Турнирная сетка строится по олимпийской системе (Single Elimination, Плей-офф), при которой участник выбывает из турнира после первого проигрыша. Такой подход обеспечивает выявление победителей за минимальное число туров.

Учитывается количество команд, которые будут участвовать в турнире. Есть 2 сценария того, как строится турнирная сетка в зависимости от количества команд:

- Количество команд равно степени двойки. Это самый просто и логичный вариант
- Количество команд НЕ равно степени двойки. В таком случае турнирная сетка формируется так, чтобы ко второму туру осталось количество команд равное степени двойки. Таким образом, часть команд приступит к игре только во втором туре (раунде).



## Инструкция по установке
Для проекта потребуется установить [Poetry](https://python-poetry.org/docs/) и 
[docker](https://docs.docker.com/engine/install/) + [docker-compose](https://docs.docker.com/compose/install/linux/)

### Подготовка к запуску

#### Инициализация базы данных для локальной разработки
```bash
docker compose up postgres -d
# wait for a bit
docker ps --format "{{.ID}}: {{.Names}}" | grep "foosball-tournament-backend-postgres" | cut -d: -f 1 | xargs -I {} docker exec {} bash -c "su - postgres -c \"createdb foosball\"" && echo database created
```

#### Запуск установка зависимостей через Poetry. (Если есть проблемы, отредактируйте poetry.lock)
```bash
poetry install
```


### Запуск проекта.
#### В докере 
Обязательно нужно заполнить поле `authjwt_secret_key`. Сделать это можно двумя способами: напрямую в 
docker-compose.yml указать переменную
```yaml
<...>
environment:
  - DEBUG=True
  - PYTHONPATH=/app
  - POSTGRES_DSN=postgres://postgres:postgres@postgres/postgres
  - authjwt_secret_key=myveryimportantsecret
ports:
  - "8000:8000"
```

Либо прописав такую команду: `export authjwt_secret_key=mysecretinanotherway`
и запустив docker-compose.

#### Локально
```bash
export DEBUG=True
export authjwt_secret_key=myveryimportantsecret
export POSTGRES_DSN=postgres://postgres:postgres@localhost:5433/foosball

docker compose up -d postgres

python src/main.py
```

## Требования для бэкенда
### Обязательные
| Требования                                                                                             | Выполнено или нет | 
|--------------------------------------------------------------------------------------------------------|:-----------------:|
| 1. Использование база данных (любой), необходимо предоставить доступ, для оценки структуры базы данных |         ✅         |
| 2. Корректная обработка ошибок и возврат соответствующих HTTP статусов и сообщений                     |         ✅         |
| 3. Swagger документация API                                                                            |         ✅         |
| 4. Сервис должен работать стабильно, без неожиданных падений                                           |         ✅         |

### Дополнительные (необязательные)
| Требования                                                               | Выполнено или нет | 
|--------------------------------------------------------------------------|:-----------------:|
| 1. Высокая производительность                                            |         ✅         |
| 2. Разработка по чистой архитектуре                                      |         ❌         |
| 3. README с описанием проблем приложения и путей по решению этих проблем |         ✅         |


## Требования к продукту
### Функциональные требования к продукту (обязательные)
| Требования                                                                                                                                                   | Выполнено или нет | 
|--------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------:|
| 1. Создание команды путем указания имени <br/>(или ID, если реализована авторизация)                                                                         |         ✅         |
| 2. Возможность ввода счета сыгранного матча в турнирной сетке                                                                                                |         ❌         |
| 3. Турнирная сетка должна генерироваться и корректно обрабатывать четное <br/>и нечетное количество команд (логика генерации на ваше усмотрение, без ошибок) |         ✅         |
| 4. В одной команде может находиться 2 человека                                                                                                               |         ✅         |
| 5. Возможность завершить турнир                                                                                                                              |         ❌         |
| 6. Хранение истории сыгранных турниров                                                                                                                       |         ✅         |
| 7. Возможность просмотра статусов всех турниров                                                                                                              |         ✅         |
| 8. Возможность обновить данные турнирной сетки (на крайний случай обновление <br/>страницы должно обновить турнирную таблицу)                                |         ✅         |
| 9. Хранение данных пользователей и матчей в БД                                                                                                               |         ✅         |
| 10. Сущности БД должны содержать более одного атрибута (сущности и связи на усмотрение разработчика)                                                         |         ✅         |

### Нефункциональные требования к продукту (дополнительные)
| Требования                                                                                          | Выполнено или нет | 
|-----------------------------------------------------------------------------------------------------|:-----------------:|
| 1. Возможность регистрации, авторизации для доступа к турнирам                                      |         ✅         |
| 2. Разграничение прав доступа: турнир может начать только создатель турнира                         |         ✅         |
| 3. Данные турнирной сетки должны обновлять автоматически                                            |         ✅         |
| 4. Турнир завершается автоматически, если все матчи сыграны, и победитель выявлен                   |         ❌         |
| 5. Возможность просмотра статистики других пользователей (история участия в турнирах, побед и т.д.) |         ✅         |
